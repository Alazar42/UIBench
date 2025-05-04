from typing import Dict, Any, List, Type
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
import asyncio
import logging
from datetime import datetime
import json

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
        AnalyzerGroup("performance", [PerformanceAnalyzer], requires_page=True),
        AnalyzerGroup("interaction", [UXAnalyzer, AccessibilityAnalyzer], requires_page=True),
        AnalyzerGroup("security", [SecurityAnalyzer], requires_page=True)
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
    
    @async_timed()
    async def run_analyzer_group(self, group: AnalyzerGroup) -> Dict[str, Any]:
        """Run a group of analyzers concurrently."""
        tasks = []
        results = {}
        
        for analyzer_class in group.analyzers:
            analyzer_name = analyzer_class.__name__.lower().replace('analyzer', '')
            analyzer = self.analyzers.get(analyzer_name)
            
            if not analyzer:
                continue
            
            # Check cache first if available
            if self.analysis_cache:
                try:
                    cached_result = await self.analysis_cache.get_result(self.url, analyzer_name)
                    if cached_result and self.analysis_cache.is_valid(cached_result):
                        results.update(cached_result.results)
                        continue
                except Exception as e:
                    logger.warning(f"Cache check failed for {analyzer_name}: {str(e)}")
            
            # Create analysis task based on analyzer requirements
            if analyzer_name == "seo":
                task = analyzer.analyze(self.url, self.soup)
            elif analyzer_name == "code":
                task = analyzer.analyze(self.url, self.html, self.soup)
            elif group.requires_page:
                task = analyzer.analyze(self.url, self.page, self.soup)
            else:
                task = analyzer.analyze(self.url, self.html, self.soup)
            
            tasks.append((analyzer_name, task))
        
        # Run all tasks concurrently
        if tasks:
            task_results = await asyncio.gather(*[task for _, task in tasks], return_exceptions=True)
            
            # Process results
            for (analyzer_name, _), result in zip(tasks, task_results):
                if isinstance(result, Exception):
                    logger.error(f"Analysis failed for {analyzer_name}: {str(result)}")
                    results[analyzer_name] = {"error": str(result)}
                else:
                    try:
                        result_data = json.loads(result)
                        results[analyzer_name] = result_data
                        
                        # Cache successful results
                        if self.analysis_cache and "error" not in result_data:
                            await self.analysis_cache.store_result(
                                AnalysisResult(
                                    analyzer_id=analyzer_name,
                                    url=self.url,
                                    timestamp=datetime.now(),
                                    results=result_data,
                                    metadata={},
                                    version="1.0.0"
                                )
                            )
                    except json.JSONDecodeError:
                        logger.error(f"Invalid JSON result from {analyzer_name}")
                        results[analyzer_name] = {"error": "Invalid JSON result"}
        
        return results
    
    @async_timed()
    async def evaluate(self) -> str:
        """Perform comprehensive page evaluation and return JSON string."""
        if not await self.validate():
            raise ValueError("Invalid page for evaluation")
        
        results = {}
        analyzer_scores = []
        
        with self.performance_monitor.monitor("page_evaluation"):
            # Run analyzer groups in sequence (they are already internally parallel)
            for group in self.ANALYZER_GROUPS:
                group_results = await self.run_analyzer_group(group)
                results.update(group_results)
                
                # Collect scores from each analyzer
                for analyzer_name, analyzer_result in group_results.items():
                    if isinstance(analyzer_result, dict) and "results" in analyzer_result:
                        score = analyzer_result["results"].get("overall_score", 0)
                        if score > 0:  # Only include valid scores
                            analyzer_scores.append(score)
            
            # Calculate page rating
            page_rating = sum(analyzer_scores) / len(analyzer_scores) if analyzer_scores else 0
            
            # Classify page based on rating
            page_class = self._classify_page(page_rating)
            
            # Add performance metrics
            evaluation_metrics = self.performance_monitor.get_metrics("page_evaluation")
            analyzer_metrics = {
                name: self.performance_monitor.get_metrics(f"{name}_analysis")
                for name in self.analyzers.keys()
            }
            
            # Extract page name from URL
            page_name = self._get_page_name(self.url)
            
            return json.dumps({
                "url": self.url,
                "page_name": page_name,
                "page_rating": page_rating,
                "page_class": page_class,
                "results": results,
                "design_data": self.design_data,
                "performance_metrics": {
                    "evaluation": evaluation_metrics,
                    "analyzers": analyzer_metrics
                }
            }, ensure_ascii=False, indent=2)
    
    def _classify_page(self, rating: float) -> str:
        """Classify page based on its rating."""
        if rating >= 90:
            return "Excellent"
        elif rating >= 75:
            return "Good"
        elif rating >= 60:
            return "Fair"
        elif rating >= 40:
            return "Poor"
        else:
            return "Critical"
    
    def _get_page_name(self, url: str) -> str:
        """Extract page name from URL."""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            path = parsed.path.strip('/')
            if not path:
                return "Home"
            return path.split('/')[-1].replace('-', ' ').title()
        except:
            return "Unknown"
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        try:
            if self.page:
                await self.page.close()
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
        finally:
            self.page = None