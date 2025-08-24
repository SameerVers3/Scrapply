import asyncio
import json
import logging
import re
from typing import Dict, Any, Optional, List
from playwright.async_api import async_playwright, Browser, Page, TimeoutError as PlaywrightTimeout
from config.settings import settings

logger = logging.getLogger(__name__)

class DynamicScraperEngine:
    """
    Handles dynamic content scraping using Playwright browser automation
    """
    
    def __init__(self, timeout: int = 60, headless: bool = True):
        self.timeout = timeout
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--no-first-run',
                '--no-default-browser-check',
                '--disable-background-timer-throttling',
                '--disable-backgrounding-occluded-windows',
                '--disable-renderer-backgrounding'
            ]
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.page:
            await self.page.close()
        if self.browser:
            await self.browser.close()
        if hasattr(self, 'playwright'):
            await self.playwright.stop()

    async def detect_dynamic_content(self, url: str) -> Dict[str, Any]:
        """
        Detect if website requires JavaScript rendering
        """
        logger.info(f"Detecting dynamic content for: {url}")
        
        dynamic_indicators = {
            'javascript_frameworks': [],
            'spa_patterns': [],
            'dynamic_loading': [],
            'requires_interaction': False,
            'confidence_score': 0.0
        }
        
        try:
            self.page = await self.browser.new_page()
            
            # Set a realistic viewport and user agent
            await self.page.set_viewport_size({"width": 1920, "height": 1080})
            await self.page.set_extra_http_headers({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            })
            
            # Get initial HTML (before JS execution)
            await self.page.goto(url, wait_until='domcontentloaded', timeout=self.timeout * 1000)
            initial_html = await self.page.content()
            
            # Wait for network idle and get final HTML
            try:
                await self.page.wait_for_load_state('networkidle', timeout=10000)
            except PlaywrightTimeout:
                logger.warning("Network idle timeout, continuing with analysis")
            
            final_html = await self.page.content()
            
            # Check for JS frameworks
            js_frameworks = await self._detect_js_frameworks(final_html)
            dynamic_indicators['javascript_frameworks'] = js_frameworks
            
            # Check for SPA patterns
            spa_patterns = await self._detect_spa_patterns(final_html)
            dynamic_indicators['spa_patterns'] = spa_patterns
            
            # Check for dynamic loading indicators
            loading_indicators = await self._detect_loading_indicators()
            dynamic_indicators['dynamic_loading'] = loading_indicators
            
            # Check if content changed significantly after JS execution
            content_change_ratio = self._calculate_content_change(initial_html, final_html)
            
            # Calculate confidence score
            confidence_score = 0.0
            if js_frameworks:
                confidence_score += 0.4
            if spa_patterns:
                confidence_score += 0.3
            if loading_indicators:
                confidence_score += 0.2
            if content_change_ratio > 0.3:
                confidence_score += 0.3
            
            dynamic_indicators['confidence_score'] = min(confidence_score, 1.0)
            dynamic_indicators['content_change_ratio'] = content_change_ratio
            
            logger.info(f"Dynamic content detection completed. Confidence: {confidence_score:.2f}")
            return dynamic_indicators
            
        except Exception as e:
            logger.error(f"Error detecting dynamic content: {e}")
            return dynamic_indicators
        finally:
            if self.page:
                await self.page.close()
                self.page = None

    async def _detect_js_frameworks(self, html: str) -> List[str]:
        """Detect JavaScript frameworks in the HTML"""
        frameworks = []
        
        framework_patterns = {
            'React': [r'react', r'ReactDOM', r'data-reactroot', r'__REACT_DEVTOOLS_GLOBAL_HOOK__'],
            'Vue': [r'Vue', r'vue\.js', r'v-app', r'data-v-'],
            'Angular': [r'angular', r'ng-', r'ng-app', r'data-ng-'],
            'Next.js': [r'__NEXT_DATA__', r'_next/', r'next\.js'],
            'Nuxt': [r'__NUXT__', r'nuxt\.js'],
            'Svelte': [r'svelte'],
            'jQuery': [r'jquery', r'\$\('],
            'Ember': [r'ember', r'Ember\.'],
            'Backbone': [r'backbone', r'Backbone\.']
        }
        
        html_lower = html.lower()
        for framework, patterns in framework_patterns.items():
            for pattern in patterns:
                if re.search(pattern, html_lower, re.IGNORECASE):
                    frameworks.append(framework)
                    break
        
        return frameworks

    async def _detect_spa_patterns(self, html: str) -> List[str]:
        """Detect Single Page Application patterns"""
        patterns = []
        
        spa_indicators = [
            (r'id="app"', 'app-root'),
            (r'id="root"', 'react-root'),
            (r'router-outlet', 'angular-router'),
            (r'v-app', 'vue-app'),
            (r'data-reactroot', 'react-spa'),
            (r'ng-app', 'angular-spa'),
            (r'<div[^>]*class="[^"]*app[^"]*"', 'app-container')
        ]
        
        for pattern, name in spa_indicators:
            if re.search(pattern, html, re.IGNORECASE):
                patterns.append(name)
        
        return patterns

    async def _detect_loading_indicators(self) -> List[str]:
        """Detect dynamic loading indicators on the page"""
        indicators = []
        
        try:
            # Check for common loading selectors
            loading_selectors = [
                '[class*="loading"]',
                '[class*="spinner"]',
                '[class*="loader"]',
                '[id*="loading"]',
                '.skeleton',
                '[data-loading]'
            ]
            
            for selector in loading_selectors:
                elements = await self.page.query_selector_all(selector)
                if elements:
                    indicators.append(f"loading-element-{selector}")
            
            # Check for lazy loading images
            lazy_images = await self.page.query_selector_all('img[loading="lazy"], img[data-src]')
            if lazy_images:
                indicators.append('lazy-loading-images')
            
            # Check for infinite scroll patterns
            scroll_triggers = await self.page.query_selector_all('[class*="infinite"], [class*="load-more"]')
            if scroll_triggers:
                indicators.append('infinite-scroll')
                
        except Exception as e:
            logger.warning(f"Error detecting loading indicators: {e}")
        
        return indicators

    def _calculate_content_change(self, initial_html: str, final_html: str) -> float:
        """Calculate how much content changed after JS execution"""
        try:
            from bs4 import BeautifulSoup
            
            initial_soup = BeautifulSoup(initial_html, 'html.parser')
            final_soup = BeautifulSoup(final_html, 'html.parser')
            
            # Remove script and style tags for comparison
            for tag in ['script', 'style', 'noscript']:
                for element in initial_soup.find_all(tag):
                    element.decompose()
                for element in final_soup.find_all(tag):
                    element.decompose()
            
            initial_text = initial_soup.get_text(strip=True)
            final_text = final_soup.get_text(strip=True)
            
            if not initial_text:
                return 1.0 if final_text else 0.0
            
            # Simple content change ratio
            initial_len = len(initial_text)
            final_len = len(final_text)
            
            if initial_len == 0:
                return 1.0 if final_len > 0 else 0.0
            
            change_ratio = abs(final_len - initial_len) / initial_len
            return min(change_ratio, 1.0)
            
        except Exception as e:
            logger.warning(f"Error calculating content change: {e}")
            return 0.0

    async def scrape_with_browser(self, url: str, selectors: Dict[str, str], config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Main method for dynamic scraping using browser automation
        """
        logger.info(f"Starting dynamic scraping for: {url}")
        config = config or {}
        
        try:
            self.page = await self.browser.new_page()
            
            # Configure page
            await self.page.set_viewport_size({"width": 1920, "height": 1080})
            await self.page.set_extra_http_headers({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            })
            
            # Navigate to page
            await self.page.goto(url, wait_until='networkidle', timeout=self.timeout * 1000)
            
            # Handle modals/popups if present
            await self._handle_modals()
            
            # Wait for content to load
            await self._wait_for_content(config.get('wait_strategy', 'networkidle'))
            
            # Handle infinite scroll if configured
            if config.get('handle_scroll', False):
                await self._handle_infinite_scroll(config.get('max_scrolls', 3))
            
            # Extract data using selectors
            data = await self._extract_data_with_selectors(selectors)
            
            # Get page metadata
            metadata = await self._get_page_metadata()
            
            logger.info(f"Dynamic scraping completed. Extracted {len(data)} items")
            
            return {
                "data": data,
                "metadata": metadata,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Dynamic scraping failed: {e}")
            return {
                "error": str(e),
                "success": False
            }
        finally:
            if self.page:
                await self.page.close()
                self.page = None

    async def _handle_modals(self):
        """Handle common modal/popup patterns"""
        modal_selectors = [
            '[class*="modal"] [class*="close"]',
            '[class*="popup"] [class*="close"]',
            '[class*="overlay"] [class*="close"]',
            'button[aria-label*="close"]',
            'button[aria-label*="dismiss"]',
            '.modal-backdrop',
            '[data-dismiss="modal"]'
        ]
        
        for selector in modal_selectors:
            try:
                close_button = await self.page.query_selector(selector)
                if close_button and await close_button.is_visible():
                    await close_button.click()
                    await self.page.wait_for_timeout(1000)
                    logger.debug(f"Closed modal using selector: {selector}")
                    break
            except Exception:
                continue

    async def _wait_for_content(self, strategy: str = 'networkidle'):
        """Wait for content based on strategy"""
        try:
            if strategy == 'networkidle':
                await self.page.wait_for_load_state('networkidle', timeout=10000)
            elif strategy == 'domcontentloaded':
                await self.page.wait_for_load_state('domcontentloaded')
            elif isinstance(strategy, dict) and 'selector' in strategy:
                await self.page.wait_for_selector(strategy['selector'], timeout=10000)
            else:
                await self.page.wait_for_timeout(3000)  # Fallback
        except PlaywrightTimeout:
            logger.warning(f"Wait strategy '{strategy}' timed out, continuing")

    async def _handle_infinite_scroll(self, max_scrolls: int = 3):
        """Handle infinite scroll scenarios"""
        logger.debug(f"Handling infinite scroll with max {max_scrolls} scrolls")
        
        for i in range(max_scrolls):
            try:
                # Get current scroll position
                prev_height = await self.page.evaluate("document.body.scrollHeight")
                
                # Scroll to bottom
                await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                
                # Wait for new content
                await self.page.wait_for_timeout(2000)
                
                # Check if new content loaded
                new_height = await self.page.evaluate("document.body.scrollHeight")
                
                if new_height == prev_height:
                    logger.debug(f"No new content after scroll {i+1}, stopping")
                    break
                    
                logger.debug(f"Scroll {i+1}: Page height increased from {prev_height} to {new_height}")
                
            except Exception as e:
                logger.warning(f"Error during scroll {i+1}: {e}")
                break

    async def _extract_data_with_selectors(self, selectors: Dict[str, str]) -> List[Dict[str, Any]]:
        """Extract data using provided CSS selectors"""
        try:
            # Find container elements (assuming first selector is the item container)
            container_selector = list(selectors.values())[0] if selectors else 'body'
            
            # If we have multiple selectors, treat first as container, rest as field selectors
            if len(selectors) > 1:
                field_selectors = {k: v for k, v in list(selectors.items())[1:]}
                items = await self.page.query_selector_all(container_selector)
            else:
                # Single selector - extract all matching elements
                field_selectors = {}
                items = await self.page.query_selector_all(container_selector)
            
            data = []
            
            for item in items[:50]:  # Limit to 50 items for safety
                item_data = {}
                
                if field_selectors:
                    # Extract specific fields
                    for field_name, field_selector in field_selectors.items():
                        try:
                            element = await item.query_selector(field_selector)
                            if element:
                                # Get text content or attribute value
                                if field_selector.endswith('[src]') or field_selector.endswith('[href]'):
                                    attr_name = field_selector.split('[')[-1].replace(']', '')
                                    value = await element.get_attribute(attr_name)
                                else:
                                    value = await element.text_content()
                                
                                item_data[field_name] = value.strip() if value else ""
                        except Exception as e:
                            logger.debug(f"Error extracting field {field_name}: {e}")
                            item_data[field_name] = ""
                else:
                    # Extract all text if no specific fields
                    text = await item.text_content()
                    item_data['content'] = text.strip() if text else ""
                
                if item_data and any(v for v in item_data.values()):
                    data.append(item_data)
            
            return data
            
        except Exception as e:
            logger.error(f"Error extracting data: {e}")
            return []

    async def _get_page_metadata(self) -> Dict[str, Any]:
        """Get page metadata"""
        try:
            title = await self.page.title()
            url = self.page.url
            
            return {
                'title': title,
                'url': url,
                'timestamp': asyncio.get_event_loop().time(),
                'scraper_type': 'dynamic',
                'browser': 'chromium'
            }
        except Exception as e:
            logger.warning(f"Error getting metadata: {e}")
            return {'scraper_type': 'dynamic', 'browser': 'chromium'}
