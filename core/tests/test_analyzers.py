import pytest
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from ..analyzers.accessibility_analyzer import AccessibilityAnalyzer
from ..analyzers.performance_analyzer import PerformanceAnalyzer
from ..analyzers.security_analyzer import SecurityAnalyzer
from ..analyzers.ux_analyzer import UXAnalyzer
from ..analyzers.code_analyzer import CodeAnalyzer
from ..analyzers.seo_analyzer import SEOAnalyzer

@pytest.fixture
async def browser():
    """Fixture for Playwright browser."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
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
        <style>
            .test { color: red; }
        </style>
    </head>
    <body>
        <h1>Test Page</h1>
        <p>This is a test page.</p>
        <img src="test.jpg" alt="Test Image">
        <form>
            <input type="text" name="test">
            <button type="submit">Submit</button>
        </form>
        <script>
            console.log("Test");
        </script>
    </body>
    </html>
    """

@pytest.mark.asyncio
async def test_accessibility_analyzer(browser, sample_html):
    """Test AccessibilityAnalyzer."""
    page = await browser.new_page()
    await page.set_content(sample_html)
    soup = BeautifulSoup(sample_html, "html.parser")
    
    analyzer = AccessibilityAnalyzer()
    results = await analyzer.analyze(page, soup)
    
    assert "wcag_compliance" in results
    assert "alt_text" in results
    assert "color_contrast" in results
    assert "keyboard_navigation" in results
    assert "semantic_html" in results
    assert "aria_labels" in results
    assert "form_accessibility" in results
    assert "media_accessibility" in results
    assert "overall_score" in results

@pytest.mark.asyncio
async def test_performance_analyzer(browser, sample_html):
    """Test PerformanceAnalyzer."""
    page = await browser.new_page()
    await page.set_content(sample_html)
    
    analyzer = PerformanceAnalyzer()
    results = await analyzer.analyze("http://test.com", page)
    
    assert "core_web_vitals" in results
    assert "resource_optimization" in results
    assert "caching" in results
    assert "rendering_performance" in results
    assert "network_performance" in results
    assert "mobile_performance" in results
    assert "overall_score" in results

@pytest.mark.asyncio
async def test_security_analyzer(browser, sample_html):
    """Test SecurityAnalyzer."""
    page = await browser.new_page()
    await page.set_content(sample_html)
    
    analyzer = SecurityAnalyzer()
    results = await analyzer.analyze("http://test.com", page)
    
    assert "headers" in results
    assert "content_security" in results
    assert "authentication" in results
    assert "input_validation" in results
    assert "data_protection" in results
    assert "api_security" in results
    assert "overall_score" in results

@pytest.mark.asyncio
async def test_ux_analyzer(browser, sample_html):
    """Test UXAnalyzer."""
    page = await browser.new_page()
    await page.set_content(sample_html)
    soup = BeautifulSoup(sample_html, "html.parser")
    
    analyzer = UXAnalyzer()
    results = await analyzer.analyze(page, soup)
    
    assert "navigation" in results
    assert "content_readability" in results
    assert "form_usability" in results
    assert "mobile_responsiveness" in results
    assert "interaction_design" in results
    assert "visual_hierarchy" in results
    assert "overall_score" in results

def test_code_analyzer(sample_html):
    """Test CodeAnalyzer."""
    soup = BeautifulSoup(sample_html, "html.parser")
    
    analyzer = CodeAnalyzer()
    results = analyzer.analyze(sample_html, soup)
    
    assert "html_quality" in results
    assert "css_quality" in results
    assert "javascript_quality" in results
    assert "code_optimization" in results
    assert "best_practices" in results
    assert "overall_score" in results

def test_seo_analyzer(sample_html):
    """Test SEOAnalyzer."""
    soup = BeautifulSoup(sample_html, "html.parser")
    
    analyzer = SEOAnalyzer()
    results = analyzer.analyze(soup)
    
    assert "meta_tags" in results
    assert "content_structure" in results
    assert "url_structure" in results
    assert "image_optimization" in results
    assert "mobile_friendliness" in results
    assert "technical_seo" in results
    assert "overall_score" in results

@pytest.mark.asyncio
async def test_analyzer_error_handling(browser):
    """Test error handling in analyzers."""
    page = await browser.new_page()
    
    # Test with invalid HTML
    invalid_html = "<invalid>html"
    soup = BeautifulSoup(invalid_html, "html.parser")
    
    # Test each analyzer
    analyzers = [
        (AccessibilityAnalyzer(), page, soup),
        (PerformanceAnalyzer(), "http://test.com", page),
        (SecurityAnalyzer(), "http://test.com", page),
        (UXAnalyzer(), page, soup),
        (CodeAnalyzer(), invalid_html, soup),
        (SEOAnalyzer(), soup)
    ]
    
    for analyzer, *args in analyzers:
        with pytest.raises(Exception):
            await analyzer.analyze(*args)

@pytest.mark.asyncio
async def test_analyzer_scores(browser, sample_html):
    """Test score calculation in analyzers."""
    page = await browser.new_page()
    await page.set_content(sample_html)
    soup = BeautifulSoup(sample_html, "html.parser")
    
    # Test each analyzer
    analyzers = [
        (AccessibilityAnalyzer(), page, soup),
        (PerformanceAnalyzer(), "http://test.com", page),
        (SecurityAnalyzer(), "http://test.com", page),
        (UXAnalyzer(), page, soup),
        (CodeAnalyzer(), sample_html, soup),
        (SEOAnalyzer(), soup)
    ]
    
    for analyzer, *args in analyzers:
        results = await analyzer.analyze(*args)
        assert "overall_score" in results
        assert 0 <= results["overall_score"] <= 100 