import pytest
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from unittest.mock import patch
from core.analyzers.accessibility_analyzer import AccessibilityAnalyzer
from core.analyzers.performance_analyzer import PerformanceAnalyzer
from core.analyzers.security_analyzer import SecurityAnalyzer
from core.analyzers.ux_analyzer import UXAnalyzer
from core.analyzers.code_analyzer import CodeAnalyzer
from core.analyzers.seo_analyzer import SEOAnalyzer
from core.analyzers.nlp_content_analyzer import NLPContentAnalyzer, HAS_SPACY
from typing import List, Dict
import asyncio
import hashlib
import multiprocessing
from concurrent.futures import ProcessPoolExecutor

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

@pytest.fixture
def sample_text():
    """Fixture for sample text content."""
    return """
    This is a test paragraph. It contains multiple sentences with varying structure.
    The quick brown fox jumps over the lazy dog. Some people use master-slave terminology,
    which should be flagged as non-inclusive language. This text should be analyzed for
    readability, sentiment, and grammar.
    """

@pytest.fixture
def nlp_analyzer():
    """Fixture for NLPContentAnalyzer instance."""
    return NLPContentAnalyzer()

@pytest.fixture
def sample_texts():
    """Fixture for multiple sample texts."""
    return [
        "This is a technical document about API endpoints.",
        "Transform your workflow with our amazing solution!",
        "In this blog post, we'll explore web development trends."
    ]

@pytest.fixture
def batch_analyzer(nlp_analyzer):
    """Fixture for BatchAnalyzer."""
    class BatchAnalyzer:
        def __init__(self, analyzer: NLPContentAnalyzer, batch_size: int = 10):
            self.analyzer = analyzer
            self.batch_size = batch_size

        async def analyze_batch(self, texts: List[str]) -> List[Dict]:
            results = []
            for i in range(0, len(texts), self.batch_size):
                batch = texts[i:i + self.batch_size]
                batch_results = await asyncio.gather(
                    *[self.analyzer.analyze(text) for text in batch]
                )
                results.extend(batch_results)
            return results

        async def analyze_with_retry(self, text: str, max_retries: int = 3) -> Dict:
            for attempt in range(max_retries):
                try:
                    return await self.analyzer.analyze(text)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    await asyncio.sleep(0.1 * (attempt + 1))
    
    return BatchAnalyzer(nlp_analyzer)

@pytest.fixture
def custom_analyzer():
    """Fixture for CustomAnalyzer."""
    class TechnicalTermAnalyzer:
        def __init__(self, technical_terms: List[str]):
            self.technical_terms = set(technical_terms)

        async def analyze(self, text: str) -> Dict:
            words = text.lower().split()
            found_terms = [term for term in self.technical_terms if term in words]
            return {
                "technical_terms": found_terms,
                "coverage": len(found_terms) / len(self.technical_terms)
            }
    
    return TechnicalTermAnalyzer(["api", "endpoint", "authentication"])

@pytest.fixture
def cached_analyzer(nlp_analyzer):
    """Fixture for CachedAnalyzer."""
    class CachedAnalyzer:
        def __init__(self, analyzer: NLPContentAnalyzer):
            self.analyzer = analyzer
            self.cache = {}

        def _get_cache_key(self, text: str) -> str:
            return hashlib.md5(text.encode()).hexdigest()

        async def analyze(self, text: str) -> Dict:
            cache_key = self._get_cache_key(text)
            if cache_key in self.cache:
                return self.cache[cache_key]
            
            results = await self.analyzer.analyze(text)
            self.cache[cache_key] = results
            return results

        def clear_cache(self):
            self.cache.clear()
    
    return CachedAnalyzer(nlp_analyzer)

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

@pytest.mark.asyncio
async def test_nlp_analyzer_basic_functionality(nlp_analyzer, sample_text):
    """Test basic NLP analysis functionality."""
    results = await nlp_analyzer.analyze(sample_text)
    
    # Check all expected keys are present
    assert "readability" in results
    assert "sentiment" in results
    assert "keywords" in results
    assert "grammar" in results
    assert "overall_score" in results
    
    # Check score ranges
    assert 0 <= results["overall_score"] <= 100
    assert 0 <= results["readability"]["score"] <= 100
    assert 0 <= results["sentiment"]["score"] <= 100
    assert 0 <= results["grammar"]["score"] <= 100

def test_nlp_readability_analysis(nlp_analyzer):
    """Test readability analysis with different text inputs."""
    # Test with simple text
    simple_text = "This is a simple sentence. It is easy to read."
    simple_results = nlp_analyzer._analyze_readability(simple_text)
    
    # Test with complex text
    complex_text = "The intricate interplay between various morphological and syntactic structures in linguistics presents a fascinating paradigm for analysis."
    complex_results = nlp_analyzer._analyze_readability(complex_text)
    
    # Simple text should have better readability score
    assert simple_results["score"] > complex_results["score"]
    
    # Test with empty text
    empty_results = nlp_analyzer._analyze_readability("")
    assert empty_results["score"] == 100  # Best score for empty text
    assert empty_results["metrics"]["avg_sentence_length"] == 0
    assert empty_results["metrics"]["avg_word_length"] == 0

def test_nlp_sentiment_analysis(nlp_analyzer):
    """Test sentiment analysis with different text inputs."""
    # Test positive sentiment
    positive_text = "I love this amazing product! It's wonderful and fantastic."
    positive_results = nlp_analyzer._analyze_sentiment(positive_text)
    
    # Test negative sentiment
    negative_text = "This is terrible and disappointing. I hate it."
    negative_results = nlp_analyzer._analyze_sentiment(negative_text)
    
    # Positive text should have higher sentiment score
    assert positive_results["score"] > negative_results["score"]
    
    # Test neutral text
    neutral_text = "This is a factual statement about the weather."
    neutral_results = nlp_analyzer._analyze_sentiment(neutral_text)
    assert 45 <= neutral_results["score"] <= 55  # Should be close to neutral (50)

@pytest.mark.skipif(not HAS_SPACY, reason="spaCy not installed")
def test_nlp_spacy_keyword_extraction(nlp_analyzer):
    """Test keyword extraction with spaCy."""
    text = "The software engineer developed a new algorithm for machine learning."
    results = nlp_analyzer._extract_keywords(text)
    
    # Check if common technical terms are extracted
    keywords = [k.lower() for k in results["keywords"]]
    assert any(word in keywords for word in ["software", "engineer", "algorithm", "learning"])
    assert results["count"] > 0

def test_nlp_nltk_keyword_extraction(nlp_analyzer):
    """Test keyword extraction with NLTK fallback."""
    with patch('core.analyzers.nlp_content_analyzer.HAS_SPACY', False):
        text = "The software engineer developed a new algorithm for machine learning."
        results = nlp_analyzer._extract_keywords(text)
        
        # Check if nouns and verbs are extracted
        keywords = [k.lower() for k in results["keywords"]]
        assert any(word in keywords for word in ["software", "engineer", "algorithm", "learning"])
        assert results["count"] > 0

def test_nlp_grammar_checking(nlp_analyzer):
    """Test grammar checking functionality."""
    # Test complete sentence
    good_text = "The cat sits on the mat."
    good_results = nlp_analyzer._check_grammar(good_text)
    assert good_results["score"] == 100
    assert len(good_results["issues"]) == 0
    
    # Test incomplete sentence
    bad_text = "sitting on the mat"
    bad_results = nlp_analyzer._check_grammar(bad_text)
    assert bad_results["score"] < 100
    assert len(bad_results["issues"]) > 0
    assert "Missing subject" in bad_results["issues"]

def test_nlp_inclusive_language_detection(nlp_analyzer, sample_text):
    """Test inclusive language detection."""
    results = NLPContentAnalyzer.detect_inclusive_language(sample_text)
    
    # Check if non-inclusive terms are detected
    assert len(results) > 0
    assert any(issue["term"] == "master" for issue in results)
    
    # Test with inclusive text
    inclusive_text = "The primary server coordinates with the replica servers."
    inclusive_results = NLPContentAnalyzer.detect_inclusive_language(inclusive_text)
    assert len(inclusive_results) == 0

def test_nlp_translation_quality_detection(nlp_analyzer):
    """Test translation quality detection."""
    # Test English text
    english_text = "This is a well-written English sentence."
    english_results = NLPContentAnalyzer.detect_translation_quality(english_text)
    assert english_results["translation_likelihood"] > 0.8
    
    # Test mixed language text
    mixed_text = "This is a mix of English and немного русского."
    mixed_results = NLPContentAnalyzer.detect_translation_quality(mixed_text)
    assert mixed_results["translation_likelihood"] < 0.8

def test_nlp_content_gaps_analysis(nlp_analyzer):
    """Test content gaps analysis."""
    text = "The quick brown fox jumps over the lazy dog. The fox is quick and brown."
    results = NLPContentAnalyzer.analyze_content_gaps(text)
    
    assert "keyword_density" in results
    assert 0 <= results["keyword_density"] <= 1
    assert isinstance(results["content_gaps"], list)
    assert isinstance(results["seo_potential"], (int, float))

def test_nlp_compute_readability_metrics(nlp_analyzer):
    """Test readability metrics computation."""
    text = "This is a simple test sentence. It should be easy to read."
    results = NLPContentAnalyzer.compute_readability(text)
    
    assert "flesch" in results
    assert "smog" in results
    assert "coleman_liau" in results
    
    # Flesch reading ease should be between 0 and 100
    assert 0 <= results["flesch"] <= 100

@pytest.mark.asyncio
async def test_nlp_full_analysis_pipeline(nlp_analyzer, sample_text):
    """Test the full analysis pipeline."""
    results = await nlp_analyzer.analyze(sample_text)
    static_results = NLPContentAnalyzer.analyze(sample_text)
    
    # Check async analysis results
    assert all(key in results for key in ["readability", "sentiment", "keywords", "grammar"])
    assert isinstance(results["overall_score"], (int, float))
    
    # Check static analysis results
    assert all(key in static_results for key in [
        "sentiment", "inclusive_language_issues", "translation_quality",
        "content_gaps", "readability"
    ]) 

@pytest.mark.asyncio
async def test_batch_processing(batch_analyzer, sample_texts):
    """Test batch processing functionality."""
    # Test batch analysis
    results = await batch_analyzer.analyze_batch(sample_texts)
    assert len(results) == len(sample_texts)
    
    # Verify each result has expected structure
    for result in results:
        assert "readability" in result
        assert "sentiment" in result
        assert "keywords" in result
        assert "grammar" in result
        assert "overall_score" in result

@pytest.mark.asyncio
async def test_retry_mechanism(batch_analyzer):
    """Test retry mechanism for failed analyses."""
    # Test successful retry
    result = await batch_analyzer.analyze_with_retry("Test text")
    assert isinstance(result, dict)
    
    # Test with invalid input (should raise after retries)
    with pytest.raises(Exception):
        await batch_analyzer.analyze_with_retry("")

def test_custom_analyzer(custom_analyzer):
    """Test custom technical term analyzer."""
    # Test with technical content
    result = custom_analyzer.analyze("The API endpoint requires authentication")
    assert "technical_terms" in result
    assert len(result["technical_terms"]) > 0
    assert result["coverage"] > 0
    
    # Test with non-technical content
    result = custom_analyzer.analyze("This is a simple text")
    assert len(result["technical_terms"]) == 0
    assert result["coverage"] == 0

@pytest.mark.asyncio
async def test_caching_mechanism(cached_analyzer):
    """Test caching mechanism."""
    text = "Test text for caching"
    
    # First analysis (should compute)
    result1 = await cached_analyzer.analyze(text)
    assert isinstance(result1, dict)
    
    # Second analysis (should use cache)
    result2 = await cached_analyzer.analyze(text)
    assert result1 == result2
    
    # Test cache clearing
    cached_analyzer.clear_cache()
    result3 = await cached_analyzer.analyze(text)
    assert result1 == result3  # Results should be same but computed again

@pytest.mark.asyncio
async def test_parallel_processing(nlp_analyzer):
    """Test parallel processing of multiple texts."""
    class ParallelAnalyzer:
        def __init__(self, analyzer: NLPContentAnalyzer):
            self.analyzer = analyzer
            self.max_workers = multiprocessing.cpu_count()

        async def analyze_parallel(self, texts: List[str]) -> List[Dict]:
            with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
                loop = asyncio.get_event_loop()
                tasks = [
                    loop.run_in_executor(executor, self.analyzer.analyze, text)
                    for text in texts
                ]
                return await asyncio.gather(*tasks)
    
    parallel_analyzer = ParallelAnalyzer(nlp_analyzer)
    results = await parallel_analyzer.analyze_parallel(sample_texts)
    
    assert len(results) == len(sample_texts)
    for result in results:
        assert isinstance(result, dict)
        assert "readability" in result
        assert "sentiment" in result

@pytest.mark.asyncio
async def test_content_specific_analysis(nlp_analyzer):
    """Test content-specific analysis configurations."""
    # Technical documentation analysis
    tech_analyzer = NLPContentAnalyzer(custom_metrics={
        "min_readability_score": 60,
        "max_sentence_length": 25,
        "required_keywords": ["api", "function", "parameter"],
        "sentiment_threshold": 0.0
    })
    
    tech_results = await tech_analyzer.analyze(
        "The API function accepts parameters and returns a response."
    )
    assert tech_results["readability"]["score"] >= 60
    
    # Marketing content analysis
    marketing_analyzer = NLPContentAnalyzer(custom_metrics={
        "min_readability_score": 80,
        "max_sentence_length": 15,
        "required_keywords": ["benefit", "solution"],
        "sentiment_threshold": 0.5
    })
    
    marketing_results = await marketing_analyzer.analyze(
        "Transform your workflow with our amazing solution!"
    )
    assert marketing_results["sentiment"]["score"] >= 50

@pytest.mark.asyncio
async def test_error_handling(nlp_analyzer):
    """Test error handling in various scenarios."""
    # Test with empty text
    with pytest.raises(ValueError):
        await nlp_analyzer.analyze("")
    
    # Test with invalid language
    with pytest.raises(ValueError):
        await nlp_analyzer.analyze("Test text", language="invalid")
    
    # Test with extremely long text
    long_text = "Test " * 10000
    result = await nlp_analyzer.analyze(long_text)
    assert isinstance(result, dict)
    assert "readability" in result

@pytest.mark.asyncio
async def test_performance_optimization(nlp_analyzer):
    """Test performance optimization features."""
    # Test memory usage
    class MemoryAwareAnalyzer:
        def __init__(self, analyzer: NLPContentAnalyzer):
            self.analyzer = analyzer
            self.max_memory = 1024 * 1024  # 1MB limit for testing

        async def analyze(self, text: str) -> Dict:
            import psutil
            process = psutil.Process()
            if process.memory_info().rss > self.max_memory:
                raise MemoryError("Memory limit exceeded")
            return await self.analyzer.analyze(text)
    
    memory_analyzer = MemoryAwareAnalyzer(nlp_analyzer)
    
    # Should work with normal text
    result = await memory_analyzer.analyze("Test text")
    assert isinstance(result, dict)
    
    # Should raise with extremely large text
    with pytest.raises(MemoryError):
        await memory_analyzer.analyze("Test " * 1000000) 