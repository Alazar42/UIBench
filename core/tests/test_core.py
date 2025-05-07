"""
Test suite for core functionality.
"""
import pytest
import pytest_asyncio
import asyncio
import json
from typing import Dict, Any
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, Page, Browser

# Import all analyzers
from core.analyzers.accessibility_analyzer import AccessibilityAnalyzer
from core.analyzers.code_analyzer import CodeAnalyzer
from core.analyzers.compliance_analyzer import ComplianceAnalyzer
from core.analyzers.design_system_analyzer import DesignSystemAnalyzer
from core.analyzers.infrastructure_analyzer import InfrastructureAnalyzer
from core.analyzers.nlp_content_analyzer import NLPContentAnalyzer
from core.analyzers.operational_metrics_analyzer import OperationalMetricsAnalyzer
from core.analyzers.performance_analyzer import PerformanceAnalyzer
from core.analyzers.security_analyzer import SecurityAnalyzer
from core.analyzers.seo_analyzer import SEOAnalyzer
from core.analyzers.ux_analyzer import UXAnalyzer
from core.analyzers.mutation_analyzer import MutationAnalyzer
from core.analyzers.contract_analyzer import ContractAnalyzer
from core.analyzers.fuzz_analyzer import FuzzAnalyzer

# Import evaluators
from core.evaluators.website_evaluator import WebsiteEvaluator
from core.evaluators.page_evaluator import PageEvaluator

from core.utils.error_handler import AnalysisError

@pytest.fixture
def test_url() -> str:
    """Test URL fixture."""
    return "https://www.cursor.com/"

@pytest_asyncio.fixture
async def browser() -> Browser:
    """Playwright browser fixture."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        yield browser
        await browser.close()

@pytest_asyncio.fixture
async def test_page(browser: Browser) -> Page:
    """Playwright page fixture."""
    page = await browser.new_page()
    yield page
    await page.close()

@pytest_asyncio.fixture
async def test_html(test_page: Page, test_url: str) -> str:
    """Get HTML content from the test URL."""
    await test_page.goto(test_url)
    return await test_page.content()

@pytest_asyncio.fixture
async def test_soup(test_html: str) -> BeautifulSoup:
    """BeautifulSoup fixture."""
    return BeautifulSoup(test_html, 'html.parser')

@pytest_asyncio.fixture
async def test_text(test_soup: BeautifulSoup) -> str:
    """Extract text content from the page."""
    return test_soup.get_text(separator=' ', strip=True)

@pytest.fixture
def website_evaluator(test_url: str) -> WebsiteEvaluator:
    """WebsiteEvaluator fixture."""
    return WebsiteEvaluator(root_url=test_url)

# Analyzer Tests
@pytest.mark.asyncio
async def test_accessibility_analysis(test_url: str, test_page: Page, test_html: str, test_soup: BeautifulSoup):
    """Test accessibility analysis."""
    analyzer = AccessibilityAnalyzer()
    try:
        results_json = await analyzer.analyze(test_url, test_html, test_soup)
        results = json.loads(results_json)
        assert "results" in results
        assert "json_path" in results
        assert "overall_score" in results["results"]
        assert "issues" in results["results"]
        assert "recommendations" in results["results"]
        assert "metrics" in results["results"]
    except Exception as e:
        pytest.fail(f"Accessibility analysis failed: {str(e)}")

@pytest.mark.asyncio
async def test_code_analysis(test_url: str, test_html: str, test_soup: BeautifulSoup):
    """Test code analysis."""
    analyzer = CodeAnalyzer()
    try:
        results_json = await analyzer.analyze(test_url, test_html, test_soup)
        results = json.loads(results_json)
        assert "results" in results
        assert "json_path" in results
        assert "overall_score" in results["results"]
        assert "issues" in results["results"]
        assert "recommendations" in results["results"]
        assert "metrics" in results["results"]
    except Exception as e:
        pytest.fail(f"Code analysis failed: {str(e)}")

@pytest.mark.asyncio
async def test_compliance_analysis(test_url: str, test_page: Page):
    """Test compliance analysis."""
    analyzer = ComplianceAnalyzer()
    try:
        await test_page.goto(test_url)
        results_json = await analyzer.analyze(test_url, test_page)
        results = json.loads(results_json)
        assert "results" in results
        assert "json_path" in results
        assert "overall_score" in results["results"]
        assert "issues" in results["results"]
        assert "recommendations" in results["results"]
        assert "metrics" in results["results"]
    except Exception as e:
        pytest.fail(f"Compliance analysis failed: {str(e)}")

@pytest.mark.asyncio
async def test_design_system_analysis(test_url: str, test_page: Page, test_soup: BeautifulSoup):
    """Test design system analysis."""
    analyzer = DesignSystemAnalyzer()
    try:
        await test_page.goto(test_url)
        results_json = await analyzer.analyze(test_url, test_page, test_soup)
        results = json.loads(results_json)
        assert "results" in results
        assert "json_path" in results
        assert "overall_score" in results["results"]
        assert "issues" in results["results"]
        assert "recommendations" in results["results"]
    except Exception as e:
        pytest.fail(f"Design system analysis failed: {str(e)}")

@pytest.mark.asyncio
async def test_infrastructure_analysis(test_url: str, test_page: Page):
    """Test infrastructure analysis."""
    analyzer = InfrastructureAnalyzer()
    try:
        await test_page.goto(test_url)
        results_json = await analyzer.analyze(test_url, test_page)
        results = json.loads(results_json)
        assert "results" in results
        assert "json_path" in results
        assert "overall_score" in results["results"]
        assert "issues" in results["results"]
        assert "recommendations" in results["results"]
    except Exception as e:
        pytest.fail(f"Infrastructure analysis failed: {str(e)}")

@pytest.mark.asyncio
async def test_nlp_analysis(test_url: str, test_text: str):
    """Test NLP content analysis."""
    analyzer = NLPContentAnalyzer()
    try:
        results_json = await analyzer.analyze(test_url, test_text)
        results = json.loads(results_json)
        assert "results" in results
        assert "json_path" in results
        assert "overall_score" in results["results"]
        assert "issues" in results["results"]
        assert "recommendations" in results["results"]
        assert "metrics" in results["results"]
    except Exception as e:
        pytest.fail(f"NLP analysis failed: {str(e)}")

@pytest.mark.asyncio
async def test_operational_metrics_analysis(test_url: str, test_page: Page):
    """Test operational metrics analysis."""
    analyzer = OperationalMetricsAnalyzer()
    try:
        await test_page.goto(test_url)
        results_json = await analyzer.analyze(test_url, test_page)
        results = json.loads(results_json)
        assert "results" in results
        assert "json_path" in results
        assert "overall_score" in results["results"]
        assert "issues" in results["results"]
        assert "recommendations" in results["results"]
    except Exception as e:
        pytest.fail(f"Operational metrics analysis failed: {str(e)}")

@pytest.mark.asyncio
async def test_performance_analysis(test_url: str, test_page: Page, test_soup: BeautifulSoup):
    """Test performance analysis."""
    analyzer = PerformanceAnalyzer()
    try:
        await test_page.goto(test_url)
        results_json = await analyzer.analyze(test_url, test_page, test_soup)
        results = json.loads(results_json)
        assert "results" in results
        assert "json_path" in results
        assert "overall_score" in results["results"]
        assert "issues" in results["results"]
        assert "recommendations" in results["results"]
        assert "metrics" in results["results"]
    except Exception as e:
        pytest.fail(f"Performance analysis failed: {str(e)}")

@pytest.mark.asyncio
async def test_security_analysis(test_url: str, test_page: Page):
    """Test security analysis."""
    analyzer = SecurityAnalyzer()
    try:
        await test_page.goto(test_url)
        html = await test_page.content()
        soup = BeautifulSoup(html, "html.parser")
        results_json = await analyzer.analyze(test_url, test_page, soup)
        results = json.loads(results_json)
        assert "results" in results
        assert "json_path" in results
        assert "overall_score" in results["results"]
        assert "issues" in results["results"]
        assert "recommendations" in results["results"]
        assert "metrics" in results["results"]
    except Exception as e:
        pytest.fail(f"Security analysis failed: {str(e)}")

@pytest.mark.asyncio
async def test_seo_analysis(test_url: str, test_soup: BeautifulSoup):
    """Test SEO analysis."""
    analyzer = SEOAnalyzer()
    try:
        results_json = await analyzer.analyze(test_url, test_soup)
        results = json.loads(results_json)
        assert "results" in results
        assert "json_path" in results
        assert "overall_score" in results["results"]
        assert "issues" in results["results"]
        assert "recommendations" in results["results"]
        assert "metrics" in results["results"]
    except Exception as e:
        pytest.fail(f"SEO analysis failed: {str(e)}")

@pytest.mark.asyncio
async def test_ux_analysis(test_url: str, test_page: Page, test_soup: BeautifulSoup):
    """Test UX analysis."""
    analyzer = UXAnalyzer()
    try:
        await test_page.goto(test_url)
        results_json = await analyzer.analyze(test_url, test_page, test_soup)
        results = json.loads(results_json)
        assert "results" in results
        assert "json_path" in results
        assert "overall_score" in results["results"]
        assert "issues" in results["results"]
        assert "recommendations" in results["results"]
    except Exception as e:
        pytest.fail(f"UX analysis failed: {str(e)}")

@pytest.mark.asyncio
async def test_mutation_analysis(test_url: str, test_page: Page, test_html: str):
    """Test mutation testing analysis."""
    analyzer = MutationAnalyzer()
    try:
        await test_page.goto(test_url)
        results_json = await analyzer.analyze(test_url, test_page, test_html)
        results = json.loads(results_json)
        assert "results" in results
        assert "json_path" in results
        assert "overall_score" in results["results"]
        assert "mutations" in results["results"]
        assert "killed" in results["results"]
        assert "survived" in results["results"]
        assert "metrics" in results["results"]
    except Exception as e:
        pytest.fail(f"Mutation analysis failed: {str(e)}")

@pytest.mark.asyncio
async def test_contract_analysis(test_url: str, test_page: Page):
    """Test contract testing analysis."""
    analyzer = ContractAnalyzer()
    try:
        await test_page.goto(test_url)
        results_json = await analyzer.analyze(test_url, test_page)
        results = json.loads(results_json)
        assert "results" in results
        assert "json_path" in results
        assert "overall_score" in results["results"]
        assert "interactions" in results["results"]
        assert "passed" in results["results"]
        assert "failed" in results["results"]
        assert "metrics" in results["results"]
    except Exception as e:
        pytest.fail(f"Contract analysis failed: {str(e)}")

@pytest.mark.asyncio
async def test_fuzz_analysis(test_url: str, test_page: Page):
    """Test fuzz testing analysis."""
    analyzer = FuzzAnalyzer()
    try:
        await test_page.goto(test_url)
        results_json = await analyzer.analyze(test_url, test_page)
        results = json.loads(results_json)
        assert "results" in results
        assert "json_path" in results
        assert "overall_score" in results["results"]
        assert "executions" in results["results"]
        assert "crashes" in results["results"]
        assert "coverage" in results["results"]
        assert "metrics" in results["results"]
    except Exception as e:
        pytest.fail(f"Fuzz analysis failed: {str(e)}")

# Evaluator Tests
@pytest.mark.asyncio
async def test_website_evaluator(website_evaluator: WebsiteEvaluator):
    """Test website evaluation."""
    try:
        results_json = await website_evaluator.evaluate()
        results = json.loads(results_json)
        assert "detailed_report" in results
        assert "overall_score" in results
        assert "analyzer_scores" in results
    except Exception as e:
        pytest.fail(f"Website evaluation failed: {str(e)}")

@pytest.mark.asyncio
async def test_page_evaluator(test_url: str, test_page: Page, test_html: str, test_soup: BeautifulSoup, test_text: str):
    """Test PageEvaluator."""
    evaluator = PageEvaluator(url=test_url, html=test_html, page=test_page, body_text=test_text)
    try:
        await test_page.goto(test_url)
        results_json = await evaluator.evaluate()
        results = json.loads(results_json)
        assert "url" in results
        assert "results" in results
        assert "design_data" in results
        assert "performance_metrics" in results
    except Exception as e:
        pytest.fail(f"PageEvaluator test failed: {str(e)}")
    finally:
        await evaluator.cleanup()