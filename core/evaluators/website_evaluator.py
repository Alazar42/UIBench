from typing import Dict, Any, List, Set, Tuple, Optional
import asyncio
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import logging
from datetime import datetime
from playwright.async_api import async_playwright

from .base_evaluator import BaseEvaluator
from .page_evaluator import PageEvaluator
from ..utils.html_parser import fetch_page_html
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
        concurrency: int = config.max_concurrent,
        custom_criteria: Dict[str, Any] = None
    ):
        super().__init__(root_url, custom_criteria)
        self.max_subpages = max_subpages
        self.max_depth = max_depth
        self.concurrency = concurrency
        self.evaluated_pages: List[Dict[str, Any]] = []
    
    async def validate(self) -> bool:
        """Validate the website for evaluation."""
        try:
            parsed_url = urlparse(self.url)
            if not all([parsed_url.scheme, parsed_url.netloc]):
                return False
            return True
        except Exception:
            return False
    
    async def crawl_all_subpages(self) -> List[str]:
        """Crawl all subpages of the website."""
        if not await self.validate():
            raise ValueError("Invalid website for evaluation")
        
        visited: Set[str] = set()
        queue: asyncio.Queue[Tuple[str, int]] = asyncio.Queue()
        visited.add(self.url)
        queue.put_nowait((self.url, 0))
        semaphore = asyncio.Semaphore(self.concurrency)
        
        async def worker():
            while True:
                try:
                    current_url, depth = await queue.get()
                except asyncio.CancelledError:
                    break
                
                if depth >= self.max_depth:
                    queue.task_done()
                    continue
                
                try:
                    async with semaphore:
                        html = await fetch_page_html(current_url)
                except Exception as e:
                    logger.error(f"Error fetching {current_url}: {e}")
                    queue.task_done()
                    continue
                
                soup = BeautifulSoup(html, "html.parser")
                for a in soup.find_all("a", href=True):
                    link = urljoin(self.url, a["href"])
                    if urlparse(link).netloc != urlparse(self.url).netloc:
                        continue
                    link = link.split("#")[0]
                    if link not in visited:
                        visited.add(link)
                        await queue.put((link, depth + 1))
                        if self.max_subpages and len(visited) >= self.max_subpages:
                            queue.task_done()
                            return
                queue.task_done()
        
        workers = [asyncio.create_task(worker()) for _ in range(self.concurrency)]
        await queue.join()
        for w in workers:
            w.cancel()
        
        return list(visited)
    
    async def evaluate(self, crawl: bool = False) -> Dict[str, Any]:
        """Evaluate the website."""
        if not await self.validate():
            raise ValueError("Invalid website for evaluation")
        
        pages = await self.crawl_all_subpages() if crawl else [self.url]
        logger.info(f"Crawling complete. {len(pages)} page(s) to evaluate.")
        
        evaluations = []
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            for url in pages:
                page = await browser.new_page()
                try:
                    await page.goto(url, timeout=60000)
                    html = await page.content()
                    body_text = await page.inner_text("body")
                    evaluator = PageEvaluator(url, html, page, body_text, custom_criteria=self.custom_criteria)
                    result = await evaluator.evaluate()
                    evaluations.append(result)
                except Exception as e:
                    logger.error(f"Error evaluating {url}: {e}")
                finally:
                    await page.close()
            await browser.close()
        
        self.evaluated_pages = evaluations
        report = self.aggregate_report(evaluations)
        report["detailed_report"] = self.generate_detailed_report(evaluations)
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
            "cross_device": [e["results"].get("cross_device_simulation", {}) for e in evaluations]
        }
    
    def generate_recommendations(self, evaluations: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on evaluation results."""
        recs = []
        
        # Language issues
        lang_issues = sum(len(p["results"]["language_quality"]["grammar_errors"]) for p in evaluations)
        if lang_issues > 0:
            recs.append(f"Address {lang_issues} language/grammar issues found in content")
        
        # Code issues
        code_issues = sum(len(p["results"]["code_quality"]["html"]["html_issues"]) for p in evaluations)
        if code_issues > 0:
            recs.append(f"Fix {code_issues} HTML/CSS code quality issues")
        
        # Cognitive load
        avg_cog_load = sum(p["results"]["ux_enhanced"]["cognitive_load"]["complexity_score"] for p in evaluations)/len(evaluations)
        if avg_cog_load > 50:
            recs.append("Simplify page layouts to reduce cognitive load")
        
        # First page specific checks
        first = evaluations[0]["results"]
        if first.get("alt_text", {}).get("missing", 0) > 0:
            recs.append("Add alt text to images.")
        if not first.get("responsive_design", {}).get("responsive", False):
            recs.append("Include a meta viewport tag for responsive design.")
        if not first.get("title_meta", {}).get("title_exists", False):
            recs.append("Add a proper title tag and meta description.")
        if not first.get("https", {}).get("https", False):
            recs.append("Ensure your site is served over HTTPS.")
        
        return recs
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        for page in self.evaluated_pages:
            if "page" in page:
                await page["page"].close() 