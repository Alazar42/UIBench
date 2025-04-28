from typing import Dict, Any, List, Set, Tuple, Optional
import asyncio
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import logging
from datetime import datetime
import traceback

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
    async def evaluate(self, crawl: bool = False) -> Dict[str, Any]:
        """Evaluate the website."""
        if not await self.validate():
            raise ValueError("Invalid website for evaluation")
        
        with self.performance_monitor.monitor("website_evaluation"):
            pages = await self.crawl_all_subpages() if crawl else [self.url]
            logger.info(f"Crawling complete. {len(pages)} page(s) to evaluate.")
            
            # Get browser manager and pool
            browser_manager = await self.get_browser_manager()
            browser_pool = await browser_manager.get_pool(
                max_browsers=config.resources.max_browsers,
                max_pages_per_browser=config.resources.max_pages_per_browser
            )
            
            async def evaluate_page(url: str) -> Dict[str, Any]:
                """Evaluate a single page using the browser pool."""
                try:
                    async def page_task(page):
                        await page.goto(url, timeout=config.resources.browser_timeout * 1000)
                        html = await page.content()
                        body_text = await page.inner_text("body")
                        evaluator = PageEvaluator(url, html, page, body_text, custom_criteria=self.custom_criteria)
                        return await evaluator.evaluate()
                    
                    return await browser_pool.execute_in_page(page_task)
                except Exception as e:
                    logger.error(f"Error evaluating {url}: {traceback.format_exc()}")
                    return {
                        "url": url,
                        "error": str(e),
                        "results": {}
                    }
            
            # Process pages in batches
            evaluations = await batch_process(
                pages,
                evaluate_page,
                batch_size=config.performance.batch_size
            )
            
            self.evaluated_pages = [e for e in evaluations if e is not None]
            report = self.aggregate_report(self.evaluated_pages)
            report["detailed_report"] = self.generate_detailed_report(self.evaluated_pages)
            report["performance_metrics"] = self.performance_monitor.get_metrics("website_evaluation")
            
            return report
    
    def aggregate_report(self, evaluations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate evaluation results into a comprehensive report."""
        total_pages = len(evaluations)
        if total_pages == 0:
            raise ValueError("No pages evaluated.")
        
        # Calculate aggregated scores
        scores = {
            "accessibility": 0,
            "performance": 0,
            "seo": 0,
            "security": 0,
            "usability": 0,
            "code_quality": 0
        }
        
        for eval in evaluations:
            results = eval.get("results", {})
            for key in scores:
                if key in results:
                    scores[key] += results[key].get("score", 0)
        
        # Average the scores
        for key in scores:
            scores[key] = scores[key] / total_pages
        
        # Collect defects
        defects = {}
        for eval in evaluations:
            url = eval.get("url")
            for check, result in eval.get("results", {}).items():
                if isinstance(result, dict) and result.get("defects"):
                    defects.setdefault(url, {})[check] = result.get("defects")
        
        return {
            "homepage": self.url,
            "pages_evaluated": total_pages,
            "aggregated_scores": scores,
            "defect_details": defects,
            "recommendations": self.generate_recommendations(evaluations),
            "evaluated_at": datetime.utcnow().isoformat(),
            "pages": evaluations
        }
    
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