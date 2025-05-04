import pytest
import json
from core.analyzers.nlp_content_analyzer import NLPContentAnalyzer

@pytest.fixture
def analyzer():
    return NLPContentAnalyzer()

@pytest.mark.asyncio
async def test_basic_analysis():
    """Test basic analysis functionality."""
    analyzer = NLPContentAnalyzer()
    text = "This is a test sentence. It contains multiple sentences!"
    result_json = await analyzer.analyze(text)
    print("\nNLP Analyzer JSON Output:")
    print(result_json)
    assert isinstance(result_json, str)
    result = json.loads(result_json)
    assert 'results' in result
    assert 'json_path' in result
    assert 'readability' in result['results']
    assert 'sentiment' in result['results']
    assert 'keywords' in result['results']
    assert 'grammar_issues' in result['results']
    assert 'inclusive_language_issues' in result['results']

@pytest.mark.asyncio
async def test_empty_text():
    """Test handling of empty text."""
    analyzer = NLPContentAnalyzer()
    result_json = await analyzer.analyze("")
    print("\nNLP Analyzer Empty Text JSON Output:")
    print(result_json)
    assert isinstance(result_json, str)
    result = json.loads(result_json)
    assert 'results' in result
    assert 'readability' in result['results']
    assert result['results']['readability'] == {}
    assert result['results']['sentiment'] == {}
    assert result['results']['keywords'] == []
    assert result['results']['grammar_issues'] == []
    assert result['results']['inclusive_language_issues'] == []

@pytest.mark.asyncio
async def test_inclusive_language():
    """Test detection of non-inclusive language."""
    analyzer = NLPContentAnalyzer()
    text = "The master branch and blacklist feature"
    issues = await analyzer.detect_inclusive_language(text)
    assert len(issues) >= 2
    terms = {issue['term'] for issue in issues}
    assert 'master' in terms
    assert 'blacklist' in terms

@pytest.mark.asyncio
async def test_grammar_check():
    """Test basic grammar checking."""
    analyzer = NLPContentAnalyzer()
    text = "this sentence has no capital letter."
    issues = await analyzer._check_grammar(text)
    assert any(issue['type'] == 'capitalization' for issue in issues)

if __name__ == '__main__':
    pytest.main([__file__])