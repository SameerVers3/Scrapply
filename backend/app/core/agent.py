import json
import re
import time
import datetime
import os
from typing import Dict, Any, Optional
import aiohttp
import asyncio
from bs4 import BeautifulSoup
from openai import AsyncOpenAI
import logging
from config.settings import settings

logger = logging.getLogger(__name__)

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
            logger.info(f"HTML sample: {html_sample} and Text Sample : {text_sample}")

            analysis_prompt = f"""
Analyze the following website and extraction requirements:

URL: {url}
Requirements: {description}

Website HTML structure:
{str(soup)}

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
