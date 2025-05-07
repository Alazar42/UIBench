import os
import sys
import pytest
import asyncio
import json
import socket
import http.server
import threading
import time
from pathlib import Path
from datetime import datetime
from bs4 import BeautifulSoup
from playwright.async_api import Page, async_playwright
from core.evaluators.page_evaluator import PageEvaluator
import logging
from core.analyzers.accessibility_analyzer import AccessibilityAnalyzer
from core.analyzers.code_analyzer import CodeAnalyzer
from core.analyzers.compliance_analyzer import ComplianceAnalyzer
from core.analyzers.infrastructure_analyzer import InfrastructureAnalyzer
from core.analyzers.design_system_analyzer import DesignSystemAnalyzer
from core.analyzers.nlp_content_analyzer import NLPContentAnalyzer
from core.analyzers.operational_metrics_analyzer import OperationalMetricsAnalyzer
from core.analyzers.performance_analyzer import PerformanceAnalyzer
from core.analyzers.security_analyzer import SecurityAnalyzer
from core.analyzers.seo_analyzer import SEOAnalyzer
from core.analyzers.ux_analyzer import UXAnalyzer
from core.analyzers.mutation_analyzer import MutationAnalyzer
from core.analyzers.contract_analyzer import ContractAnalyzer
from core.analyzers.fuzz_analyzer import FuzzAnalyzer



# Add the core directory to the Python path
core_dir = str(Path(__file__).parent.parent)
if core_dir not in sys.path:
    sys.path.insert(0, core_dir)

# Set up the root directory for analysis results
root_dir = str(Path(__file__).parent.parent.parent)
results_dir = os.path.join(root_dir, "analysis_results")

def find_available_port(start_port: int = 3000, max_attempts: int = 100) -> int:
    """Find an available port starting from start_port."""
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', port))
                return port
        except OSError:
            continue
    raise RuntimeError(f"Could not find an available port after {max_attempts} attempts")

def wait_for_server(port: int, timeout: int = 5) -> bool:
    """Wait for the server to be ready."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect(('localhost', port))
                return True
        except (ConnectionRefusedError, OSError):
            time.sleep(0.1)
    return False

class StaticFileHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(Path(__file__).parent.parent.parent), **kwargs)
    
    def log_message(self, format, *args):
        """Override to suppress logging"""
        pass

class HTTPServer:
    def __init__(self, port: int):
        self.port = port
        self.server = None
        self.thread = None
    
    def start(self):
        """Start the server in a separate thread."""
        self.server = http.server.HTTPServer(('localhost', self.port), StaticFileHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        
        if not wait_for_server(self.port):
            self.stop()
            raise RuntimeError("Server failed to start")
    
    def stop(self):
        """Stop the server."""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            self.server = None
            self.thread = None

@pytest.fixture(scope="session")
def test_port():
    """Get an available port for testing."""
    return find_available_port()

@pytest.fixture(scope="session")
def http_server(test_port):
    """Create and manage the HTTP server."""
    server = HTTPServer(test_port)
    server.start()
    yield server
    server.stop()

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def browser():
    """Create a browser instance for the test session."""
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        yield browser
        await browser.close()

@pytest.fixture(scope="function")
async def page(browser):
    """Create a new page for each test."""
    page = await browser.new_page()
    try:
        yield page
    finally:
        try:
            await page.close()
        except Exception as e:
            logger.warning(f"Error closing page: {str(e)}")

@pytest.fixture(scope="function")
def project_path():
    return "/home/jared/Documents/UIBench_code_backup/frontend"

@pytest.fixture(scope="function")
def analysis_results_dir():
    dir_path = Path(results_dir)
    dir_path.mkdir(exist_ok=True)
    return dir_path

@pytest.fixture(scope="function")
async def html(page: Page, project_path: str, test_port: int, http_server) -> str:
    """Load the HTML content and set it in the page"""
    app_path = Path(project_path) / "src" / "app.html"
    if not app_path.is_file():
        raise FileNotFoundError(f"app.html not found at {app_path}")
    raw = app_path.read_text(encoding="utf-8")
    
    # Use the local HTTP server
    relative_path = app_path.relative_to(Path(__file__).parent.parent.parent)
    test_url = f"http://localhost:{test_port}/{relative_path}"
    
    # Add retry logic for page loading
    max_retries = 3
    for attempt in range(max_retries):
        try:
            await page.goto(test_url)
            await page.wait_for_load_state("networkidle")
            rendered_html = await page.content()
            return rendered_html
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(1)  # Wait before retrying

@pytest.fixture(scope="function")
def soup(html: str) -> BeautifulSoup:
    """Create and return a BeautifulSoup object from the HTML content"""
    return BeautifulSoup(html, "html.parser")

@pytest.fixture(scope="function")
async def body_text(page: Page) -> str:
    """Get the body text directly from the page"""
    return await page.inner_text("body")

def save_results(analyzer_name: str, data: dict, project_path: str, analysis_results_dir: Path) -> str:
    """Helper method to save results to JSON file in the correct format.
    
    Args:
        analyzer_name: Name of the analyzer (e.g., 'accessibility', 'security')
        data: Analysis results data
        project_path: Path to the project being analyzed
        analysis_results_dir: Directory to save results in
        
    Returns:
        str: Path to the saved results file
    """
    project_name = os.path.basename(project_path)
    
    # Create a single file per analyzer without timestamp
    filename = f"{analyzer_name}_{project_name}.json"
    filepath = analysis_results_dir / filename
    
    # Ensure the directory exists
    analysis_results_dir.mkdir(parents=True, exist_ok=True)
    
    # Extract URL from results if available
    url = data.get("url", "unknown_url")
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Prepare the new result entry
    new_result = {
        "timestamp": current_time,
        "url": url,
        "data": data
    }
    
    # Initialize or load existing results
    if filepath.exists():
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                output = json.load(f)
                # Ensure results is a list
                if "results" not in output:
                    output["results"] = []
                # Append new result
                output["results"].append(new_result)
                # Update last_updated timestamp
                output["metadata"]["last_updated"] = current_time
        except json.JSONDecodeError:
            # If file is corrupted, start fresh
            output = {
                "metadata": {
                    "analyzer": analyzer_name,
                    "project_path": project_path,
                    "created": current_time,
                    "last_updated": current_time,
                    "version": "1.0.0"
                },
                "results": [new_result]
            }
    else:
        # Create new file with initial result
        output = {
            "metadata": {
                "analyzer": analyzer_name,
                "project_path": project_path,
                "created": current_time,
                "last_updated": current_time,
                "version": "1.0.0"
            },
            "results": [new_result]
        }
    
    # Write the file
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    return str(filepath)

@pytest.fixture
async def browser_manager():
    """Create a browser manager instance."""
    manager = await BrowserManager.get_instance()
    yield manager
    await manager.close_all()

@pytest.fixture
def analysis_cache():
    """Create an analysis cache instance."""
    return AnalysisCache()

@pytest.fixture
def sample_html():
    """Return a sample HTML page for testing."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Page</title>
        <style>
            .test-class { color: blue; }
        </style>
    </head>
    <body>
        <h1>Test Page</h1>
        <form id="test-form">
            <input type="text" id="test-input" name="test-input">
            <button type="submit">Submit</button>
        </form>
        <div id="test-div" class="test-class">
            <p>Test content</p>
        </div>
        <script>
            document.getElementById('test-form').addEventListener('submit', function(e) {
                e.preventDefault();
                console.log('Form submitted');
            });
        </script>
    </body>
    </html>
    """

@pytest.mark.asyncio
class TestOfflineEvaluation:
    """Test suite for offline project evaluation"""
    
    async def _create_evaluator(self, project_path: str, page: Page, html: str, body_text: str, test_port: int) -> PageEvaluator:
        """Helper method to create a PageEvaluator instance with proper setup"""
        app_path = Path(project_path) / "src" / "app.html"
        relative_path = app_path.relative_to(Path(__file__).parent.parent.parent)
        url = f"http://localhost:{test_port}/{relative_path}"
        
        # Ensure page is ready
        if not page.url:
            await page.goto(url)
            await page.wait_for_load_state("networkidle")
        
        return PageEvaluator(
            url=url,
            html=html,
            page=page,
            body_text=body_text
        )
    
    async def test_accessibility_analysis(self, project_path: str, page: Page, html: str, soup: BeautifulSoup, 
                                        body_text: str, analysis_results_dir: Path, test_port: int):
        evaluator = await self._create_evaluator(project_path, page, html, body_text, test_port)
        analyzer = AccessibilityAnalyzer()
        results_json = await analyzer.analyze(evaluator.url, html, soup)
        results = json.loads(results_json)
        results["url"] = evaluator.url
        save_results('accessibility', results, project_path, analysis_results_dir)
        assert "results" in results
        assert "json_path" in results
        assert "overall_score" in results["results"]
        assert "issues" in results["results"]
        assert "recommendations" in results["results"]
        assert "metrics" in results["results"]

    async def test_code_analysis(self, project_path: str, page: Page, html: str, soup: BeautifulSoup, 
                               body_text: str, analysis_results_dir: Path, test_port: int):
        evaluator = await self._create_evaluator(project_path, page, html, body_text, test_port)
        analyzer = CodeAnalyzer()
        results_json = await analyzer.analyze(evaluator.url, html, soup)
        results = json.loads(results_json)
        results["url"] = evaluator.url
        save_results('code', results, project_path, analysis_results_dir)
        assert "results" in results
        assert "json_path" in results
        assert "overall_score" in results["results"]
        assert "issues" in results["results"]
        assert "recommendations" in results["results"]
        assert "metrics" in results["results"]

    async def test_compliance_analysis(self, project_path: str, page: Page, html: str, soup: BeautifulSoup, 
                                     body_text: str, analysis_results_dir: Path, test_port: int):
        evaluator = await self._create_evaluator(project_path, page, html, body_text, test_port)
        analyzer = ComplianceAnalyzer()
        results_json = await analyzer.analyze(evaluator.url, page)
        results = json.loads(results_json)
        results["url"] = evaluator.url
        save_results('compliance', results, project_path, analysis_results_dir)
        assert "results" in results
        assert "json_path" in results
        assert "overall_score" in results["results"]
        assert "issues" in results["results"]
        assert "recommendations" in results["results"]
        assert "metrics" in results["results"]

    async def test_infrastructure_analysis(self, project_path: str, page: Page, html: str, soup: BeautifulSoup, 
                                         body_text: str, analysis_results_dir: Path, test_port: int):
        evaluator = await self._create_evaluator(project_path, page, html, body_text, test_port)
        analyzer = InfrastructureAnalyzer()
        results_json = await analyzer.analyze(evaluator.url, page)
        results = json.loads(results_json)
        results["url"] = evaluator.url
        save_results('infrastructure', results, project_path, analysis_results_dir)
        assert "results" in results
        assert "json_path" in results
        assert "overall_score" in results["results"]
        assert "issues" in results["results"]
        assert "recommendations" in results["results"]

    async def test_design_system_analysis(self, project_path: str, page: Page, html: str, soup: BeautifulSoup, 
                                        body_text: str, analysis_results_dir: Path, test_port: int):
        """Test design system analysis"""
        evaluator = await self._create_evaluator(project_path, page, html, body_text, test_port)
        analyzer = DesignSystemAnalyzer()
        results_json = await analyzer.analyze(evaluator.url, page, soup)
        results = json.loads(results_json)
        results["url"] = evaluator.url
        save_results('design', results, project_path, analysis_results_dir)
        assert "results" in results
        assert "json_path" in results
        assert "overall_score" in results["results"]
        assert "issues" in results["results"]
        assert "recommendations" in results["results"]

    async def test_nlp_analysis(self, project_path: str, page: Page, html: str, soup: BeautifulSoup, 
                              body_text: str, analysis_results_dir: Path, test_port: int):
        """Test NLP content analysis"""
        evaluator = await self._create_evaluator(project_path, page, html, body_text, test_port)
        analyzer = NLPContentAnalyzer()
        results_json = await analyzer.analyze(evaluator.url, body_text)
        results = json.loads(results_json)
        results["url"] = evaluator.url
        save_results('nlp_content', results, project_path, analysis_results_dir)
        assert "results" in results
        assert "json_path" in results
        assert "overall_score" in results["results"]
        assert "issues" in results["results"]
        assert "recommendations" in results["results"]
        assert "metrics" in results["results"]

    async def test_operational_metrics_analysis(self, project_path: str, page: Page, html: str, soup: BeautifulSoup, 
                                              body_text: str, analysis_results_dir: Path, test_port: int):
        """Test operational metrics analysis"""
        evaluator = await self._create_evaluator(project_path, page, html, body_text, test_port)
        analyzer = OperationalMetricsAnalyzer()
        results_json = await analyzer.analyze(evaluator.url, page)
        results = json.loads(results_json)
        results["url"] = evaluator.url
        save_results('operational_metrics', results, project_path, analysis_results_dir)
        assert "results" in results
        assert "json_path" in results
        assert "overall_score" in results["results"]
        assert "issues" in results["results"]
        assert "recommendations" in results["results"]

    async def test_performance_analysis(self, project_path: str, page: Page, html: str, soup: BeautifulSoup, 
                                      body_text: str, analysis_results_dir: Path, test_port: int):
        evaluator = await self._create_evaluator(project_path, page, html, body_text, test_port)
        analyzer = PerformanceAnalyzer()
        results_json = await analyzer.analyze(evaluator.url, page, soup)
        results = json.loads(results_json)
        results["url"] = evaluator.url
        save_results('performance', results, project_path, analysis_results_dir)
        assert "results" in results
        assert "json_path" in results
        assert "overall_score" in results["results"]
        assert "issues" in results["results"]
        assert "recommendations" in results["results"]

    async def test_security_analysis(self, project_path: str, page: Page, html: str, soup: BeautifulSoup, 
                                   body_text: str, analysis_results_dir: Path, test_port: int):
        """Test security analysis"""
        evaluator = await self._create_evaluator(project_path, page, html, body_text, test_port)
        analyzer = SecurityAnalyzer()
        results_json = await analyzer.analyze(evaluator.url, page, soup)
        results = json.loads(results_json)
        results["url"] = evaluator.url
        save_results('security', results, project_path, analysis_results_dir)
        assert "results" in results
        assert "json_path" in results
        assert "overall_score" in results["results"]
        assert "issues" in results["results"]
        assert "recommendations" in results["results"]
        assert "metrics" in results["results"]

    async def test_seo_analysis(self, project_path: str, page: Page, html: str, soup: BeautifulSoup, 
                              body_text: str, analysis_results_dir: Path, test_port: int):
        evaluator = await self._create_evaluator(project_path, page, html, body_text, test_port)
        analyzer = SEOAnalyzer()
        results_json = await analyzer.analyze(evaluator.url, soup)
        results = json.loads(results_json)
        results["url"] = evaluator.url
        save_results('seo', results, project_path, analysis_results_dir)
        assert "results" in results
        assert "json_path" in results
        assert "overall_score" in results["results"]
        assert "issues" in results["results"]
        assert "recommendations" in results["results"]
        assert "metrics" in results["results"]

    async def test_ux_analysis(self, project_path: str, page: Page, html: str, soup: BeautifulSoup, 
                             body_text: str, analysis_results_dir: Path, test_port: int):
        evaluator = await self._create_evaluator(project_path, page, html, body_text, test_port)
        analyzer = UXAnalyzer()
        results_json = await analyzer.analyze(evaluator.url, page, soup)
        results = json.loads(results_json)
        results["url"] = evaluator.url
        save_results('ux', results, project_path, analysis_results_dir)
        assert "results" in results
        assert "json_path" in results
        assert "overall_score" in results["results"]
        assert "issues" in results["results"]
        assert "recommendations" in results["results"]
        assert "metrics" in results["results"]

    async def test_mutation_analysis(self, project_path: str, page: Page, html: str, soup: BeautifulSoup, 
                                   body_text: str, analysis_results_dir: Path, test_port: int):
        """Test mutation testing analysis"""
        evaluator = await self._create_evaluator(project_path, page, html, body_text, test_port)
        analyzer = MutationAnalyzer()
        results_json = await analyzer.analyze(evaluator.url, page, html)
        results = json.loads(results_json)
        results["url"] = evaluator.url
        save_results('mutation', results, project_path, analysis_results_dir)
        assert "results" in results
        assert "json_path" in results
        assert "overall_score" in results["results"]
        assert "mutations" in results["results"]
        assert "metrics" in results["results"]

    async def test_contract_analysis(self, project_path: str, page: Page, html: str, soup: BeautifulSoup, 
                                   body_text: str, analysis_results_dir: Path, test_port: int):
        """Test contract testing analysis"""
        evaluator = await self._create_evaluator(project_path, page, html, body_text, test_port)
        analyzer = ContractAnalyzer()
        results_json = await analyzer.analyze(evaluator.url, page)
        results = json.loads(results_json)
        results["url"] = evaluator.url
        save_results('contract', results, project_path, analysis_results_dir)
        assert "results" in results
        assert "json_path" in results
        assert "overall_score" in results["results"]
        assert "interactions" in results["results"]
        assert "metrics" in results["results"]

    async def test_fuzz_analysis(self, project_path: str, page: Page, html: str, soup: BeautifulSoup, 
                               body_text: str, analysis_results_dir: Path, test_port: int):
        """Test fuzz testing analysis"""
        evaluator = await self._create_evaluator(project_path, page, html, body_text, test_port)
        analyzer = FuzzAnalyzer()
        results_json = await analyzer.analyze(evaluator.url, page)
        results = json.loads(results_json)
        results["url"] = evaluator.url
        save_results('fuzz', results, project_path, analysis_results_dir)
        assert "results" in results
        assert "json_path" in results
        assert "overall_score" in results["results"]
        assert "crashes" in results["results"]
        assert "metrics" in results["results"]
    
    async def test_website_evaluator(self, project_path: str, page: Page, html: str, soup: BeautifulSoup, 
                                   body_text: str, analysis_results_dir: Path, test_port: int):
        """Test website evaluation"""
        evaluator = await self._create_evaluator(project_path, page, html, body_text, test_port)
        results_json = await evaluator.evaluate()
        results = json.loads(results_json)
        results["url"] = evaluator.url
        save_results('website', results, project_path, analysis_results_dir)
        assert "url" in results
        assert "results" in results
        assert "design_data" in results
        assert "performance_metrics" in results
    
    async def test_page_evaluator(self, project_path: str, page: Page, html: str, soup: BeautifulSoup, 
                                body_text: str, analysis_results_dir: Path, test_port: int):
        """Test page evaluation"""
        evaluator = await self._create_evaluator(project_path, page, html, body_text, test_port)
        results_json = await evaluator.evaluate()
        results = json.loads(results_json)
        results["url"] = evaluator.url
        save_results('page', results, project_path, analysis_results_dir)
        assert "url" in results
        assert "results" in results
        assert "design_data" in results
        assert "performance_metrics" in results

if __name__ == '__main__':
    pytest.main()