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
from openai import AsyncOpenAI
import logging
from config.settings import settings

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

    def __init__(self, api_key: str, model: str = "gpt-4o"):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
        self.session = None
        logger.debug(f"UnifiedAgent initialized with model={model}")

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

Tasks:
1. Determine if this is a static or dynamic website
2. Identify the best CSS selectors for the required data
3. Check for pagination or infinite scroll
4. Suggest a JSON schema for the output
5. Identify potential challenges or obstacles
6. Estimate confidence level (0.0 to 1.0)

Return your analysis in this JSON format:

Return your analysis in this JSON format:
{{
    "site_type": "static|dynamic",
    "selectors": {{"field_name": "css_selector"}},
    "pagination": {{"present": true/false, "strategy": "description"}},
    "schema": {{"field": "type"}},
    "challenges": ["list", "of", "challenges"],
    "confidence": 0.8,
    "recommended_approach": "description of best scraping approach"
}}

Be specific with CSS selectors and provide fallback options if possible.
"""
            logger.debug(f"Generated analysis prompt length={len(analysis_prompt)}")

            ai_start = time.time()
            response = await self.client.chat.completions.create(
                model=self.model,
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
                    "recommended_approach": "Basic static scraping with manual selector identification"
                }

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

        scraper_prompt = f"""
You are a Python code generator. Your response must contain ONLY valid Python code.  

Context:
- Website URL: {url}
- Description: {description}
- Analysis: {json.dumps(analysis, indent=2)}

STRICT requirements:
1. Output only Python code. No markdown, no triple backticks, no explanations, no natural language.
2. All non-code information must appear only as inline comments inside the code.
3. The code must begin with Python import statements and end with the function definition.
4. The function signature must be:

def scrape_data(url: str) -> Dict[str, Any]:
    # implementation
    return {{"data": [...], "metadata": {{...}}}}

5. Implementation rules:
   - Use only requests and BeautifulSoup4 (no Selenium, Playwright, or external libraries).
   - Data must be JSON-serializable.
   - Add error handling for network, parsing, and missing elements.
   - Handle pagination (max 3 pages).
   - Add rate limiting (1 second between requests).
   - Use a realistic user-agent header.
   - Respect robots.txt rules.
   - Enforce execution timeout of 25 seconds.
   - Collect both "data" and "metadata" (pages_scraped, total_items, errors, etc.).

If you output anything other than Python code (e.g., explanations, markdown, notes, or extra formatting), you have FAILED.  

Begin your response immediately with Python imports and end with the function definition.
"""
        logger.debug(f"Scraper prompt length={len(scraper_prompt)}")

        try:
            ai_start = time.time()
            response = await self.client.chat.completions.create(
                model=self.model,
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

    async def refine_scraper(self, original_code: str, error_info: Dict[str, Any], analysis: Dict[str, Any]) -> str:
        await self._log_io('refine_scraper', 'input', {'original_code': original_code, 'error_info': error_info, 'analysis': analysis})
        logger.info("Refining scraper code based on errors")
        logger.debug(f"Original code length={len(original_code)}, Error info={json.dumps(error_info)}")

        refinement_prompt = f"""
The following scraper code failed during testing. Please fix the issues and return improved code.

Original Code:
{original_code}

Error Information:
{json.dumps(error_info, indent=2)}

Original Analysis:
{json.dumps(analysis, indent=2)}

Common issues to check:
1. CSS selectors that don't match elements
2. Missing error handling for network requests  
3. Incorrect data extraction logic
4. Missing pagination handling
5. Timeout issues
6. Empty results due to wrong selectors

Please return the corrected Python code with the same function signature.
Focus on making the selectors more robust and adding better error handling.
If selectors are failing, try more generic approaches or multiple fallback selectors.

IMPORTANT: Generate ONLY valid Python code. Do NOT include:
- Any explanatory text or comments outside the code
- Markdown formatting or code blocks  
- Instructions or notes to the user
- Any text that is not valid Python syntax

Start your response with the imports and end with the function definition.

DON't INCLUDE ANYTHING OTHER THEN CODE. not even a single word or code block (```python)
"""
        logger.debug(f"Refinement prompt length={len(refinement_prompt)}")
        logger.info(f"corrected code: {refinement_prompt}")

        try:
            ai_start = time.time()
            response = await self.client.chat.completions.create(
                model=self.model,
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

    def _clean_generated_code(self, code: str) -> str:
        logger.debug("Cleaning generated code")
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

        # Ensure required imports are present
        required_imports = ['import requests', 'from bs4 import BeautifulSoup']
        for req_import in required_imports:
            if req_import not in code:
                logger.debug(f"Adding missing import: {req_import}")
                code = req_import + '\n' + code

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
