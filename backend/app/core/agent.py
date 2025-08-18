import json
import re
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
    
    def __init__(self, api_key: str, model: str = "gpt-4"):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=settings.REQUEST_TIMEOUT),
            headers={'User-Agent': settings.USER_AGENT}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def analyze_website(self, url: str, description: str) -> Dict[str, Any]:
        """Analyze website structure and plan extraction strategy"""
        try:
            logger.info(f"Starting website analysis for {url}")
            
            # Fetch website content
            html_content = await self._fetch_website_content(url)
            if not html_content:
                raise Exception("Failed to fetch website content")
            
            # Parse HTML and get sample
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements for cleaner analysis
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text content and structure sample
            html_sample = str(soup)[:2000]  # First 2000 characters
            text_sample = soup.get_text()[:1000]  # First 1000 characters of text
            
            # Analysis prompt
            analysis_prompt = f"""
Analyze the following website and extraction requirements:

URL: {url}
Requirements: {description}

Website HTML structure (first 2000 chars):
{html_sample}

Website text content (first 1000 chars):
{text_sample}

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
            
            # Get AI analysis
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": analysis_prompt}],
                temperature=0.1
            )
            
            analysis_text = response.choices[0].message.content
            logger.debug(f"AI analysis response: {analysis_text}")
            
            # Parse JSON response with fallback
            try:
                analysis = json.loads(analysis_text)
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse AI response as JSON: {e}")
                # Fallback analysis
                analysis = {
                    "site_type": "static",
                    "selectors": {},
                    "pagination": {"present": False, "strategy": "none"},
                    "schema": {},
                    "challenges": ["JSON parsing failed from AI response"],
                    "confidence": 0.3,
                    "recommended_approach": "Basic static scraping with manual selector identification"
                }
            
            logger.info(f"Website analysis completed with confidence: {analysis.get('confidence', 0)}")
            return analysis
            
        except Exception as e:
            logger.error(f"Website analysis failed: {e}")
            raise Exception(f"Website analysis failed: {str(e)}")
    
    async def generate_scraper(self, analysis: Dict[str, Any], url: str, description: str) -> str:
        """Generate Python scraper code based on analysis"""
        try:
            logger.info(f"Generating scraper code for {url}")
            
            scraper_prompt = f"""
Generate Python scraper code based on this analysis:

URL: {url}
Description: {description}
Analysis: {json.dumps(analysis, indent=2)}

Requirements:
- Use requests and BeautifulSoup4 only (no Selenium/Playwright)
- Include comprehensive error handling
- Return data as JSON-serializable dict
- Handle pagination if needed (max 3 pages for MVP)
- Include rate limiting (1 second delay between requests)
- Add realistic user-agent header
- Follow robots.txt respectfully
- Limit total execution time to 25 seconds
- Handle common issues like missing elements gracefully

Function signature must be:
def scrape_data(url: str) -> Dict[str, Any]:
    # Your implementation here
    return {{"data": [...], "metadata": {{...}}}}

The function should return:
- "data": List of extracted items
- "metadata": Information about the scraping process (pages_scraped, total_items, etc.)

Generate only the Python code, no explanations or markdown formatting.
Include proper imports at the top.
"""
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": scraper_prompt}],
                temperature=0.1
            )
            
            code = response.choices[0].message.content
            logger.debug(f"Generated scraper code length: {len(code)} characters")
            
            # Clean up the code
            cleaned_code = self._clean_generated_code(code)
            logger.info("Scraper code generation completed")
            
            return cleaned_code
            
        except Exception as e:
            logger.error(f"Scraper generation failed: {e}")
            raise Exception(f"Scraper generation failed: {str(e)}")
    
    async def refine_scraper(self, original_code: str, error_info: Dict[str, Any], analysis: Dict[str, Any]) -> str:
        """Refine scraper based on test failures"""
        try:
            logger.info("Refining scraper code based on test results")
            
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

Generate only the corrected Python code, no explanations.
"""
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": refinement_prompt}],
                temperature=0.1
            )
            
            refined_code = response.choices[0].message.content
            cleaned_code = self._clean_generated_code(refined_code)
            
            logger.info("Scraper code refinement completed")
            return cleaned_code
            
        except Exception as e:
            logger.error(f"Scraper refinement failed: {e}")
            raise Exception(f"Scraper refinement failed: {str(e)}")
    
    async def _fetch_website_content(self, url: str) -> Optional[str]:
        """Fetch website content with error handling"""
        try:
            async with self.session.get(url, max_redirects=3) as response:
                if response.status == 200:
                    content = await response.text()
                    
                    # Check content size
                    if len(content) > settings.MAX_PAGE_SIZE:
                        logger.warning(f"Page size ({len(content)}) exceeds limit ({settings.MAX_PAGE_SIZE})")
                        content = content[:settings.MAX_PAGE_SIZE]
                    
                    return content
                else:
                    logger.error(f"HTTP {response.status} when fetching {url}")
                    return None
                    
        except asyncio.TimeoutError:
            logger.error(f"Timeout when fetching {url}")
            return None
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
    
    def _clean_generated_code(self, code: str) -> str:
        """Clean and validate generated code"""
        # Remove markdown code blocks
        code = re.sub(r'^```python\n?', '', code, flags=re.MULTILINE)
        code = re.sub(r'^```\n?$', '', code, flags=re.MULTILINE)
        code = re.sub(r'^```.*$', '', code, flags=re.MULTILINE)
        
        # Basic security validation
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
                code = req_import + '\n' + code
        
        return code.strip()
