from typing import Dict, Any, List, Set, Tuple, Optional
import asyncio
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import logging
from datetime import datetime
import traceback
import json

from .base_evaluator import BaseEvaluator
from .page_evaluator import PageEvaluator
from ..utils.html_parser import fetch_page_html
from ..utils.browser_manager import BrowserManager
from ..utils.async_utils import batch_process, AsyncPool
from ..utils.performance_utils import async_timed, PerformanceMonitor
from ..utils.cache import NetworkCache
from ..config import Settings

logger = logging.getLogger(__name__)
config = Settings()

class WebsiteEvaluator(BaseEvaluator):
    """Manages crawling and evaluation for an entire website."""
    
    def __init__(
        self,
        root_url: str,
        max_subpages: Optional[int] = None,
        max_depth: int = 10,
        concurrency: int = config.performance.max_concurrent,
        custom_criteria: Dict[str, Any] = None
    ):
        super().__init__(root_url, custom_criteria)
        self.max_subpages = max_subpages
        self.max_depth = max_depth
        self.concurrency = concurrency
        self.evaluated_pages: List[Dict[str, Any]] = []
        self.performance_monitor = PerformanceMonitor()
        self.network_cache = NetworkCache()
        self._browser_manager = None
    
    async def get_browser_manager(self) -> BrowserManager:
        """Get or create the browser manager instance."""
        if not self._browser_manager:
            self._browser_manager = await BrowserManager.get_instance()
        return self._browser_manager
    
    @async_timed()
    async def validate(self) -> bool:
        """Validate the website for evaluation."""
        try:
            parsed_url = urlparse(self.url)
            if not all([parsed_url.scheme, parsed_url.netloc]):
                return False
            return True
        except Exception:
            return False
    
    @async_timed()
    async def crawl_all_subpages(self) -> List[str]:
        """Crawl all subpages of the website."""
        if not await self.validate():
            raise ValueError("Invalid website for evaluation")
        
        visited: Set[str] = set()
        queue: asyncio.Queue[Tuple[str, int]] = asyncio.Queue()
        visited.add(self.url)
        queue.put_nowait((self.url, 0))
        
        # Create a pool for managing concurrent crawlers
        crawler_pool = AsyncPool(max_concurrency=self.concurrency)
        
        async def crawl_page(url: str, depth: int) -> List[str]:
            """Crawl a single page and return discovered links."""
            discovered_links = []
            
            try:
                # Check cache first
                cached_response = self.network_cache.get_response(url)
                if cached_response:
                    html = cached_response['content']
                else:
                    html = await fetch_page_html(url)
                    self.network_cache.cache_response(url, html, {})
                
                soup = BeautifulSoup(html, "html.parser")
                for a in soup.find_all("a", href=True):
                    link = urljoin(self.url, a["href"])
                    if urlparse(link).netloc != urlparse(self.url).netloc:
                        continue
                    link = link.split("#")[0]
                    discovered_links.append((link, depth + 1))
            except Exception as e:
                logger.error(f"Error crawling {url}: {e}")
            
            return discovered_links
        
        async def worker():
            while True:
                try:
                    current_url, depth = await queue.get()
                except asyncio.CancelledError:
                    break
                
                if depth >= self.max_depth:
                    queue.task_done()
                    continue
                
                discovered = await crawl_page(current_url, depth)
                for link, new_depth in discovered:
                    if link not in visited:
                        visited.add(link)
                        await queue.put((link, new_depth))
                        if self.max_subpages and len(visited) >= self.max_subpages:
                            queue.task_done()
                            return
                queue.task_done()
        
        # Start workers with the crawler pool
        workers = [crawler_pool.add_task(worker()) for _ in range(self.concurrency)]
        await queue.join()
        for w in workers:
            if not isinstance(w, asyncio.Task):
                w = asyncio.create_task(w)
            w.cancel()
        
        return list(visited)
    
    @async_timed()
    async def evaluate(self) -> str:
        """Perform comprehensive website evaluation and return JSON string."""
        if not await self.validate():
            raise ValueError("Invalid website for evaluation")
        
        results = {}
        page_ratings = []
        page_evaluations = {}
        
        with self.performance_monitor.monitor("website_evaluation"):
            # Evaluate each page
            for url in self.urls:
                try:
                    # Get page content
                    page = await self.browser.new_page()
                    await page.goto(url)
                    html = await page.content()
                    soup = BeautifulSoup(html, "html.parser")
                    body_text = soup.get_text()
                    
                    # Create and run page evaluator
                    page_evaluator = PageEvaluator(
                        url=url,
                        html=html,
                        page=page,
                        body_text=body_text,
                        custom_criteria=self.custom_criteria
                    )
                    
                    page_result = await page_evaluator.evaluate()
                    page_data = json.loads(page_result)
                    
                    # Store page evaluation
                    page_name = page_data.get("page_name", "Unknown")
                    page_ratings.append(page_data.get("page_rating", 0))
                    page_evaluations[page_name] = {
                        "url": url,
                        "rating": page_data.get("page_rating", 0),
                        "class": page_data.get("page_class", "Unknown"),
                        "details": page_data.get("results", {})
                    }
                    
                    # Cleanup
                    await page_evaluator.cleanup()
                    await page.close()
                    
                except Exception as e:
                    logger.error(f"Error evaluating page {url}: {str(e)}")
                    page_evaluations[url] = {
                        "error": str(e),
                        "rating": 0,
                        "class": "Error"
                    }
            
            # Calculate overall website rating
            website_rating = sum(page_ratings) / len(page_ratings) if page_ratings else 0
            
            # Classify website based on rating
            website_class = self._classify_website(website_rating)
            
            # Add performance metrics
            evaluation_metrics = self.performance_monitor.get_metrics("website_evaluation")
            
            return json.dumps({
                "website_url": self.base_url,
                "website_rating": website_rating,
                "website_class": website_class,
                "page_evaluations": page_evaluations,
                "performance_metrics": {
                    "evaluation": evaluation_metrics
                }
            }, ensure_ascii=False, indent=2)
    
    def _classify_website(self, rating: float) -> str:
        """Classify website based on its overall rating."""
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
    
    def aggregate_report(self, page_results: List[Dict]) -> Dict:
        """Aggregate results from all pages into a comprehensive report."""
        aggregated = {
            "overall_score": 0.0,
            "page_count": len(page_results),
            "analyzer_scores": {},
            "issues": [],
            "recommendations": []
        }
        
        # Initialize score counters
        score_weights = {
            "accessibility": 0.2,
            "performance": 0.2,
            "seo": 0.2,
            "security": 0.2,
            "usability": 0.1,
            "code_quality": 0.1
        }
        
        # Aggregate scores and collect issues
        for page in page_results:
            for analyzer_name, analyzer_result in page.get("results", {}).items():
                if analyzer_name not in aggregated["analyzer_scores"]:
                    aggregated["analyzer_scores"][analyzer_name] = {
                        "total_score": 0.0,
                        "count": 0,
                        "issues": []
                    }
                
                # Handle different analyzer result formats
                if isinstance(analyzer_result, dict):
                    score = analyzer_result.get("score", 0.0)
                    issues = analyzer_result.get("issues", [])
                    recommendations = analyzer_result.get("recommendations", [])
                else:
                    score = analyzer_result
                    issues = []
                    recommendations = []
                
                aggregated["analyzer_scores"][analyzer_name]["total_score"] += score
                aggregated["analyzer_scores"][analyzer_name]["count"] += 1
                aggregated["analyzer_scores"][analyzer_name]["issues"].extend(issues)
                aggregated["issues"].extend(issues)
                aggregated["recommendations"].extend(recommendations)
        
        # Calculate weighted average scores
        for analyzer_name, data in aggregated["analyzer_scores"].items():
            if data["count"] > 0:
                avg_score = data["total_score"] / data["count"]
                weight = score_weights.get(analyzer_name, 0.1)
                aggregated["overall_score"] += avg_score * weight
        
        # Remove duplicate issues and recommendations
        aggregated["issues"] = list(set(aggregated["issues"]))
        aggregated["recommendations"] = list(set(aggregated["recommendations"]))
        
        return aggregated
    
    def generate_detailed_report(self, evaluations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a detailed report with specific metrics."""
        return {
            "aesthetic": [e["results"].get("aesthetic_metrics", {}) for e in evaluations],
            "wcag": [e["results"].get("wcag_details", {}) for e in evaluations],
            "cross_device": [e["results"].get("cross_device_simulation", {}) for e in evaluations],
            "performance_metrics": self.performance_monitor.get_metrics("website_evaluation")
        }
    
    def generate_recommendations(self, evaluations: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on evaluation results."""
        recs = []
        
        # Language issues
        lang_issues = sum(len(p["results"].get("language_quality", {}).get("grammar_errors", [])) for p in evaluations)
        if lang_issues > 0:
            recs.append(f"Address {lang_issues} language/grammar issues found in content")
        
        # Code issues
        code_issues = sum(len(p["results"].get("code_quality", {}).get("html", {}).get("html_issues", [])) for p in evaluations)
        if code_issues > 0:
            recs.append(f"Fix {code_issues} HTML/CSS code quality issues")
        
        # Cognitive load
        try:
            avg_cog_load = sum(p["results"].get("ux_enhanced", {}).get("cognitive_load", {}).get("complexity_score", 0) for p in evaluations)/len(evaluations)
            if avg_cog_load > 50:
                recs.append("Simplify page layouts to reduce cognitive load")
        except (ZeroDivisionError, KeyError):
            pass
        
        # First page specific checks
        if evaluations and "results" in evaluations[0]:
            first = evaluations[0]["results"]
            if first.get("alt_text", {}).get("missing", 0) > 0:
                recs.append("Add alt text to images")
        
        return recs
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        try:
            if self._browser_manager:
                browser_manager = await self.get_browser_manager()
                await browser_manager.close_all()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
        finally:
            self._browser_manager = None