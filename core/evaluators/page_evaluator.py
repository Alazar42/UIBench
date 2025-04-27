from typing import Dict, Any
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
import asyncio

from .base_evaluator import BaseEvaluator
from ..analyzers.accessibility_analyzer import AccessibilityAnalyzer
from ..analyzers.performance_analyzer import PerformanceAnalyzer
from ..analyzers.security_analyzer import SecurityAnalyzer
from ..analyzers.ux_analyzer import UXAnalyzer
from ..analyzers.code_analyzer import CodeAnalyzer
from ..analyzers.seo_analyzer import SEOAnalyzer
from ..utils.html_parser import fetch_page_html

class PageEvaluator(BaseEvaluator):
    """Evaluates a single page by combining multiple analysis types."""
    
    def __init__(self, url: str, html: str, page, body_text: str, custom_criteria: Dict[str, Any] = None):
        super().__init__(url, custom_criteria)
        self.html = html
        self.page = page
        self.body_text = body_text
        self.soup = BeautifulSoup(self.html, "html.parser")
        self.design_data = {}
        
        # Initialize analyzers
        self.accessibility_analyzer = AccessibilityAnalyzer()
        self.performance_analyzer = PerformanceAnalyzer()
        self.security_analyzer = SecurityAnalyzer()
        self.ux_analyzer = UXAnalyzer()
        self.code_analyzer = CodeAnalyzer()
        self.seo_analyzer = SEOAnalyzer()
    
    async def validate(self) -> bool:
        """Validate the page for evaluation."""
        try:
            # Check if URL is valid
            parsed_url = urlparse(self.url)
            if not all([parsed_url.scheme, parsed_url.netloc]):
                return False
            
            # Check if HTML content is valid
            if not self.html or not self.soup:
                return False
            
            return True
        except Exception:
            return False
    
    async def evaluate(self) -> Dict[str, Any]:
        """Perform comprehensive page evaluation."""
        if not await self.validate():
            raise ValueError("Invalid page for evaluation")
        
        results = {}
        
        # Run all analyzers
        results.update(await self.accessibility_analyzer.analyze(self.page, self.soup))
        results.update(await self.performance_analyzer.analyze(self.url, self.page))
        results.update(await self.security_analyzer.analyze(self.url, self.page))
        results.update(await self.ux_analyzer.analyze(self.page, self.soup))
        results.update(await self.code_analyzer.analyze(self.html, self.soup))
        results.update(await self.seo_analyzer.analyze(self.soup))
        
        return {
            "url": self.url,
            "results": results,
            "design_data": self.design_data
        }
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        if self.page:
            await self.page.close() 