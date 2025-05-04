from typing import Dict, Any, List, Optional, Tuple
import logging
import re
from collections import Counter
import asyncio
import json
import spacy
from textblob import TextBlob
import textstat
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import wordnet, stopwords
from nltk.tag import pos_tag
from nltk.sentiment import SentimentIntensityAnalyzer
from bs4 import BeautifulSoup
from .base_analyzer import BaseAnalyzer

logger = logging.getLogger(__name__)

# Initialize flags for optional dependencies
HAS_SPACY = False
HAS_NLTK = False
HAS_NLTK_DATA = False

# Try to load spaCy
try:
    import spacy
    HAS_SPACY = True
except ImportError:
    logger.warning("spaCy is not installed. Some NLP features will be limited.")

# Load spaCy model only if available
nlp = None
if HAS_SPACY:
    try:
        nlp = spacy.load("en_core_web_sm")
    except Exception as e:
        logger.warning(f"Failed to load spaCy model: {e}")
        HAS_SPACY = False

# Try to load NLTK and its data
try:
    import nltk
    HAS_NLTK = True
    try:
        # Download required NLTK data
        nltk.download('punkt', quiet=True)
        nltk.download('averaged_perceptron_tagger', quiet=True)
        nltk.download('stopwords', quiet=True)
        HAS_NLTK_DATA = True
    except Exception as e:
        logger.warning(f"Failed to download NLTK data: {e}")
except ImportError:
    logger.warning("NLTK is not installed. Some NLP features will be limited.")

INCLUSIVE_LANGUAGE_DB = {
    "blacklist": {"alternatives": ["denylist", "blocklist"], "severity": "high"},
    "whitelist": {"alternatives": ["allowlist", "safelist"], "severity": "high"},
    "master": {"alternatives": ["main", "primary", "controller"], "severity": "medium"},
    "slave": {"alternatives": ["secondary", "replica", "worker"], "severity": "high"},
}

class NLPContentAnalyzer(BaseAnalyzer):
    """Analyzes text content using NLP techniques with optional spaCy and NLTK support."""
    
    def __init__(self):
        super().__init__()
        self.inclusive_language_db = INCLUSIVE_LANGUAGE_DB
        self.stop_words = set(stopwords.words('english')) if HAS_NLTK_DATA else set()
    
    def _tokenize_text(self, text: str) -> List[str]:
        """Tokenize text using available NLP libraries."""
        if HAS_SPACY and nlp:
            doc = nlp(text)
            return [token.text for token in doc]
        elif HAS_NLTK_DATA:
            return word_tokenize(text)
        return text.split()  # Fallback to basic splitting
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences using available NLP libraries."""
        if HAS_SPACY and nlp:
            doc = nlp(text)
            return [str(sent) for sent in doc.sents]
        elif HAS_NLTK_DATA:
            return sent_tokenize(text)
        return [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]  # Basic sentence splitting
    
    async def _analyze_readability(self, text: str) -> Dict[str, float]:
        """Analyze text readability using various metrics."""
        def calculate_metrics():
            return {
                "flesch_reading_ease": textstat.flesch_reading_ease(text),
                "flesch_kincaid_grade": textstat.flesch_kincaid_grade(text),
                "gunning_fog": textstat.gunning_fog(text),
                "smog_index": textstat.smog_index(text),
                "automated_readability_index": textstat.automated_readability_index(text),
                "coleman_liau_index": textstat.coleman_liau_index(text),
                "linsear_write_formula": textstat.linsear_write_formula(text),
                "dale_chall_readability_score": textstat.dale_chall_readability_score(text)
            }
        
        # Run blocking operations in a thread pool
        return await asyncio.get_event_loop().run_in_executor(None, calculate_metrics)
    
    async def _analyze_sentiment(self, text: str) -> Dict[str, float]:
        """Analyze sentiment of text using available NLP tools."""
        loop = asyncio.get_event_loop()
        if HAS_NLTK_DATA:
            try:
                sia = SentimentIntensityAnalyzer()
                scores = await loop.run_in_executor(None, sia.polarity_scores, text)
                return {
                    'positive': scores['pos'],
                    'negative': scores['neg'],
                    'neutral': scores['neu'],
                    'compound': scores['compound']
                }
            except Exception as e:
                logger.warning(f"NLTK sentiment analysis failed: {e}")
        
        # Fallback to TextBlob for basic sentiment
        try:
            blob = await loop.run_in_executor(None, TextBlob, text)
            polarity = await loop.run_in_executor(None, getattr, blob, 'polarity')
            return {
                'compound': polarity,
                'positive': max(0, polarity),
                'negative': abs(min(0, polarity)),
                'neutral': 1 - abs(polarity)
            }
        except Exception as e:
            logger.warning(f"TextBlob sentiment analysis failed: {e}")
            return {
                'positive': 0.0,
                'negative': 0.0,
                'neutral': 1.0,
                'compound': 0.0
            }
    
    async def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text using available NLP tools."""
        tokens = self._tokenize_text(text)
        
        if HAS_NLTK_DATA:
            try:
                # Use POS tagging to identify nouns and adjectives
                tagged = await asyncio.get_event_loop().run_in_executor(None, pos_tag, tokens)
                keywords = [word for word, pos in tagged 
                          if pos.startswith(('NN', 'JJ')) and word.lower() not in self.stop_words]
                return list(set(keywords))[:10]  # Return top 10 unique keywords
            except Exception as e:
                logger.warning(f"NLTK keyword extraction failed: {e}")
        
        # Fallback to basic frequency-based extraction
        words = [word.lower() for word in tokens if len(word) > 3]
        word_freq = Counter(words)
        return [word for word, _ in word_freq.most_common(10) if word not in self.stop_words]
    
    async def _check_grammar(self, text: str) -> List[Dict[str, Any]]:
        """Check grammar using available NLP tools."""
        issues = []
        
        if not text.strip():
            return issues

        # Basic checks that don't require NLTK
        sentences = self._split_sentences(text)
        
        for sentence in sentences:
            # Check for basic capitalization
            if sentence and sentence[0].islower():
                issues.append({
                    'type': 'capitalization',
                    'message': 'Sentence should start with a capital letter',
                    'text': sentence
                })
            
            # Check for ending punctuation
            if not sentence.strip()[-1] in '.!?':
                issues.append({
                    'type': 'punctuation',
                    'message': 'Sentence should end with proper punctuation',
                    'text': sentence
                })

        if HAS_NLTK_DATA:
            try:
                # Additional NLTK-based checks could be added here
                tagged = await asyncio.get_event_loop().run_in_executor(None, pos_tag, word_tokenize(text))
                # Add grammar checks based on POS patterns
                for i in range(len(tagged) - 1):
                    if tagged[i][1] == 'DT' and tagged[i + 1][1] == 'VB':
                        issues.append({
                            'type': 'grammar',
                            'message': f"Possible article-verb agreement error: '{tagged[i][0]} {tagged[i + 1][0]}'",
                            'text': f"{tagged[i][0]} {tagged[i + 1][0]}"
                        })
            except Exception as e:
                logger.warning(f"NLTK grammar checking failed: {e}")

        return issues
    
    async def detect_inclusive_language(self, text: str) -> List[Dict[str, Any]]:
        """Detect non-inclusive language using available NLP tools."""
        issues = []
        
        if not text.strip():
            return issues

        tokens = self._tokenize_text(text.lower())
        
        for token in tokens:
            if token in self.inclusive_language_db:
                issue = {
                    'term': token,
                    'alternatives': self.inclusive_language_db[token]['alternatives'],
                    'severity': self.inclusive_language_db[token]['severity']
                }
                issues.append(issue)

        return issues
    
    async def analyze(self, url: str, text: str) -> str:
        """
        Perform comprehensive text analysis using available NLP tools.
        
        Args:
            url: Target URL
            text: Text content to analyze
            
        Returns:
            JSON string containing NLP analysis results and JSON file path
        """
        try:
            if not text.strip():
                results = {
                    'readability': {},
                    'sentiment': {},
                    'keywords': [],
                    'grammar_issues': [],
                    'inclusive_language_issues': [],
                    'translation_quality': {},
                    'content_gaps': {}
                }
            else:
                # Run all NLP analyses concurrently
                tasks = [
                    self._analyze_readability(text),
                    self._analyze_sentiment(text),
                    self._extract_keywords(text),
                    self._check_grammar(text),
                    self.detect_inclusive_language(text),
                    self.detect_translation_quality(text),
                    self.analyze_content_gaps(text)
                ]
                
                results = await asyncio.gather(*tasks)
                
                # Organize results
                results = {
                    'readability': results[0],
                    'sentiment': results[1],
                    'keywords': results[2],
                    'grammar_issues': results[3],
                    'inclusive_language_issues': results[4],
                    'translation_quality': results[5],
                    'content_gaps': results[6]
                }

            # Calculate overall score
            scores = []
            if results['readability']:
                scores.append(results['readability'].get('average_score', 0))
            if results['sentiment']:
                scores.append((results['sentiment'].get('compound', 0) + 1) * 50)  # Convert -1 to 1 to 0 to 100
            if results['grammar_issues']:
                grammar_score = max(100 - len(results['grammar_issues']) * 10, 0)
                scores.append(grammar_score)
            if results['inclusive_language_issues']:
                inclusive_score = max(100 - len(results['inclusive_language_issues']) * 20, 0)
                scores.append(inclusive_score)

            overall_score = sum(scores) / len(scores) if scores else 0

            # Generate recommendations
            recommendations = []
            if results['readability']:
                if results['readability'].get('flesch_reading_ease', 0) < 60:
                    recommendations.append("Consider improving readability by simplifying complex sentences")
            if results['sentiment']:
                if results['sentiment'].get('compound', 0) < -0.5:
                    recommendations.append("Content appears negative, consider more positive language")
            if results['grammar_issues']:
                recommendations.append(f"Fix {len(results['grammar_issues'])} grammar issues")
            if results['inclusive_language_issues']:
                recommendations.append(f"Address {len(results['inclusive_language_issues'])} instances of non-inclusive language")

            # Standardize results
            standardized_results = {
                'overall_score': overall_score,
                'issues': {
                    'grammar': results['grammar_issues'],
                    'inclusive_language': results['inclusive_language_issues']
                },
                'recommendations': recommendations,
                'metrics': {
                    'readability': results['readability'],
                    'sentiment': results['sentiment'],
                    'translation_quality': results['translation_quality'],
                    'content_gaps': results['content_gaps']
                },
                'details': {
                    'keywords': results['keywords'],
                    'raw_analysis': results
                }
            }

            # Save to JSON
            json_path = self.save_to_json(standardized_results, url, "nlp")

            return json.dumps({
                "results": standardized_results,
                "json_path": json_path
            }, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"NLP analysis failed: {str(e)}")
            raise AnalysisError(f"NLP analysis failed: {str(e)}")

    @staticmethod
    async def analyze_sentiment(text: str) -> Dict[str, Any]:
        blob = TextBlob(text)
        return {
            "polarity": blob.sentiment.polarity,
            "subjectivity": blob.sentiment.subjectivity
        }

    @staticmethod
    async def detect_inclusive_language(text: str) -> List[Dict[str, Any]]:
        issues = []
        # Use basic string matching if spaCy is not available
        words = text.lower().split()
        for word in words:
            if word in INCLUSIVE_LANGUAGE_DB:
                entry = INCLUSIVE_LANGUAGE_DB[word]
                issues.append({
                    "term": word,
                    "alternatives": entry["alternatives"],
                    "severity": entry["severity"]
                })
        return issues

    @staticmethod
    async def detect_translation_quality(text: str) -> Dict[str, Any]:
        # Use TextBlob for basic language detection and quality assessment
        blob = TextBlob(text)
        try:
            detected_language = blob.detect_language()
            is_english = detected_language == 'en'
            translation_likelihood = 0.9 if is_english else 0.6
        except:
            # If language detection fails, assume it's English
            translation_likelihood = 0.8
        
        return {
            "translation_likelihood": translation_likelihood,
            "cultural_appropriateness": True
        }

    @staticmethod
    async def analyze_content_gaps(text: str) -> Dict[str, Any]:
        # Use NLTK for basic content analysis when spaCy is not available
        words = word_tokenize(text.lower())
        word_freq = nltk.FreqDist(words)
        return {
            "word_frequency": dict(word_freq.most_common(10)),
            "vocabulary_richness": len(set(words)) / len(words) if words else 0
        }

    @staticmethod
    async def compute_readability(text: str) -> Dict[str, Any]:
        return {
            "flesch_reading_ease": textstat.flesch_reading_ease(text),
            "flesch_kincaid_grade": textstat.flesch_kincaid_grade(text),
            "gunning_fog": textstat.gunning_fog(text)
        }