import pytest
import asyncio
import json
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from core.evaluators.page_evaluator import PageEvaluator
from core.evaluators.website_evaluator import WebsiteEvaluator
from core.utils.error_handler import ValidationError

@pytest.fixture(scope="session")
async def browser():
    """Fixture for Playwright browser - session scoped."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, timeout=30000)
        yield browser
        await browser.close()

@pytest.fixture
def sample_html():
    """Fixture for sample HTML content."""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Test Page</title>
    </head>
    <body>
        <h1>Test Page</h1>
        <p>This is a test page.</p>
        <img src="test.jpg" alt="Test Image">
        <form>
            <input type="text" name="test">
            <button type="submit">Submit</button>
        </form>
    </body>
    </html>
    """

@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_page_evaluator_validation(browser, sample_html):
    """Test PageEvaluator validation."""
    page = await browser.new_page()
    await page.set_content(sample_html)
    body_text = await page.inner_text("body")
    
    evaluator = PageEvaluator("http://test.com", sample_html, page, body_text)
    assert await evaluator.validate() is True
    
    # Test invalid URL
    evaluator.url = "invalid-url"
    assert await evaluator.validate() is False
    
    # Test invalid HTML
    evaluator.html = ""
    assert await evaluator.validate() is False
    
    await page.close()

@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_page_evaluator_evaluation(browser, sample_html):
    """Test PageEvaluator evaluation."""
    page = await browser.new_page()
    await page.set_content(sample_html)
    body_text = await page.inner_text("body")
    
    evaluator = PageEvaluator("http://test.com", sample_html, page, body_text)
    results_json = await evaluator.evaluate()
    print("\nPageEvaluator JSON Output:")
    print(results_json)
    results = json.loads(results_json)
    
    assert "url" in results
    assert "results" in results
    assert "design_data" in results
    
    # Check specific analysis results
    assert "accessibility" in results["results"]
    assert "performance" in results["results"]
    assert "security" in results["results"]
    assert "ux" in results["results"]
    assert "code_quality" in results["results"]
    assert "seo" in results["results"]
    
    await page.close()

@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_website_evaluator_validation(browser):
    """Test WebsiteEvaluator validation."""
    evaluator = WebsiteEvaluator("http://test.com")
    assert await evaluator.validate() is True
    
    # Test invalid URL
    evaluator.url = "invalid-url"
    assert await evaluator.validate() is False

@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_website_evaluator_crawl(browser, sample_html):
    """Test WebsiteEvaluator crawling."""
    evaluator = WebsiteEvaluator("http://test.com", max_subpages=5, max_depth=2)
    
    # Mock the fetch_page_html function
    async def mock_fetch(url):
        return sample_html
    
    evaluator._fetch_page_html = mock_fetch
    
    pages = await evaluator.crawl_all_subpages()
    assert len(pages) > 0
    assert "http://test.com" in pages

@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_website_evaluator_evaluation(browser, sample_html):
    """Test WebsiteEvaluator evaluation."""
    evaluator = WebsiteEvaluator("http://test.com")
    
    # Mock the crawl_all_subpages function
    async def mock_crawl():
        return ["http://test.com"]
    
    evaluator.crawl_all_subpages = mock_crawl
    
    # Mock the page evaluation
    async def mock_evaluate(*args, **kwargs):
        return json.dumps({
            "url": "http://test.com",
            "results": {
                "accessibility": {"score": 90},
                "performance": {"score": 85},
                "security": {"score": 95},
                "ux": {"score": 88},
                "code_quality": {"score": 92},
                "seo": {"score": 87}
            }
        })
    
    evaluator._evaluate_page = mock_evaluate
    
    report_json = await evaluator.evaluate(crawl=True)
    print("\nWebsiteEvaluator JSON Output:")
    print(report_json)
    report = json.loads(report_json)
    
    assert "homepage" in report or "url" in report
    assert "pages_evaluated" in report or "results" in report
    assert "aggregated_scores" in report or "results" in report
    assert "defect_details" in report or "results" in report
    assert "recommendations" in report or "results" in report

@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_error_handling(browser, sample_html):
    """Test error handling in evaluators."""
    page = await browser.new_page()
    await page.set_content(sample_html)
    body_text = await page.inner_text("body")
    
    evaluator = PageEvaluator("http://test.com", sample_html, page, body_text)
    
    # Test with invalid HTML
    evaluator.html = "<invalid>html"
    with pytest.raises(ValidationError):
        await evaluator.evaluate()
    
    # Test with invalid URL
    evaluator.url = "invalid-url"
    with pytest.raises(ValidationError):
        await evaluator.evaluate()
    
    await page.close()

@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_cleanup(browser, sample_html):
    """Test cleanup in evaluators."""
    page = await browser.new_page()
    await page.set_content(sample_html)
    body_text = await page.inner_text("body")
    
    evaluator = PageEvaluator("http://test.com", sample_html, page, body_text)
    await evaluator.cleanup()
    
    # Verify page is closed
    with pytest.raises(Exception):
        await page.content()