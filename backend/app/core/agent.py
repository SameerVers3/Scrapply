import json
import re
import time
import datetime
import os
from typing import Dict, Any, Optional, List, Tuple
import aiohttp
import asyncio
from bs4 import BeautifulSoup
from bs4.element import Tag
from openai import OpenAI, AsyncOpenAI
import logging
from config.settings import settings
from .dynamic_scraper import DynamicScraperEngine
from .strategy_selector import ScrapingStrategySelector

logger = logging.getLogger(__name__)


class UniversalHtmlAnalyzer:
    """Analyze a static HTML document to identify repeating-content containers,
    hypothesize selectors, and produce representative samples.

    This is a deterministic, content-agnostic analyzer that uses structural
    signals (repetition, class similarity, tag similarity, and semantic list
    tags) rather than domain-specific heuristics.
    """

    def __init__(self, html_content: str):
        """Initialize with raw HTML content and prepare a BeautifulSoup instance.

        This initializer stores the raw HTML and constructs a soup object used by
        the analyzer methods. Call `analyze()` to find the most likely repeating
        container and a confidence score.
        """
        self.html_content = html_content or ""
        # Build a soup for internal analysis
        try:
            self.soup = BeautifulSoup(self.html_content, 'html.parser')
        except Exception:
            # Fallback to empty soup
            self.soup = BeautifulSoup('', 'html.parser')

    def analyze(self) -> Tuple[Optional[Tag], float]:
        """Find the most likely repeating-item container and return (tag, score).

        The scoring is based on direct child count, tag similarity, class
        similarity, semantic list bonuses, and simple density penalties. This
        method is intentionally conservative and fast so it can be used to
        extract a small focused snippet to send to an LLM.
        """
        from collections import Counter

        candidates: List[Tuple[Tag, float]] = []

        # Consider a focused set of container tags
        for tag in self.soup.find_all(['div', 'section', 'main', 'article', 'ul', 'ol', 'table']):
            children = [c for c in tag.find_all(recursive=False) if isinstance(c, Tag)]
            child_count = len(children)
            if child_count < 2:
                continue

            # Base score: more direct children implies potential repeating structure
            score = float(child_count)

            # Tag similarity among children (many <li> inside a <ul> for example)
            tag_names = [c.name for c in children]
            if tag_names:
                tag_count = Counter(tag_names)
                most_common_count = tag_count.most_common(1)[0][1]
                tag_similarity = most_common_count / child_count
                score += tag_similarity * 1.0  # weight 1.0

            # Class similarity is a very strong signal (component classes)
            class_keys = [tuple(c.get('class') or []) for c in children]
            if class_keys:
                cls_count = Counter(class_keys)
                most_common_cls_freq = cls_count.most_common(1)[0][1]
                class_similarity = most_common_cls_freq / child_count
                score += class_similarity * 1.5  # higher weight

            # Semantic list tags get a boost
            if tag.name in ('ul', 'ol', 'table'):
                score += 1.2

            # Penalize overly-generic containers
            if tag.name in ('body', 'html') or (tag.get('id') in ('root', 'app') if tag.get('id') else False):
                score *= 0.2

            # Penalize when there's a lot of nested tags but very little text
            text_len = len(''.join(tag.stripped_strings))
            descendant_tag_count = len(tag.find_all())
            if descendant_tag_count > 0:
                text_density = text_len / descendant_tag_count
                if text_density < 2:
                    score *= 0.7

            candidates.append((tag, score))

        if not candidates:
            return None, 0.0

        best = max(candidates, key=lambda t: t[1])
        return best[0], float(best[1])

    def _analyze_container_semantics(self, container: Tag) -> Dict[str, Any]:
        """Hypothesize item selector and potential fields from a container.

        Returns a dictionary with 'item_container_selector' and 'potential_fields'.
        """
        from collections import Counter

        children = [c for c in container.find_all(recursive=False) if isinstance(c, Tag)]
        if not children:
            return {"item_container_selector": "", "potential_fields": {}}

        tag_names = [c.name for c in children]
        tag_count = Counter(tag_names)
        most_common_tag, _ = tag_count.most_common(1)[0]

        class_keys = [tuple(c.get('class') or []) for c in children]
        cls_count = Counter(class_keys)
        most_common_cls, freq = cls_count.most_common(1)[0]

        if most_common_cls:
            first_class = most_common_cls[0] if len(most_common_cls) > 0 else ''
            item_selector = f"{most_common_tag}.{first_class}" if first_class else most_common_tag
        else:
            item_selector = most_common_tag

        # Field detectors
        def detect_title(item: Tag) -> Optional[str]:
            for h in item.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                cls = h.get('class') or []
                return f"{h.name}{'.' + '.'.join(cls) if cls else ''}"
            el = item.find(True, class_=re.compile(r'title|name|heading', re.I))
            if el:
                cls = el.get('class') or []
                return f"{el.name}{'.' + '.'.join(cls) if cls else ''}"
            return None

        def detect_price(item: Tag) -> Optional[str]:
            el = item.find(True, class_=re.compile(r'price|cost|amount', re.I))
            if el:
                cls = el.get('class') or []
                return f"{el.name}{'.' + '.'.join(cls) if cls else ''}"
            for t in item.find_all(text=True):
                if re.search(r'[\$€£¥]', t):
                    parent = t.parent
                    cls = parent.get('class') or []
                    return f"{parent.name}{'.' + '.'.join(cls) if cls else ''}"
            return None

        def detect_image(item: Tag) -> Optional[str]:
            img = item.find('img')
            if img and img.get('src'):
                cls = img.get('class') or []
                return f"img{'.' + '.'.join(cls) if cls else ''}[src]"
            return None

        def detect_link(item: Tag) -> Optional[str]:
            a = item.find('a', href=True)
            if a:
                cls = a.get('class') or []
                return f"a{'.' + '.'.join(cls) if cls else ''}[href]"
            return None

        samples = container.select(item_selector)[:5] if item_selector else children[:5]

        titles, prices, images, links = [], [], [], []
        for it in samples:
            t = detect_title(it)
            if t:
                titles.append(t)
            p = detect_price(it)
            if p:
                prices.append(p)
            im = detect_image(it)
            if im:
                images.append(im)
            ln = detect_link(it)
            if ln:
                links.append(ln)

        def most_common_or_empty(lst: List[str]) -> str:
            return Counter(lst).most_common(1)[0][0] if lst else ''

        potential_fields = {
            'title': most_common_or_empty(titles),
            'price': most_common_or_empty(prices),
            'image': most_common_or_empty(images),
            'link': most_common_or_empty(links)
        }

        return {"item_container_selector": item_selector, "potential_fields": potential_fields}

    def _extract_intelligent_samples(self, container: Tag, item_selector: str) -> List[Dict[str, str]]:
        samples: List[Dict[str, str]] = []
        try:
            items = container.select(item_selector)[:3] if item_selector else [c for c in container.find_all(recursive=False) if isinstance(c, Tag)][:3]
        except Exception:
            items = []

        for it in items:
            try:
                html = it.prettify()
            except Exception:
                html = str(it)
            samples.append({"sample_html": html})

        return samples


class UnifiedAgent:
    """
    Unified AI agent that handles website analysis, scraper generation, and refinement
    """

    def __init__(self, api_key: str, model: str = "gpt-4o", base_url: Optional[str] = None):
        # Store API key and base URL for direct requests approach
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.session = None
        
        # Configure client with custom base URL if provided
        client_kwargs = {"api_key": api_key}
        if base_url:
            client_kwargs["base_url"] = base_url
            
        # Use direct requests for AIMLAPI compatibility, async client for standard OpenAI
        if base_url and "aimlapi.com" in base_url:
            self.client = None  # We'll use requests directly
            self.is_sync_client = True
            logger.debug(f"UnifiedAgent initialized for AIMLAPI direct requests, model={model}, base_url={base_url}")
        else:
            self.client = AsyncOpenAI(**client_kwargs)
            self.is_sync_client = False
            logger.debug(f"UnifiedAgent initialized with async client, model={model}, base_url={base_url}")

    async def __aenter__(self):
        logger.debug("Creating aiohttp session")
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=settings.REQUEST_TIMEOUT),
            headers={'User-Agent': settings.USER_AGENT}
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        logger.debug("Closing aiohttp session")
        if self.session:
            await self.session.close()

    async def _make_ai_request(self, messages: List[Dict[str, str]], temperature: float = 0.1):
        """Helper method to handle both sync and async API calls"""
        if self.is_sync_client and hasattr(self, 'api_key') and hasattr(self, 'base_url'):
            # Use requests for AIMLAPI to ensure proper header format
            import requests
            import asyncio
            
            def make_request():
                response = requests.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.api_key}"
                    },
                    json={
                        "model": self.model,
                        "messages": messages,
                        "temperature": temperature
                    },
                    timeout=60  # 60 second timeout for AIMLAPI
                )
                response.raise_for_status()
                return response.json()
            
            loop = asyncio.get_event_loop()
            response_data = await loop.run_in_executor(None, make_request)
            
            # Convert to OpenAI-like response format
            class MockResponse:
                def __init__(self, data):
                    self.choices = [MockChoice(data['choices'][0])]
            
            class MockChoice:
                def __init__(self, choice_data):
                    self.message = MockMessage(choice_data['message'])
            
            class MockMessage:
                def __init__(self, message_data):
                    self.content = message_data['content']
            
            return MockResponse(response_data)
        else:
            # Use async client for standard OpenAI
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature
            )
            return response

    async def analyze_website(self, url: str, description: str) -> Dict[str, Any]:
        """Analyze website structure and plan extraction strategy"""
        await self._log_io('analyze_website', 'input', {'url': url, 'description': description})
        logger.info(f"Starting website analysis for {url} with description='{description}'")
        start_time = time.time()

        try:
            html_content = await self._fetch_website_content(url)
            if not html_content:
                raise Exception("Failed to fetch website content")
            logger.debug(f"Fetched {len(html_content)} characters of HTML from {url}")

            soup = BeautifulSoup(html_content, 'html.parser')
            logger.debug("Parsed HTML with BeautifulSoup")

            # Remove script/style
            removed = 0
            for script in soup(["script", "style"]):
                script.decompose()
                removed += 1
            logger.debug(f"Removed {removed} script/style tags")

            html_sample = str(soup)[:2000]
            text_sample = soup.get_text()[:1000]

            logger.info(f"HTML sample length={len(html_sample)}, Text sample length={len(text_sample)}")
            logger.debug(f"HTML sample (truncated): {html_sample}")

            # Use the UniversalHtmlAnalyzer to extract the most likely repeating
            # container and a few representative samples to reduce tokens sent to
            # the LLM. This avoids including the full page HTML in the prompt.
            analyzer = UniversalHtmlAnalyzer(html_content=str(soup))
            try:
                best_container, best_score = analyzer.analyze()
            except Exception as e:
                logger.exception(f"Analyzer failed: {e}")
                best_container, best_score = None, 0.0

            if best_container is not None:
                try:
                    container_html = best_container.prettify()
                except Exception:
                    container_html = str(best_container)
                # Limit size to a safe token budget
                container_html_snippet = container_html[:6000]

                # Derive item selector and potential fields for context
                semantics = analyzer._analyze_container_semantics(best_container)
                samples = analyzer._extract_intelligent_samples(best_container, semantics.get('item_container_selector', ''))
                samples_text = '\n'.join(s.get('sample_html', '')[:1500] for s in samples)
            else:
                # Fallback: use truncated full page and text sample
                container_html_snippet = html_sample
                semantics = {'item_container_selector': '', 'potential_fields': {}}
                samples_text = text_sample

            # Detect dynamic content using Playwright
            dynamic_indicators = await self._detect_dynamic_content(url)

            analysis_prompt = f"""
Analyze the following website and extraction requirements (focused snippet):

URL: {url}
Requirements: {description}

Best repeating container HTML (truncated):
{container_html_snippet}

Representative item samples (truncated):
{samples_text}

Container analysis (inferred):
{json.dumps(semantics, ensure_ascii=False)}

Dynamic content analysis:
{json.dumps(dynamic_indicators, ensure_ascii=False)}

Tasks:
1. Determine if this is a static or dynamic website
2. Identify the best CSS selectors for the required data
3. Check for pagination or infinite scroll
4. Suggest a JSON schema for the output
5. Identify potential challenges or obstacles
6. Estimate confidence level (0.0 to 1.0)

Return your analysis in this JSON format:
{{
    "site_type": "static|dynamic",
    "selectors": {{"field_name": "css_selector"}},
    "pagination": {{"present": true/false, "strategy": "description"}},
    "schema": {{"field": "type"}},
    "challenges": ["list", "of", "challenges"],
    "confidence": 0.8,
    "recommended_approach": "description of best scraping approach",
    "dynamic_indicators": {dynamic_indicators}
}}

Be specific with CSS selectors and provide fallback options if possible.
"""
            logger.debug(f"Generated analysis prompt length={len(analysis_prompt)}")

            ai_start = time.time()
            response = await self._make_ai_request(
                messages=[{"role": "user", "content": analysis_prompt}],
                temperature=0.1
            )
            ai_duration = time.time() - ai_start
            logger.debug(f"AI analysis completed in {ai_duration:.2f}s")

            analysis_text = response.choices[0].message.content
            logger.debug(f"Raw AI response: {analysis_text[:500]}... (truncated)")

            try:
                analysis = json.loads(analysis_text)
                logger.debug("Parsed AI response as valid JSON")
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse AI response as JSON: {e}")
                analysis = {
                    "site_type": "static",
                    "selectors": {},
                    "pagination": {"present": False, "strategy": "none"},
                    "schema": {},
                    "challenges": ["JSON parsing failed from AI response"],
                    "confidence": 0.3,
                    "recommended_approach": "Basic static scraping with manual selector identification",
                    "dynamic_indicators": dynamic_indicators
                }

            # Ensure dynamic indicators are included
            analysis['dynamic_indicators'] = dynamic_indicators

            duration = time.time() - start_time
            logger.info(f"Website analysis completed in {duration:.2f}s with confidence {analysis.get('confidence', 0)}")
            await self._log_io('analyze_website', 'output', analysis)
            return analysis

        except Exception as e:
            logger.exception(f"Website analysis failed for {url}: {e}")
            await self._log_io('analyze_website', 'output', {'error': str(e)})
            raise

    async def generate_scraper(self, analysis: Dict[str, Any], url: str, description: str) -> str:
        await self._log_io('generate_scraper', 'input', {'analysis': analysis, 'url': url, 'description': description})
        logger.info(f"Generating scraper for {url}")
        logger.debug(f"Analysis input: {json.dumps(analysis, indent=2)[:500]}... (truncated)")

        scraper_prompt = f"""Generate complete, syntactically correct Python code for web scraping.

TARGET: {url}
TASK: {description}
ANALYSIS: {json.dumps(analysis, indent=2)}

REQUIREMENTS:
- Start with ALL imports: import requests, from bs4 import BeautifulSoup, from typing import Dict, Any, import time
- Function signature: def scrape_data(url: str) -> Dict[str, Any]:
- Return format: {{"data": [...], "metadata": {{...}}}}
- Use only: requests, BeautifulSoup4, standard library
- ALL requests.get() calls MUST include verify=False and timeout=10
- Add headers: {{'User-Agent': 'Mozilla/5.0'}}
- Add timeout, error handling, rate limiting with time.sleep(1)
- Maximum 3 pages, 25 second execution limit

CRITICAL: 
- Generate COMPLETE Python code only
- NO markdown, explanations, or incomplete blocks
- MUST start with: import requests
- ALL try blocks MUST have except/finally
- ALL function/class definitions MUST be complete
- Check your syntax before responding
- DO NOT include print() or result = scrape_data() calls
- End with ONLY the function definition, NO execution code

Example structure:
import requests
from bs4 import BeautifulSoup
from typing import Dict, Any
import time

def scrape_data(url: str) -> Dict[str, Any]:
    # Your code here
    return {{"data": data, "metadata": metadata}}"""
        logger.debug(f"Scraper prompt length={len(scraper_prompt)}")

        try:
            ai_start = time.time()
            response = await self._make_ai_request(
                messages=[{"role": "user", "content": scraper_prompt}],
                temperature=0.1
            )
            ai_duration = time.time() - ai_start
            logger.debug(f"AI scraper generation completed in {ai_duration:.2f}s")

            code = response.choices[0].message.content
            logger.debug(f"Raw generated code length={len(code)}")

            cleaned_code = self._clean_generated_code(code)
            logger.info("Scraper code generation completed successfully")
            logger.debug(f"Cleaned scraper code (first 500 chars):\n{cleaned_code[:500]}...")
            await self._log_io('generate_scraper', 'output', {'code': cleaned_code})

            return cleaned_code

        except Exception as e:
            logger.exception(f"Scraper generation failed for {url}: {e}")
            await self._log_io('generate_scraper', 'output', {'error': str(e)})
            raise

    async def generate_dynamic_scraper(self, analysis: Dict[str, Any], url: str, description: str) -> str:
        """Generate Playwright-based scraper for dynamic websites"""
        await self._log_io('generate_dynamic_scraper', 'input', {'analysis': analysis, 'url': url, 'description': description})
        logger.info(f"Generating dynamic scraper for {url}")
        
        strategy_selector = ScrapingStrategySelector()
        config = strategy_selector.get_strategy_config("dynamic", analysis)
        
        frameworks = analysis.get('dynamic_indicators', {}).get('javascript_frameworks', [])
        spa_patterns = analysis.get('dynamic_indicators', {}).get('spa_patterns', [])
        loading_indicators = analysis.get('dynamic_indicators', {}).get('dynamic_loading', [])
        
        scraper_prompt = f"""Generate complete, syntactically correct Python code for dynamic web scraping using Playwright.

TARGET: {url}
TASK: {description}
ANALYSIS: {json.dumps(analysis.get('selectors', {}), indent=2)}

DETECTED:
- JavaScript Frameworks: {frameworks}
- SPA Patterns: {spa_patterns}
- Dynamic Loading: {loading_indicators}

REQUIREMENTS:
- Use Playwright async API for browser automation
- Function signature: async def scrape_data(url: str) -> Dict[str, Any]:
- Return format: {{"data": [...], "metadata": {{...}}}}
- Handle dynamic content loading with proper waits
- Include error handling for timeouts and browser issues
- Maximum execution time: 60 seconds
- Handle modals/popups automatically
- Support infinite scroll if detected: {any('infinite-scroll' in indicator for indicator in loading_indicators)}

CRITICAL TEMPLATE:
```python
from playwright.async_api import async_playwright
import asyncio
import json
import time
from typing import Dict, Any, List

async def scrape_data(url: str) -> Dict[str, Any]:
    start_time = time.time()
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        
        try:
            page = await browser.new_page()
            
            # Set viewport and user agent
            await page.set_viewport_size({{"width": 1920, "height": 1080}})
            await page.set_extra_http_headers({{
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }})
            
            # Navigate and wait for content
            await page.goto(url, wait_until='networkidle', timeout=30000)
            
            # Handle modals/popups
            try:
                close_btn = await page.query_selector('[class*="close"], [class*="modal"] button, [aria-label*="close"]')
                if close_btn and await close_btn.is_visible():
                    await close_btn.click()
                    await page.wait_for_timeout(1000)
            except:
                pass
            
            # Wait for dynamic content
            await page.wait_for_load_state('networkidle', timeout=10000)
            
            # Your extraction logic here using the selectors from analysis
            # Extract data using page.query_selector_all() and related methods
            
            data = []  # Your extracted data
            
            execution_time = int((time.time() - start_time) * 1000)
            
            return {{
                "data": data,
                "metadata": {{
                    "execution_time_ms": execution_time,
                    "scraper_type": "dynamic",
                    "url": url,
                    "items_count": len(data)
                }}
            }}
            
        finally:
            await browser.close()
```

Generate COMPLETE working Python code ONLY. No explanations, no markdown blocks.
Make sure to implement the actual data extraction logic using the provided selectors.
"""

        try:
            ai_start = time.time()
            response = await self._make_ai_request(
                messages=[{"role": "user", "content": scraper_prompt}],
                temperature=0.1
            )
            ai_duration = time.time() - ai_start
            logger.debug(f"AI dynamic scraper generation completed in {ai_duration:.2f}s")

            code = response.choices[0].message.content
            logger.debug(f"Raw generated dynamic code length={len(code)}")

            cleaned_code = self._clean_generated_code(code, scraper_type="dynamic")
            logger.info("Dynamic scraper code generation completed successfully")
            await self._log_io('generate_dynamic_scraper', 'output', {'code': cleaned_code})

            return cleaned_code

        except Exception as e:
            logger.exception(f"Dynamic scraper generation failed for {url}: {e}")
            await self._log_io('generate_dynamic_scraper', 'output', {'error': str(e)})
            raise

    async def _detect_dynamic_content(self, url: str) -> Dict[str, Any]:
        """Detect dynamic content using browser automation"""
        try:
            async with DynamicScraperEngine(timeout=30) as scraper:
                return await scraper.detect_dynamic_content(url)
        except Exception as e:
            logger.warning(f"Failed to detect dynamic content for {url}: {e}")
            return {
                'javascript_frameworks': [],
                'spa_patterns': [],
                'dynamic_loading': [],
                'requires_interaction': False,
                'confidence_score': 0.0
            }

    async def refine_scraper(self, original_code: str, error_info: Dict[str, Any], analysis: Dict[str, Any]) -> str:
        await self._log_io('refine_scraper', 'input', {'original_code': original_code, 'error_info': error_info, 'analysis': analysis})
        logger.info("Refining scraper code based on errors")
        logger.debug(f"Original code length={len(original_code)}, Error info={json.dumps(error_info)}")

        refinement_prompt = f"""Fix this Python code. The code has syntax errors.

BROKEN CODE:
{original_code}

ERROR:
{json.dumps(error_info, indent=2)}

REQUIREMENTS:
- Fix ALL syntax errors
- Complete any incomplete try/except blocks
- Ensure ALL functions have proper return statements
- Generate COMPLETE, working Python code ONLY
- Function signature: def scrape_data(url: str) -> Dict[str, Any]:
- Must return {{"data": [...], "metadata": {{...}}}}

CRITICAL: Your response must be COMPLETE Python code with NO explanations, NO markdown, NO incomplete blocks."""
        logger.debug(f"Refinement prompt length={len(refinement_prompt)}")
        logger.info(f"corrected code: {refinement_prompt}")

        try:
            ai_start = time.time()
            response = await self._make_ai_request(
                messages=[{"role": "user", "content": refinement_prompt}],
                temperature=0.1
            )
            ai_duration = time.time() - ai_start
            logger.debug(f"AI refinement completed in {ai_duration:.2f}s")

            refined_code = response.choices[0].message.content
            logger.info(f"Raw refined code: {refined_code}")

            cleaned_code = self._clean_generated_code(refined_code)
            logger.info("Scraper refinement completed successfully")
            await self._log_io('refine_scraper', 'output', {'code': cleaned_code})
            return cleaned_code

        except Exception as e:
            logger.exception(f"Scraper refinement failed: {e}")
            await self._log_io('refine_scraper', 'output', {'error': str(e)})
            raise

    async def _fetch_website_content(self, url: str) -> Optional[str]:
        logger.debug(f"Fetching website content from {url}")
        try:
            async with self.session.get(url, max_redirects=3) as response:
                logger.debug(f"Received HTTP {response.status} from {url}")
                if response.status == 200:
                    content = await response.text()
                    logger.debug(f"Fetched {len(content)} chars from {url}")

                    if len(content) > settings.MAX_PAGE_SIZE:
                        logger.warning(f"Page size ({len(content)}) exceeds limit ({settings.MAX_PAGE_SIZE}), truncating")
                        return content[:settings.MAX_PAGE_SIZE]
                    return content
                else:
                    logger.error(f"HTTP {response.status} when fetching {url}")
                    return None
        except asyncio.TimeoutError:
            logger.error(f"Timeout when fetching {url}")
            return None
        except Exception as e:
            logger.exception(f"Error fetching {url}: {e}")
            return None

    def _clean_generated_code(self, code: str, scraper_type: str = "static") -> str:
        logger.debug(f"Cleaning generated {scraper_type} code")
        code_before = code[:200]
        
        # Remove markdown code blocks
        code = re.sub(r'^```python\n?', '', code, flags=re.MULTILINE)
        code = re.sub(r'^```\n?$', '', code, flags=re.MULTILINE)
        code = re.sub(r'^```.*$', '', code, flags=re.MULTILINE)
        
        # Find the start of actual Python code by looking for imports or function definitions
        lines = code.split('\n')
        code_start_idx = 0
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            if (stripped.startswith('import ') or 
                stripped.startswith('from ') or 
                stripped.startswith('def ') or
                stripped.startswith('async def ') or
                stripped.startswith('class ')):
                code_start_idx = i
                break
        
        # If we found the start of code, take everything from there
        if code_start_idx > 0:
            logger.debug(f"Found code start at line {code_start_idx}, removing {code_start_idx} explanatory lines")
            lines = lines[code_start_idx:]
            code = '\n'.join(lines)
        
        # Now filter out any remaining explanatory lines within the code
        lines = code.split('\n')
        cleaned_lines = []
        
        for line in lines:
            stripped = line.strip()
            
            # Skip empty lines (but preserve them for formatting)
            if not stripped:
                cleaned_lines.append(line)
                continue
                
            # Always keep imports, function definitions, and comments
            if (stripped.startswith('import ') or 
                stripped.startswith('from ') or 
                stripped.startswith('def ') or
                stripped.startswith('async def ') or
                stripped.startswith('class ') or
                stripped.startswith('#')):
                cleaned_lines.append(line)
                continue
            
            # Check for lines that are clearly explanatory text (not code)
            # These are lines that don't contain typical Python syntax
            has_python_syntax = any(keyword in stripped for keyword in [
                '=', '(', ')', '[', ']', '{', '}', ':', 'return', 'if', 'for', 'while', 
                'try', 'except', 'with', 'break', 'continue', 'True', 'False', 'None',
                'and', 'or', 'not', 'in', 'is', 'lambda', 'yield', 'pass', 'raise',
                'assert', 'global', 'nonlocal', 'del', 'async', 'await'
            ])
            
            # If it looks like a sentence (long, no Python syntax), skip it
            if (not has_python_syntax and 
                len(stripped.split()) > 4 and  # More than 4 words
                not stripped.endswith(':') and  # Not a label/statement
                '.' in stripped and  # Contains periods (sentence-like)
                stripped[0].isupper()):  # Starts with capital (sentence-like)
                logger.debug(f"Skipping explanatory line: {stripped[:50]}...")
                continue
                
            cleaned_lines.append(line)
        
        code = '\n'.join(cleaned_lines).strip()

        # Security validation
        dangerous_patterns = [
            r'__import__\s*\(',
            r'eval\s*\(',
            r'exec\s*\(',
            r'subprocess',
            r'os\.system',
            r'os\.popen',
            r'open\s*\(',
            r'file\s*\(',
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                logger.error(f"Generated code contains dangerous pattern: {pattern}")
                raise Exception(f"Generated code contains dangerous pattern: {pattern}")

        # Ensure required imports are present based on scraper type
        if scraper_type == "static":
            required_imports = [
                'import requests',
                'from bs4 import BeautifulSoup',
                'from typing import Dict, Any',
                'import time'
            ]
        else:  # dynamic
            required_imports = [
                'from playwright.async_api import async_playwright',
                'import asyncio',
                'from typing import Dict, Any',
                'import time',
                'import json'
            ]
        
        # Check and add missing imports at the beginning
        lines = code.split('\n')
        import_lines = []
        code_lines = []
        
        # Separate existing imports from code
        for line in lines:
            if line.strip().startswith(('import ', 'from ')):
                import_lines.append(line)
            else:
                code_lines.append(line)
        
        # Add missing imports
        for req_import in required_imports:
            if req_import not in '\n'.join(import_lines):
                logger.debug(f"Adding missing import: {req_import}")
                import_lines.insert(0, req_import)
        
        # Reconstruct code with all imports at the top
        code = '\n'.join(import_lines + [''] + code_lines)
        
        # Remove execution code (print statements, result = scrape_data() calls)
        lines = code.split('\n')
        cleaned_lines = []
        
        for line in lines:
            stripped = line.strip()
            # Skip lines that execute the scraper or print results
            if (stripped.startswith('result = scrape_data(') or
                stripped.startswith('print(result)') or
                stripped.startswith('print(scrape_data(') or
                (stripped.startswith('print(') and 'result' in stripped)):
                logger.debug(f"Removing execution line: {stripped}")
                continue
            cleaned_lines.append(line)
        
        code = '\n'.join(cleaned_lines)

        # Validate Python syntax
        try:
            compile(code, '<generated>', 'exec')
            logger.debug("Generated code passed syntax validation")
        except SyntaxError as e:
            logger.error(f"Generated code has syntax error: {e}")
            logger.error(f"Error at line {e.lineno}: {e.text}")
            # Try to fix common issues
            if "expected 'except' or 'finally'" in str(e):
                code += "\n    except Exception as e:\n        pass"
            elif "invalid syntax" in str(e) and e.text and "if not" in e.text:
                # Fix incomplete if statements
                lines = code.split('\n')
                if e.lineno <= len(lines):
                    line = lines[e.lineno - 1]
                    if line.strip().endswith('if not'):
                        lines[e.lineno - 1] = line + ' None:'
                        code = '\n'.join(lines)
            # Try compiling again
            try:
                compile(code, '<generated>', 'exec')
                logger.debug("Fixed syntax error")
            except SyntaxError:
                logger.error("Could not fix syntax error, returning as-is")

        logger.debug(f"Code cleaned. Before: {code_before}... After: {code[:200]}...")
        return code.strip()

    async def _log_io(self, method: str, io_type: str, data: Any):
        """Append input/output log to agent_io_log.txt"""
        log_path = os.path.join(os.path.dirname(__file__), 'agent_io_log.txt')
        timestamp = datetime.datetime.now().isoformat()
        
        # Truncate large data for readability
        if isinstance(data, dict) and 'code' in data:
            log_data = {**data, 'code': data['code'][:500] + '...' if len(data['code']) > 500 else data['code']}
        else:
            log_data = data
            
        entry = f"[{timestamp}] [{method}] [{io_type}] {json.dumps(log_data, ensure_ascii=False, indent=2)}\n\n"
        
        try:
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(entry)
        except Exception as e:
            logger.error(f"Failed to write log entry: {e}")
