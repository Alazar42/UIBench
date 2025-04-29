from typing import Dict, Any, List, Type
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
import asyncio
import logging
from datetime import datetime

from .base_evaluator import BaseEvaluator
from ..analyzers.accessibility_analyzer import AccessibilityAnalyzer
from ..analyzers.performance_analyzer import PerformanceAnalyzer
from ..analyzers.security_analyzer import SecurityAnalyzer
from ..analyzers.ux_analyzer import UXAnalyzer
from ..analyzers.code_analyzer import CodeAnalyzer
from ..analyzers.seo_analyzer import SEOAnalyzer
from ..utils.html_parser import fetch_page_html
from ..utils.performance_utils import async_timed, PerformanceMonitor
from ..utils.analysis_cache import AnalysisCache, AnalysisResult
from ..config import Settings

logger = logging.getLogger(__name__)
config = Settings()

class AnalyzerGroup:
    """Groups analyzers by their dependencies and execution requirements."""
    
    def __init__(self, name: str, analyzers: List[Type[BaseEvaluator]], requires_page: bool = True):
        self.name = name
        self.analyzers = analyzers
        self.requires_page = requires_page

class PageEvaluator(BaseEvaluator):
    """Evaluates a single page by combining multiple analysis types."""
    
    # Define analyzer groups for coordinated execution
    ANALYZER_GROUPS = [
        AnalyzerGroup("content", [SEOAnalyzer, CodeAnalyzer], requires_page=False),
        AnalyzerGroup("interaction", [UXAnalyzer, AccessibilityAnalyzer], requires_page=True),
        AnalyzerGroup("technical", [PerformanceAnalyzer, SecurityAnalyzer], requires_page=True)
    ]
    
    def __init__(self, url: str, html: str, page, body_text: str, custom_criteria: Dict[str, Any] = None):
        super().__init__(url, custom_criteria)
        self.html = html
        self.page = page
        self.body_text = body_text
        self.soup = BeautifulSoup(self.html, "html.parser")
        self.design_data = {}
        self.performance_monitor = PerformanceMonitor()
        self.analysis_cache = AnalysisCache()
        
        # Initialize analyzers with configuration
        self.analyzers = {
            "accessibility": AccessibilityAnalyzer(),
            "performance": PerformanceAnalyzer(),
            "security": SecurityAnalyzer(),
            "ux": UXAnalyzer(),
            "code": CodeAnalyzer(),
            "seo": SEOAnalyzer()
        }
    
    @async_timed()
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
        except Exception as e:
            logger.error(f"Validation error for {self.url}: {str(e)}")
            return False
    
    async def run_analyzer_group(self, group: AnalyzerGroup) -> Dict[str, Any]:
        """Run a group of analyzers concurrently."""
        tasks = []
        results = {}
        
        for analyzer_class in group.analyzers:
            analyzer_name = analyzer_class.__name__.lower().replace('analyzer', '')
            analyzer = self.analyzers.get(analyzer_name)
            
            if not analyzer:
                continue
            
            # Check cache first
            cached_result = self.analysis_cache.get_result(self.url, analyzer_name)
            if cached_result and self.analysis_cache.is_valid(cached_result):
                results.update(cached_result.results)
                continue
            
            # Create analysis task
            async def run_analysis(a_name: str, a: BaseEvaluator):
                try:
                    with self.performance_monitor.monitor(f"{a_name}_analysis"):
                        if group.requires_page:
                            result = await a.analyze(self.url, self.page)
                        else:
                            result = await a.analyze(self.html, self.soup)
                        
                        # Cache the result
                        self.analysis_cache.store_result(AnalysisResult(
                            analyzer_id=a_name,
                            url=self.url,
                            timestamp=datetime.now(),
                            results=result,
                            metadata={},
                            version="1.0.0"
                        ))
                        
                        return result
                except Exception as e:
                    logger.error(f"Error in {a_name} analyzer: {str(e)}")
                    return {a_name: {"error": str(e), "score": 0}}
            
            tasks.append(run_analysis(analyzer_name, analyzer))
        
        if tasks:
            group_results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in group_results:
                if isinstance(result, dict):
                    results.update(result)
        
        return results
    
    @async_timed()
    async def evaluate(self) -> Dict[str, Any]:
        """Perform comprehensive page evaluation with coordinated analyzer execution."""
        if not await self.validate():
            raise ValueError("Invalid page for evaluation")
        
        results = {}
        
        with self.performance_monitor.monitor("page_evaluation"):
            # Run analyzer groups in sequence (they are already internally parallel)
            for group in self.ANALYZER_GROUPS:
                group_results = await self.run_analyzer_group(group)
                results.update(group_results)
            
            # Add performance metrics
            evaluation_metrics = self.performance_monitor.get_metrics("page_evaluation")
            analyzer_metrics = {
                name: self.performance_monitor.get_metrics(f"{name}_analysis")
                for name in self.analyzers.keys()
            }
            
            return {
                "url": self.url,
                "results": results,
                "design_data": self.design_data,
                "performance_metrics": {
                    "evaluation": evaluation_metrics,
                    "analyzers": analyzer_metrics
                }
            }
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        try:
            if self.page:
                await self.page.close()
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
        finally:
            self.page = None 