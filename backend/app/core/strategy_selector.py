import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class ScrapingStrategySelector:
    """
    Determines the best scraping approach based on website analysis
    """
    
    def select_strategy(self, analysis: Dict[str, Any], force_dynamic: bool = False) -> str:
        """
        Returns: "static", "dynamic", or "hybrid"
        """
        # If dynamic scraping was already used successfully, force dynamic strategy
        if force_dynamic:
            logger.info("Forcing dynamic strategy due to successful dynamic content retrieval")
            return "dynamic"
            
        # Get dynamic indicators
        dynamic_indicators = analysis.get('dynamic_indicators', {})
        confidence_score = dynamic_indicators.get('confidence_score', 0.0)
        
        # Check for explicit dynamic requirements
        js_frameworks = dynamic_indicators.get('javascript_frameworks', [])
        spa_patterns = dynamic_indicators.get('spa_patterns', [])
        dynamic_loading = dynamic_indicators.get('dynamic_loading', [])
        
        logger.info(f"Strategy selection - Confidence: {confidence_score}, "
                   f"JS Frameworks: {js_frameworks}, SPA: {spa_patterns}, "
                   f"Dynamic Loading: {dynamic_loading}")
        
        # High confidence dynamic indicators
        if confidence_score > 0.7:
            return "dynamic"
        
        # Medium confidence - use hybrid approach
        elif confidence_score > 0.3:
            return "hybrid"
        
        # Low confidence or clear static indicators
        else:
            return "static"
    
    def get_strategy_config(self, strategy: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Returns configuration for the selected strategy
        """
        dynamic_indicators = analysis.get('dynamic_indicators', {})
        
        configs = {
            "static": {
                "engine": "requests",
                "timeout": 30,
                "libraries": ["requests", "beautifulsoup4", "json", "time"],
                "approach": "Traditional HTTP request + BeautifulSoup parsing"
            },
            "dynamic": {
                "engine": "playwright",
                "timeout": 60,
                "browser": "chromium",
                "headless": True,
                "wait_strategy": self._get_wait_strategy(dynamic_indicators),
                "handle_scroll": self._should_handle_scroll(dynamic_indicators),
                "max_scrolls": 3,
                "libraries": ["playwright", "asyncio", "json", "time"],
                "approach": "Browser automation with JavaScript execution"
            },
            "hybrid": {
                "primary": "static",
                "fallback": "dynamic",
                "fallback_triggers": ["empty_results", "minimal_content", "js_required"],
                "timeout": 45,
                "approach": "Try static first, fallback to dynamic if needed"
            }
        }
        
        base_config = configs.get(strategy, configs["static"])
        
        # Add analysis-specific configurations
        if strategy == "dynamic":
            base_config.update(self._get_dynamic_specific_config(dynamic_indicators))
        
        return base_config
    
    def _get_wait_strategy(self, dynamic_indicators: Dict[str, Any]) -> str:
        """Determine the best wait strategy based on detected patterns"""
        frameworks = dynamic_indicators.get('javascript_frameworks', [])
        loading_indicators = dynamic_indicators.get('dynamic_loading', [])
        
        # React/Next.js often needs networkidle
        if any(fw in ['React', 'Next.js'] for fw in frameworks):
            return 'networkidle'
        
        # Vue/Nuxt typically loads faster
        elif any(fw in ['Vue', 'Nuxt'] for fw in frameworks):
            return 'domcontentloaded'
        
        # If loading indicators detected, wait for networkidle
        elif loading_indicators:
            return 'networkidle'
        
        # Default
        else:
            return 'networkidle'
    
    def _should_handle_scroll(self, dynamic_indicators: Dict[str, Any]) -> bool:
        """Determine if infinite scroll handling is needed"""
        loading_indicators = dynamic_indicators.get('dynamic_loading', [])
        return any('infinite-scroll' in indicator or 'load-more' in indicator 
                  for indicator in loading_indicators)
    
    def _get_dynamic_specific_config(self, dynamic_indicators: Dict[str, Any]) -> Dict[str, Any]:
        """Get dynamic scraping specific configuration"""
        config = {}
        
        frameworks = dynamic_indicators.get('javascript_frameworks', [])
        
        # Framework-specific configurations
        if 'React' in frameworks:
            config['react_mode'] = True
            config['wait_for_react'] = True
        
        if 'Vue' in frameworks:
            config['vue_mode'] = True
        
        if any(fw in ['Next.js', 'Nuxt'] for fw in frameworks):
            config['ssr_mode'] = True
            config['wait_strategy'] = 'networkidle'
        
        # SPA specific settings
        spa_patterns = dynamic_indicators.get('spa_patterns', [])
        if spa_patterns:
            config['spa_mode'] = True
            config['wait_for_navigation'] = True
        
        return config

    def should_fallback_to_dynamic(self, static_result: Dict[str, Any], 
                                 analysis: Dict[str, Any]) -> bool:
        """
        Determine if we should fallback from static to dynamic scraping
        """
        if not static_result.get('success', False):
            return True
        
        data = static_result.get('data', [])
        
        # Empty results
        if not data:
            logger.info("Fallback triggered: Empty results from static scraping")
            return True
        
        # Very minimal content (likely missing JS-rendered content)
        if len(data) < 3 and all(
            len(str(item).strip()) < 50 for item in data 
            if isinstance(item, (str, dict))
        ):
            logger.info("Fallback triggered: Minimal content detected")
            return True
        
        # High dynamic confidence from analysis
        dynamic_score = analysis.get('dynamic_indicators', {}).get('confidence_score', 0)
        if dynamic_score > 0.6:
            logger.info(f"Fallback triggered: High dynamic confidence ({dynamic_score})")
            return True
        
        return False
