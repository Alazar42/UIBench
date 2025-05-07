"""
Website evaluator for comprehensive analysis.
"""
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
        self.max_subpages = max_subpages or 5  # Default to 5 pages
        self.max_depth = min(max_depth, 2)  # Cap depth at 2
        self.concurrency = min(concurrency, 3)  # Cap concurrency at 3
        self.evaluated_pages: List[Dict[str, Any]] = []
        self.performance_monitor = PerformanceMonitor()
        self.network_cache = NetworkCache()
        self._browser_manager = None
        self.urls: List[str] = []
        self.base_url = root_url  # Add base_url attribute
    
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
                async with asyncio.timeout(5.0):  # 5 second timeout per page
                    # Check cache first
                    cached_response = self.network_cache.get_response(url)
                    if cached_response:
                        html = cached_response['content']
                    else:
                        html = await fetch_page_html(url)
                        self.network_cache.cache_response(url, html, {})
                    
                    soup = BeautifulSoup(html, "html.parser")
                    for a in soup.find_all("a", href=True):
                        if len(discovered_links) >= 10:  # Limit links per page
                            break
                        link = urljoin(self.url, a["href"])
                        if urlparse(link).netloc != urlparse(self.url).netloc:
                            continue
                        link = link.split("#")[0]
                        discovered_links.append((link, depth + 1))
            except asyncio.TimeoutError:
                logger.warning(f"Timeout crawling {url}")
            except Exception as e:
                logger.error(f"Error crawling {url}: {e}")
            
            return discovered_links
        
        async def worker():
            while True:
                try:
                    current_url, depth = await queue.get()
                except asyncio.CancelledError:
                    break
                
                if depth >= self.max_depth or len(visited) >= self.max_subpages:
                    queue.task_done()
                    continue
                
                discovered = await crawl_page(current_url, depth)
                for link, new_depth in discovered:
                    if link not in visited and len(visited) < self.max_subpages:
                        visited.add(link)
                        await queue.put((link, new_depth))
                queue.task_done()
        
        # Start workers with the crawler pool
        workers = [crawler_pool.add_task(worker()) for _ in range(self.concurrency)]
        
        try:
            async with asyncio.timeout(30.0):  # 30 second timeout for entire crawl
                await queue.join()
        except asyncio.TimeoutError:
            logger.warning("Crawl timeout reached")
        
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

        # Initialize URL list by crawling subpages
        self.urls = await self.crawl_all_subpages()

        results = {}
        page_ratings = []
        page_evaluations = {}
        analyzer_scores = {
            "accessibility": [],
            "performance": [],
            "security": [],
            "seo": [],
            "ux": [],
            "code": [],
            "design": [],
            "infrastructure": [],
            "operational": [],
            "compliance": []
        }

        with self.performance_monitor.monitor("website_evaluation"):
            for url in self.urls:
                try:
                    async with asyncio.timeout(10.0):  # 10 second timeout per page evaluation
                        # Try to get cached result
                        cached = self.network_cache.get_response(url)
                        if cached and "page_data" in cached:
                            page_data = cached["page_data"]
                        else:
                            # Get page content
                            page = await self.browser.new_page()
                            await page.goto(url, timeout=5000)  # 5 second page load timeout
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

                            # Cache the result
                            self.network_cache.cache_response(url, html, {"page_data": page_data})

                            # Cleanup
                            await page_evaluator.cleanup()
                            await page.close()

                        # Store page evaluation
                        page_name = page_data.get("page_name", "Unknown")
                        page_ratings.append(page_data.get("page_rating", 0))
                        page_evaluations[page_name] = {
                            "url": url,
                            "rating": page_data.get("page_rating", 0),
                            "class": page_data.get("page_class", "Unknown"),
                            "details": page_data.get("results", {})
                        }

                        # Collect analyzer scores
                        if "detailed_report" in page_data and "analyzer_scores" in page_data["detailed_report"]:
                            for analyzer, score in page_data["detailed_report"]["analyzer_scores"].items():
                                if analyzer in analyzer_scores:
                                    analyzer_scores[analyzer].append(score)

                except asyncio.TimeoutError:
                    logger.warning(f"Timeout evaluating {url}")
                    page_evaluations[url] = {
                        "error": "Evaluation timeout",
                        "rating": 0,
                        "class": "Error"
                    }
                except Exception as e:
                    logger.error(f"Error evaluating page {url}: {str(e)}")
                    page_evaluations[url] = {
                        "error": str(e),
                        "rating": 0,
                        "class": "Error"
                    }

            # Calculate overall website rating
            website_rating = sum(page_ratings) / len(page_ratings) if page_ratings else 0

            # Calculate average analyzer scores
            avg_analyzer_scores = {
                analyzer: sum(scores) / len(scores) if scores else 0
                for analyzer, scores in analyzer_scores.items()
            }

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
                },
                "detailed_report": {
                    "url": self.base_url,
                    "pages_evaluated": len(self.urls),
                    "analyzer_scores": avg_analyzer_scores,
                    "page_details": page_evaluations
                },
                "overall_score": website_rating,
                "analyzer_scores": avg_analyzer_scores
            }, ensure_ascii=False, indent=2)
    
    def _classify_website(self, rating: float) -> str:
        """Classify website based on rating."""
        if rating >= 90:
            return "Excellent"
        elif rating >= 75:
            return "Good"
        elif rating >= 60:
            return "Average"
        else:
            return "Needs Improvement"
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        if self._browser_manager:
            await self._browser_manager.cleanup()