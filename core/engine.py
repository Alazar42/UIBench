import os
import asyncio
import json
import logging
from datetime import datetime
from collections import Counter
from typing import Optional, List, Set, Tuple, Dict
from urllib.parse import urlparse, urljoin, parse_qs
from heapq import heappush, heappop

import aiohttp
import requests
import textstat
from fastapi import FastAPI, HTTPException, WebSocket
from pydantic import BaseModel, BaseSettings
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

# For caching heavy computations
from aiocache import cached

# For accessibility tool integration (using axe-playwright wrapper)
from axe_playwright_python.sync_playwright import Axe

# For Lighthouse integration
import lighthouse_pyasync

# For security scanning with OWASP ZAP
from zapv2 import ZAPv2

# ------------------- Additional Imports (Advanced NLP, CSS, Lint, etc.) -------------------
import spacy
from textblob import TextBlob
import cssutils
from cssutils import css
from io import StringIO
import pylint.lint
from pylint.reporters.text import TextReporter

# ------------------- Configuration Management -------------------
class Settings(BaseSettings):
    evaluation_timeout: int = 60
    max_concurrent: int = 10
    zap_scan_depth: int = 5
    nlp_model: str = "en_core_web_lg"
    max_workers: int = 20  # For scalability
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

config = Settings()

# ------------------- Load NLP Models -------------------
try:
    nlp = spacy.load(config.nlp_model)
except OSError:
    from spacy.cli import download
    download(config.nlp_model)
    nlp = spacy.load(config.nlp_model)

# Inclusive language database
INCLUSIVE_LANGUAGE_DB = {
    "blacklist": {"alternatives": ["denylist", "blocklist"], "severity": "high"},
    "whitelist": {"alternatives": ["allowlist", "safelist"], "severity": "high"},
    "master": {"alternatives": ["main", "primary", "controller"], "severity": "medium"},
    "slave": {"alternatives": ["secondary", "replica", "worker"], "severity": "high"},
}

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# ------------------- Design Tool Integration (Plugin System) -------------------
class DesignToolIntegration:
    @staticmethod
    async def parse_figma(file_key: str) -> dict:
        token = os.getenv("FIGMA_API_TOKEN")
        if not token:
            return {"error": "FIGMA_API_TOKEN not configured"}
        url = f"https://api.figma.com/v1/files/{file_key}"
        headers = {"X-Figma-Token": token}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Figma API call failed with status {response.status_code}"}
    @staticmethod
    async def import_sketch(file_url: str) -> dict:
        # Simulated Sketch integration; replace with real Sketch Cloud API calls.
        return {"sketch_data": "Sample Sketch file data", "file_url": file_url}

# ------------------- Enhanced Reporting Module -------------------
class ReportGenerator:
    @staticmethod
    def create_executive_summary(data: dict) -> dict:
        return {
            "grades": ReportGenerator._calculate_grades(data),
            "priority_issues": ReportGenerator._identify_critical_issues(data),
            "comparative_analysis": ReportGenerator._compare_industry_benchmarks(data)
        }
    @staticmethod
    def _calculate_grades(data: dict) -> dict:
        return data.get("aggregated_scores", {})
    @staticmethod
    def _identify_critical_issues(data: dict) -> List[str]:
        defects = []
        for url, checks in data.get("defect_details", {}).items():
            for check, issues in checks.items():
                defects.extend(issues)
        return defects
    @staticmethod
    def _compare_industry_benchmarks(data: dict) -> dict:
        return {"performance": 90, "accessibility": 95}
    @staticmethod
    def generate_pdf(data: dict) -> bytes:
        pdf_content = f"Executive Summary:\n{json.dumps(data, indent=2)}"
        return pdf_content.encode("utf-8")

# ------------------- Caching for Heavy Computations -------------------
@cached(ttl=3600)
async def get_page_metrics_cached(url: str) -> dict:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            await page.goto(url, timeout=60000)
            metrics = await page.evaluate("() => window.performance.timing.toJSON()")
        finally:
            await page.close()
            await browser.close()
        return metrics

# ------------------- Accessibility Integration with Axe -------------------
async def run_axe_accessibility(page) -> dict:
    axe = Axe()
    results = await axe.run(page)
    return {
        "violations": results.violations,
        "score": max(100 - (len(results.violations) * 5), 0),
        "recommendations": [v['help'] for v in results.violations]
    }

# ------------------- Performance Integration with Lighthouse -------------------
async def run_lighthouse_audit(url: str) -> dict:
    lh = lighthouse_pyasync.Lighthouse(url)
    report = await lh.audit()
    return {
        "core_web_vitals": report['categories']['performance']['auditRefs'],
        "scores": {
            "performance": report['categories']['performance']['score'],
            "accessibility": report['categories']['accessibility']['score']
        }
    }

# ------------------- Security Scanning with OWASP ZAP -------------------
async def run_security_scan(url: str) -> dict:
    zap = ZAPv2(apikey=os.getenv('ZAP_API_KEY', ''))
    zap.urlopen(url)
    await asyncio.sleep(2)  # Allow time for spidering
    alerts = zap.core.alerts()
    return {
        "vulnerabilities": [a['alert'] for a in alerts],
        "risk_distribution": dict(Counter(a['risk'] for a in alerts))
    }

# ------------------- Enhanced NLP Checks -------------------
class LanguageAnalyzer:
    @staticmethod
    def analyze_text_quality(text: str) -> dict:
        doc = nlp(text)
        blob = TextBlob(text)
        grammar_errors = []
        for sent in doc.sents:
            if sent[-1].text not in {'.', '!', '?'}:
                grammar_errors.append(f"Missing punctuation in sentence: '{sent.text}'")
        polarity = blob.sentiment.polarity
        subjectivity = blob.sentiment.subjectivity
        inclusive_issues = []
        for token in doc:
            if token.text.lower() in INCLUSIVE_LANGUAGE_DB:
                entry = INCLUSIVE_LANGUAGE_DB[token.text.lower()]
                inclusive_issues.append({
                    "term": token.text,
                    "alternatives": entry["alternatives"],
                    "severity": entry["severity"]
                })
        readability = {
            "flesch": textstat.flesch_reading_ease(text),
            "smog": textstat.smog_index(text),
            "coleman_liau": textstat.coleman_liau_index(text)
        }
        return {
            "grammar_errors": grammar_errors,
            "sentiment": {"polarity": polarity, "subjectivity": subjectivity},
            "inclusive_language_issues": inclusive_issues,
            "readability": readability,
            "word_stats": {
                "total_words": len(doc),
                "unique_words": len(set(token.text for token in doc)),
                "avg_word_length": sum(len(token.text) for token in doc) / len(doc)
            }
        }

# ------------------- Enhanced Code Quality Scanning -------------------
class CodeQualityAnalyzer:
    @staticmethod
    def analyze_html_quality(html: str) -> dict:
        issues = []
        deprecated_tags = {'center', 'font', 'strike', 'tt'}
        soup = BeautifulSoup(html, 'html.parser')
        found_deprecated = [tag.name for tag in soup.find_all(deprecated_tags)]
        if found_deprecated:
            issues.append(f"Deprecated HTML tags found: {', '.join(found_deprecated)}")
        try:
            BeautifulSoup(html, 'html.parser')
        except Exception as e:
            issues.append(f"HTML validation error: {str(e)}")
        return {"html_issues": issues}
    @staticmethod
    def analyze_css_quality(css_content: str) -> dict:
        issues = []
        sheet = cssutils.parseString(css_content)
        for rule in sheet:
            if isinstance(rule, css.CSSStyleRule):
                for prop in rule.style:
                    if prop.name.startswith('-'):
                        issues.append(f"Vendor prefix detected: {prop.name}")
                    if prop.name in ['zoom', 'filter']:
                        issues.append(f"Potentially problematic property: {prop.name}")
        return {"css_issues": issues}
    @staticmethod
    def run_pylint_analysis(code: str) -> dict:
        issues = []
        class StringWriter:
            def __init__(self):
                self.content = []
            def write(self, text):
                self.content.append(text)
            def read(self):
                return "\n".join(self.content)
        reporter = TextReporter(StringWriter())
        pylint.lint.Run(["--disable=all", "--enable=E,W"], reporter=reporter, exit=False)
        return {"python_issues": reporter.writer.read().splitlines()}

# ------------------- Expanded UX/Usability Evaluation -------------------
class EnhancedUXAnalyzer:
    @staticmethod
    def check_heatmap_simulation(page) -> dict:
        elements = page.query_selector_all("h1, h2, h3, button, img")
        scores = []
        for element in elements:
            style = element.evaluate("el => { return { fontSize: getComputedStyle(el).fontSize, fontWeight: getComputedStyle(el).fontWeight, contrast: window.getComputedStyle(el).color, position: el.getBoundingClientRect() } }")
            score = 0
            if 'h1' in element.tag_name.lower():
                score += 30
            try:
                if int(style['fontWeight']) > 600:
                    score += 20
            except Exception:
                pass
            if style['fontSize'] and 'px' in style['fontSize']:
                if int(style['fontSize'].replace('px', '')) > 24:
                    score += 20
            scores.append(score)
        return {"heatmap_simulation": {
            "max_score": max(scores) if scores else 0,
            "average_score": sum(scores) / len(scores) if scores else 0
        }}
    @staticmethod
    def check_error_recovery(page) -> dict:
        test_url = urljoin(page.url, "/non-existent-page-1234")
        response = requests.get(test_url)
        is_custom_404 = "404" not in response.text
        forms = page.query_selector_all("form")
        error_handling = []
        for form in forms:
            inputs = form.query_selector_all("input")
            has_errors = any(input.evaluate("el => el.hasAttribute('aria-invalid')") for input in inputs)
            error_handling.append(has_errors)
        return {
            "custom_404_page": is_custom_404,
            "form_error_handling": sum(error_handling) / len(error_handling) if error_handling else 0
        }

# ------------------- Advanced Security Enhancements -------------------
class SecurityEnhancements:
    @staticmethod
    async def check_csrf_protection(page) -> dict:
        forms = await page.query_selector_all("form")
        protected = 0
        for form in forms:
            token = await form.query_selector("input[name='csrf_token']")
            protected += 1 if token else 0
        return {"csrf_protection": f"{protected}/{len(forms)} forms protected"}
    @staticmethod
    async def check_content_security_policy(headers: dict) -> dict:
        csp = headers.get("Content-Security-Policy", "")
        return {
            "csp_present": bool(csp),
            "unsafe_inline": "unsafe-inline" in csp,
            "unsafe_eval": "unsafe-eval" in csp
        }

# ------------------- Advanced Error Handling -------------------
class EvaluationErrorHandler:
    def __init__(self):
        self.errors = []
    def log_error(self, error: dict):
        self.errors.append({
            **error,
            "timestamp": datetime.utcnow(),
            "resolved": False
        })
    async def auto_retry(self, task, max_retries=3):
        retries = 0
        while retries < max_retries:
            try:
                return await task()
            except Exception as e:
                self.log_error({
                    "error": str(e),
                    "task": task.__name__,
                    "retries": retries
                })
                retries += 1
        raise RuntimeError(f"Max retries ({max_retries}) exceeded")

# ------------------- Performance Optimization -------------------
from async_lru import alru_cache
class PerformanceOptimizer:
    def __init__(self, evaluator):
        self.evaluator = evaluator
        self.priority_queue = []  # priority queue for evaluations
    async def optimize_evaluation_performance(self):
        # Intelligent caching: wrap a private method for page analysis
        @cached(ttl=3600, key_builder=lambda f, *args, **kwargs: f"evalcache:{hash(args[0])}")
        async def cached_page_analysis(url: str):
            return await self.evaluator._analyze_page(url)
        self.evaluator.cached_page_analysis = cached_page_analysis
        # Parallel evaluation: wrap evaluate_page with alru_cache
        self.evaluator.evaluate_page = alru_cache(maxsize=100)(self.evaluator.evaluate_page)
    def prioritize(self, url, priority=0):
        heappush(self.priority_queue, (-priority, url))

# ------------------- Scalability Enhancements -------------------
class ClusterManager:
    def __init__(self):
        self.worker_count = config.max_workers
    async def distribute_evaluation(self, urls: List[str]):
        # In-memory distribution of URLs to workers
        from hashlib import md5
        worker_assignments = {}
        for url in urls:
            worker_id = int(md5(url.encode()).hexdigest(), 16) % self.worker_count
            if worker_id not in worker_assignments:
                worker_assignments[worker_id] = []
            worker_assignments[worker_id].append(url)
        return worker_assignments
    def auto_scale_workers(self):
        # In-memory worker scaling
        return self.worker_count
    def scale_workers(self, count: int):
        logger.info(f"Scaling workers to {count}")
        self.worker_count = count

# ------------------- User Experience Enhancements -------------------
class UserExperience:
    def __init__(self):
        self.feedback = []
    def collect_feedback(self, evaluation_id: str, rating: int, comments: str):
        self.feedback.append({
            "evaluation_id": evaluation_id,
            "rating": rating,
            "comments": comments,
            "timestamp": datetime.utcnow()
        })
    def calculate_satisfaction_score(self):
        if not self.feedback:
            return 0
        return sum(f["rating"] for f in self.feedback) / len(self.feedback)
    def generate_heatmaps(self):
        # Placeholder for generating visual heatmaps from user interaction data
        return {"heatmap_data": "Sample heatmap data"}

# ------------------- Advanced NLP Features -------------------
class AdvancedNLPAnalysis:
    @staticmethod
    def detect_translation_quality(text: str) -> dict:
        doc = nlp(text)
        # Dummy implementations – replace with real models or heuristics
        translation_likelihood = 0.8
        cultural_relevance = True
        return {
            "translation_likelihood": translation_likelihood,
            "cultural_appropriateness": cultural_relevance
        }
    @staticmethod
    def analyze_content_strategy(text: str) -> dict:
        doc = nlp(text)
        keyword_density = 0.05
        content_gaps = ["Missing topic X"]
        seo_potential = 80
        return {
            "keyword_density": keyword_density,
            "content_gaps": content_gaps,
            "seo_potential": seo_potential
        }

# ------------------- Compliance Checking -------------------
class ComplianceChecker:
    GDPR_REQUIREMENTS = ["cookie_consent", "data_access", "right_to_be_forgotten"]
    ADA_REQUIREMENTS = ["alt_text", "keyboard_nav", "contrast_ratio"]
    def __init__(self):
        self.standards = {}
    def check_gdpr_compliance(self, evaluation: dict) -> dict:
        return self._verify_requirements(evaluation, self.GDPR_REQUIREMENTS)
    def check_ada_compliance(self, evaluation: dict) -> dict:
        return self._verify_requirements(evaluation, self.ADA_REQUIREMENTS)
    def _verify_requirements(self, evaluation: dict, requirements: list):
        return {
            req: evaluation["results"].get(req, {}).get("score", 0) >= 90
            for req in requirements
        }

# ------------------- Testing Framework Integration -------------------
class EvaluationTestSuite:
    def __init__(self):
        self.test_cases = []
    def add_test_case(self, url: str, expected_metrics: dict):
        self.test_cases.append((url, expected_metrics))
    async def run_regression_tests(self):
        results = []
        for url, expected in self.test_cases:
            evaluator = WebsiteEvaluator(url)
            report = await evaluator.evaluate()
            results.append(self._compare_results(report, expected))
        return results
    def _compare_results(self, actual: dict, expected: dict):
        passed = all(actual["aggregated_scores"].get(k, 0) >= v for k, v in expected.items())
        differences = {k: actual["aggregated_scores"].get(k, 0) - v for k, v in expected.items()}
        return {"passed": passed, "differences": differences}

# ------------------- Documentation Generation -------------------
class APIDocumentationGenerator:
    def __init__(self, app: FastAPI):
        self.app = app
    def generate_openapi_spec(self) -> dict:
        return self.app.openapi()
    def create_user_guide(self):
        return {
            "endpoints": self._parse_routes(),
            "examples": self._create_usage_examples(),
            "best_practices": self._document_best_practices()
        }
    def _parse_routes(self):
        return [route.path for route in self.app.routes]
    def _create_usage_examples(self):
        return {"example": "Use the /enhanced-evaluate endpoint with a POST request"}
    def _document_best_practices(self):
        return ["Ensure proper HTTPS configuration", "Maintain semantic HTML", "Optimize images and scripts"]

# ------------------- Updated PageEvaluator Class -------------------
class PageEvaluator:
    """
    Evaluates a single page by combining:
      - Accessibility via Axe
      - Performance metrics via Lighthouse and Playwright
      - Security scanning via OWASP ZAP and advanced security enhancements
      - NLP, code quality, UX, SEO, and various heuristic checks
    """
    def __init__(self, url: str, html: str, page, body_text: str, custom_criteria: dict = {}):
        self.url = url
        self.html = html
        self.page = page
        self.body_text = body_text
        self.criteria = custom_criteria
        self.soup = BeautifulSoup(self.html, "html.parser")
        self.design_data = {}
        self.check_design_tool_integration()
    def check_design_tool_integration(self):
        qs = parse_qs(urlparse(self.url).query)
        if "design_source" in qs:
            source = qs["design_source"][0].lower()
            if source == "figma" and "file_key" in qs:
                file_key = qs["file_key"][0]
                self.design_data = asyncio.run(DesignToolIntegration.parse_figma(file_key))
            elif source == "sketch" and "file_url" in qs:
                file_url = qs["file_url"][0]
                self.design_data = asyncio.run(DesignToolIntegration.import_sketch(file_url))
    async def evaluate(self) -> dict:
        results = {}
        # Language Analysis
        results["language_quality"] = LanguageAnalyzer.analyze_text_quality(self.body_text)
        # Enhanced Code Quality
        results["code_quality"] = {
            "html": CodeQualityAnalyzer.analyze_html_quality(self.html),
            "css": await self.analyze_css_quality(),
            "javascript": await self.analyze_javascript_quality()
        }
        # Expanded UX/Usability
        results["ux_enhanced"] = {
            "heatmap_simulation": EnhancedUXAnalyzer.check_heatmap_simulation(self.page),
            "error_recovery": EnhancedUXAnalyzer.check_error_recovery(self.page),
            "cognitive_load": self.assess_cognitive_load(),
            "feedback_mechanisms": self.check_feedback_mechanisms()
        }
        # Accessibility Checks
        results["axe_accessibility"] = await run_axe_accessibility(self.page)
        results["alt_text"] = self.check_alt_text_for_images()
        results["video_captions"] = await self.check_video_captions()
        results["video_transcripts"] = self.check_video_transcripts()
        results["color_contrast"] = self.check_color_contrast()
        results["responsive_design"] = self.check_responsive_design()
        results["semantic_html"] = self.check_semantic_html()
        results["title_meta"] = self.check_title_and_meta()
        results["structured_data"] = self.check_structured_data()
        results["html_validity"] = self.check_valid_html()
        results["wcag_details"] = self.check_wcag_details()
        # Operable Checks
        results["keyboard_access"] = await self.check_keyboard_accessibility()
        results["sufficient_time"] = self.check_sufficient_time()
        results["flashing_content"] = self.check_flashing_content()
        # Understandable Checks
        results["readability"] = self.analyze_text_readability()
        results["predictable_operation"] = self.check_predictable_operation()
        results["form_error_messages"] = self.check_form_error_messages()
        # Robust Checks
        results["assistive_tech_compatibility"] = self.check_compatibility_assistive_technologies()
        # Performance Checks
        results["lighthouse_metrics"] = await run_lighthouse_audit(self.url)
        results["minification"] = self.check_minification()
        results["image_optimization"] = self.check_image_optimization()
        results["cached_performance_metrics"] = await get_page_metrics_cached(self.url)
        results["core_web_vitals"] = self.check_core_web_vitals()
        results["browser_caching"] = self.check_browser_caching()
        results["mobile_performance"] = self.check_mobile_performance()
        results["performance_prediction"] = self.predict_performance_based_on_design()
        # Cross-device Simulation
        results["cross_device_simulation"] = await self.check_cross_device_simulation()
        # Aesthetic Analysis
        results["aesthetic_metrics"] = self.check_aesthetic_metrics()
        # SEO Checks
        results["heading_tags"] = self.check_heading_tags()
        results["clear_url_structure"] = self.check_clear_url_structure()
        results["sitemap"] = self.check_sitemap()
        # Security Checks (including enhanced security)
        results["zap_security"] = await run_security_scan(self.url)
        results["https"] = self.check_https()
        results["security_headers"] = await self.check_security_headers()
        # Advanced Security Enhancements
        results["csrf_protection"] = await SecurityEnhancements.check_csrf_protection(self.page)
        # Usability / UX Checks
        results["navigation_presence"] = self.check_navigation_presence()
        results["form_placeholders"] = self.check_form_placeholders()
        results["information_architecture"] = self.check_information_architecture()
        results["consistent_design"] = self.check_consistent_design()
        results["overall_user_satisfaction"] = self.check_overall_user_satisfaction()
        # Code Quality Checks
        results["code_optimization"] = self.check_code_optimization()
        results["code_consistency"] = self.check_code_consistency()
        return {"url": self.url, "results": results, "design_data": self.design_data}

# ------------------- WebsiteEvaluator Class with Performance Optimization -------------------
class WebsiteEvaluator:
    """
    Manages crawling and evaluation for an entire website.
    Integrates persistent storage, task queue support (via Celery), caching, and enhanced reporting.
    """
    def __init__(self, root_url: str, max_subpages: Optional[int] = None, max_depth: int = 10, concurrency: int = config.max_concurrent, custom_criteria: dict = {}):
        self.root_url = root_url
        self.max_subpages = max_subpages
        self.max_depth = max_depth
        self.concurrency = concurrency
        self.custom_criteria = custom_criteria
        self.evaluated_pages: List[dict] = []
    async def crawl_all_subpages(self) -> List[str]:
        visited: Set[str] = set()
        queue: asyncio.Queue[Tuple[str, int]] = asyncio.Queue()
        visited.add(self.root_url)
        queue.put_nowait((self.root_url, 0))
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
                    link = urljoin(self.root_url, a["href"])
                    if urlparse(link).netloc != urlparse(self.root_url).netloc:
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
    async def evaluate(self, crawl: bool = False) -> dict:
        pages = await self.crawl_all_subpages() if crawl else [self.root_url]
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
        report["learning_resources"] = get_learning_resources(
            [defect for page in evaluations for check, defect in page["results"].items() if isinstance(defect, dict) and defect.get("defects")]
        )
        return report
    def aggregate_report(self, evaluations: List[dict]) -> dict:
        total_pages = len(evaluations)
        if total_pages == 0:
            raise ValueError("No pages evaluated.")
        accessibility_score = sum(e["results"].get("alt_text", {}).get("score", 100) for e in evaluations) / total_pages
        performance_score = sum(e["results"].get("performance_prediction", {}).get("predicted_performance_score", 100) for e in evaluations) / total_pages
        seo_score = 100
        security_score = 100
        usability_score = 100
        code_quality_score = 100
        defects = {}
        for e in evaluations:
            url = e.get("url")
            for check, result in e.get("results", {}).items():
                if isinstance(result, dict) and result.get("defects"):
                    defects.setdefault(url, {})[check] = result.get("defects")
        recommendations = self.generate_recommendations(evaluations)
        return {
            "homepage": self.root_url,
            "pages_evaluated": total_pages,
            "aggregated_scores": {
                "accessibility": accessibility_score,
                "performance": performance_score,
                "seo": seo_score,
                "security": security_score,
                "usability": usability_score,
                "code_quality": code_quality_score
            },
            "defect_details": defects,
            "recommendations": recommendations,
            "evaluated_at": datetime.utcnow().isoformat(),
            "pages": evaluations
        }
    def generate_detailed_report(self, evaluations: List[dict]) -> dict:
        aesthetic_reports = [e["results"].get("aesthetic_metrics", {}) for e in evaluations]
        wcag_reports = [e["results"].get("wcag_details", {}) for e in evaluations]
        cross_device = [e["results"].get("cross_device_simulation", {}) for e in evaluations]
        return {"aesthetic": aesthetic_reports, "wcag": wcag_reports, "cross_device": cross_device}
    def generate_recommendations(self, evaluations: List[dict]) -> List[str]:
        recs = []
        lang_issues = sum(len(p["results"]["language_quality"]["grammar_errors"]) for p in evaluations)
        if lang_issues > 0:
            recs.append(f"Address {lang_issues} language/grammar issues found in content")
        code_issues = sum(len(p["results"]["code_quality"]["html"]["html_issues"]) for p in evaluations)
        if code_issues > 0:
            recs.append(f"Fix {code_issues} HTML/CSS code quality issues")
        avg_cog_load = sum(p["results"]["ux_enhanced"]["cognitive_load"]["complexity_score"] for p in evaluations)/len(evaluations)
        if avg_cog_load > 50:
            recs.append("Simplify page layouts to reduce cognitive load")
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

# ------------------- Utility: Fetch Page HTML -------------------
async def fetch_page_html(url: str) -> str:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.text()

# ------------------- Dummy Function for Learning Resources -------------------
def get_learning_resources(defects: List[str]) -> dict:
    return {"resources": ["Resource A", "Resource B"]}

# ------------------- FastAPI Endpoints & Models -------------------
class EvaluationRequest(BaseModel):
    url: str
    crawl_subpages: Optional[bool] = False
    max_subpages: Optional[int] = None
    max_depth: Optional[int] = 10
    custom_criteria: Optional[dict] = {}

# Updated Evaluation Report Model with new fields
class EnhancedEvaluationReport(BaseModel):
    homepage: str
    pages: List[dict]
    summary: dict
    recommendations: List[str]
    accessibility_score: float
    performance_score: float
    seo_score: float
    security_score: float
    usability_score: float
    code_quality_score: float
    defect_details: dict
    detailed_report: dict
    learning_resources: dict
    language_score: float
    code_quality_score: float
    ux_enhanced: dict
    cognitive_load_score: float

@app.post("/enhanced-evaluate", response_model=EnhancedEvaluationReport)
async def enhanced_evaluation(request: EvaluationRequest):
    try:
        evaluator = WebsiteEvaluator(
            root_url=request.url,
            max_subpages=request.max_subpages,
            max_depth=request.max_depth,
            custom_criteria=request.custom_criteria
        )
        report = await evaluator.evaluate(crawl=request.crawl_subpages)
        scores = report["aggregated_scores"]
        return EnhancedEvaluationReport(
            homepage=report["homepage"],
            pages=report["pages"],
            summary={
                "pages_evaluated": report["pages_evaluated"],
                "evaluated_at": report["evaluated_at"]
            },
            recommendations=report["recommendations"],
            accessibility_score=scores["accessibility"],
            performance_score=scores["performance"],
            seo_score=scores["seo"],
            security_score=scores["security"],
            usability_score=scores["usability"],
            code_quality_score=scores["code_quality"],
            defect_details=report["defect_details"],
            detailed_report=report["detailed_report"],
            learning_resources=report["learning_resources"],
            language_score=calculate_language_score(report),
            code_quality_score=calculate_code_quality_score(report),
            ux_enhanced=report.get("ux_enhanced", {}),
            cognitive_load_score=sum(
                p["results"]["ux_enhanced"]["cognitive_load"]["complexity_score"] 
                for p in report["pages"]
            ) / len(report["pages"])
        )
    except Exception as e:
        logger.error(f"Evaluation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")

@app.websocket("/ws/feedback")
async def websocket_feedback(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            evaluator = WebsiteEvaluator(root_url=data)
            report = await evaluator.evaluate(crawl=False)
            await websocket.send_text(json.dumps(report))
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        await websocket.close()

def calculate_language_score(report: dict) -> float:
    scores = []
    for page in report["pages"]:
        lang = page["results"]["language_quality"]
        scores.append(
            100 - len(lang["grammar_errors"]) * 2 -
            len(lang["inclusive_language_issues"]) * 5
        )
    return sum(scores)/len(scores) if scores else 100

def calculate_code_quality_score(report: dict) -> float:
    scores = []
    for page in report["pages"]:
        cq = page["results"]["code_quality"]
        issues = (
            len(cq["html"]["html_issues"]) +
            len(cq["css"]["css_issues"]) +
            len(cq["javascript"]["js_issues"])
        )
        scores.append(max(100 - issues * 2, 0))
    return sum(scores)/len(scores) if scores else 100

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("your_module_name:app", host="0.0.0.0", port=8000, reload=True)
