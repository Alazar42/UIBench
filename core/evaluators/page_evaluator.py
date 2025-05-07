"""
Page evaluator for analyzing individual web pages.
"""
import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup
from ..utils.performance_utils import async_timed
from ..utils.analysis_cache import AnalysisCache, AnalysisResult
from ..analyzers.base_analyzer import BaseAnalyzer
from ..analyzers.accessibility_analyzer import AccessibilityAnalyzer
from ..analyzers.performance_analyzer import PerformanceAnalyzer
from ..analyzers.security_analyzer import SecurityAnalyzer
from ..analyzers.seo_analyzer import SEOAnalyzer
from ..analyzers.ux_analyzer import UXAnalyzer
from ..analyzers.code_analyzer import CodeAnalyzer
from ..analyzers.compliance_analyzer import ComplianceAnalyzer
from ..analyzers.design_system_analyzer import DesignSystemAnalyzer
from ..analyzers.infrastructure_analyzer import InfrastructureAnalyzer
from ..analyzers.nlp_content_analyzer import NLPContentAnalyzer
from ..analyzers.operational_metrics_analyzer import OperationalMetricsAnalyzer
from ..analyzers.mutation_analyzer import MutationAnalyzer
from ..analyzers.contract_analyzer import ContractAnalyzer
from ..analyzers.fuzz_analyzer import FuzzAnalyzer
from datetime import datetime

logger = logging.getLogger(__name__)

class AnalyzerGroup:
    """Groups analyzers by their dependencies and execution requirements."""
    def __init__(self, name: str, analyzers: List[BaseAnalyzer]):
        self.name = name
        self.analyzers = analyzers

class PageEvaluator:
    """Evaluates a single page by combining multiple analysis types."""
    
    # Define analyzer groups
    ANALYZER_GROUPS = {
        "accessibility": AnalyzerGroup("accessibility", [AccessibilityAnalyzer()]),
        "performance": AnalyzerGroup("performance", [PerformanceAnalyzer()]),
        "security": AnalyzerGroup("security", [SecurityAnalyzer()]),
        "seo": AnalyzerGroup("seo", [SEOAnalyzer()]),
        "ux": AnalyzerGroup("ux", [UXAnalyzer()]),
        "code": AnalyzerGroup("code", [CodeAnalyzer()]),
        "compliance": AnalyzerGroup("compliance", [ComplianceAnalyzer()]),
        "design": AnalyzerGroup("design", [DesignSystemAnalyzer()]),
        "infrastructure": AnalyzerGroup("infrastructure", [InfrastructureAnalyzer()]),
        "nlp": AnalyzerGroup("nlp", [NLPContentAnalyzer()]),
        "operational": AnalyzerGroup("operational", [OperationalMetricsAnalyzer()]),
        "mutation": AnalyzerGroup("mutation", [MutationAnalyzer()]),
        "contract": AnalyzerGroup("contract", [ContractAnalyzer()]),
        "fuzz": AnalyzerGroup("fuzz", [FuzzAnalyzer()])
    }
    
    def __init__(self, url: str, html: str, page, body_text: str):
        self.url = url
        self._html = html
        self.page = page
        self.body_text = body_text
        self._soup = None
        self.analysis_cache = AnalysisCache()
        self.analyzers = {}
    
    @property
    async def html(self) -> str:
        """Get the HTML content."""
        if not self._html:
            self._html = await self.page.content()
        return self._html
    
    @property
    async def soup(self) -> BeautifulSoup:
        """Get the BeautifulSoup object."""
        if not self._soup:
            html = await self.html
            self._soup = BeautifulSoup(html, "html.parser")
        return self._soup
    
    async def validate(self) -> bool:
        """Validate the page for analysis."""
        try:
            if not self.url or not self.page:
                return False
            
            # Check if page is accessible
            try:
                await self.page.wait_for_load_state("networkidle")
                return True
            except Exception as e:
                logger.error(f"Page validation failed: {str(e)}")
                return False
                
        except Exception as e:
            logger.error(f"Validation failed: {str(e)}")
            return False
    
    @async_timed()
    async def run_analyzer_group(self, group: AnalyzerGroup) -> Dict[str, Any]:
        """Run a group of analyzers."""
        results = {}
        
        for analyzer in group.analyzers:
            try:
                # Generate analyzer ID from class name and URL
                analyzer_id = f"{analyzer.__class__.__name__}_{self.url}"
                
                # Check cache first
                cached_result = await self.analysis_cache.get_result(self.url, analyzer_id)
                
                if cached_result and self.analysis_cache.is_valid(cached_result):
                    results[analyzer.__class__.__name__] = cached_result.results
                    continue
                
                # Run analyzer with appropriate parameters
                soup = await self.soup
                try:
                    # Try with soup parameter first
                    result = await analyzer.analyze(self.url, self.page, soup)
                except TypeError:
                    try:
                        # Try without soup parameter
                        result = await analyzer.analyze(self.url, self.page)
                    except TypeError:
                        # Try with just url and html
                        html = await self.html
                        result = await analyzer.analyze(self.url, html)
                
                # Handle different result formats
                if isinstance(result, str):
                    try:
                        result_dict = json.loads(result)
                    except json.JSONDecodeError:
                        result_dict = {"error": "Invalid JSON result", "status": "failed"}
                else:
                    result_dict = result
                
                # Standardize result format
                if isinstance(result_dict, dict):
                    if "results" in result_dict:
                        # Extract results from nested structure
                        standardized_result = result_dict["results"]
                    else:
                        standardized_result = result_dict
                else:
                    standardized_result = {"error": "Invalid result format", "status": "failed"}
                
                # Ensure required fields are present
                if isinstance(standardized_result, dict):
                    if "overall_score" not in standardized_result:
                        standardized_result["overall_score"] = 0.0
                    if "details" not in standardized_result:
                        standardized_result["details"] = {}
                    if "issues" not in standardized_result:
                        standardized_result["issues"] = []
                    if "recommendations" not in standardized_result:
                        standardized_result["recommendations"] = []
                    if "metrics" not in standardized_result:
                        standardized_result["metrics"] = {}
                
                # Convert back to JSON string for storage
                results[analyzer.__class__.__name__] = json.dumps({
                    "results": standardized_result,
                    "json_path": f"analysis_results/{analyzer.__class__.__name__.lower()}_{self.url.replace('://', '_').replace('/', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                })
                
                # Cache result
                analysis_result = AnalysisResult(
                    analyzer_id=analyzer_id,
                    url=self.url,
                    timestamp=datetime.now(),
                    results=standardized_result,
                    metadata={"group": group.name},
                    version="1.0.0"
                )
                await self.analysis_cache.store_result(analysis_result)
                
            except Exception as e:
                logger.error(f"Analyzer {analyzer.__class__.__name__} failed: {str(e)}")
                error_result = {
                    "error": str(e),
                    "status": "failed",
                    "overall_score": 0.0,
                    "details": {},
                    "issues": [f"Analysis failed: {str(e)}"],
                    "recommendations": ["Fix analyzer implementation"],
                    "metrics": {}
                }
                results[analyzer.__class__.__name__] = json.dumps({
                    "results": error_result,
                    "json_path": f"analysis_results/{analyzer.__class__.__name__.lower()}_{self.url.replace('://', '_').replace('/', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                })
        
        return results
    
    @async_timed()
    async def evaluate(self) -> str:
        """Evaluate the page using all analyzer groups."""
        try:
            if not await self.validate():
                raise ValueError("Page validation failed")
            
            results = {}
            design_data = {}
            
            for group_name, group in self.ANALYZER_GROUPS.items():
                group_results = await self.run_analyzer_group(group)
                results[group_name] = group_results
                
                # Extract design data from design system analyzer results
                if group_name == "design" and group_results:
                    for analyzer_result in group_results.values():
                        if isinstance(analyzer_result, dict) and "design_data" in analyzer_result:
                            design_data.update(analyzer_result["design_data"])
            
            # Calculate overall score
            scores = []
            for group_results in results.values():
                for analyzer_result in group_results.values():
                    if isinstance(analyzer_result, dict) and "score" in analyzer_result:
                        scores.append(analyzer_result["score"])
            
            overall_score = sum(scores) / len(scores) if scores else 0
            
            # Classify page
            page_class = await self._classify_page(results)
            
            # Prepare final results
            final_results = {
                "url": self.url,
                "page_rating": overall_score,
                "page_class": page_class,
                "results": results,
                "design_data": design_data,
                "performance_metrics": results.get("performance", {})  # <-- Add this line
            }
            
            return json.dumps(final_results)
            
        except Exception as e:
            logger.error(f"Page evaluation failed: {str(e)}")
            return json.dumps({
                "error": str(e),
                "status": "failed",
                "design_data": {}
            })
    
    async def _classify_page(self, results: Dict[str, Any]) -> str:
        """Classify the page based on analysis results."""
        try:
            # Get page name
            page_name = await self._get_page_name()
            
            # Determine page type
            if "login" in page_name.lower() or "signin" in page_name.lower():
                return "authentication"
            elif "dashboard" in page_name.lower():
                return "dashboard"
            elif "profile" in page_name.lower():
                return "profile"
            elif "settings" in page_name.lower():
                return "settings"
            else:
                return "content"
                
        except Exception as e:
            logger.error(f"Page classification failed: {str(e)}")
            return "unknown"
    
    async def _get_page_name(self) -> str:
        """Get the page name from title or URL."""
        try:
            title = await self.page.title()
            if title:
                return title
            
            # Fallback to URL
            return self.url.split("/")[-1]
            
        except Exception as e:
            logger.error(f"Failed to get page name: {str(e)}")
            return "unknown"
    
    async def cleanup(self):
        """Clean up resources."""
        try:
            if self.page:
                await self.page.close()
        except Exception as e:
            logger.error(f"Cleanup failed: {str(e)}")