from datetime import datetime
from typing import Dict, Any
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import spacy
from ..utils.error_handler import AnalysisError
from .base_analyzer import BaseAnalyzer
import json

class SEOAnalyzer(BaseAnalyzer):
    """Analyzes web pages for search engine optimization."""
    
    def __init__(self):
        super().__init__()
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            from spacy.cli import download
            download("en_core_web_sm")
            self.nlp = spacy.load("en_core_web_sm")
    
    async def analyze(self, url: str, html: Any) -> str:
        """
        Perform comprehensive SEO analysis.
        Returns:
            JSON string containing SEO analysis results and JSON file path
        """
        try:
            # Check if html is a Playwright Page object
            if hasattr(html, 'content') and callable(html.content):
                # Extract HTML content from the Page object
                html = await html.content()

            # Parse the HTML content with BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")

            # Run all SEO analyses
            results = {
                "meta_tags": self._analyze_meta_tags(soup),
                "content_structure": self._analyze_content_structure(soup),
                "url_structure": self._analyze_url_structure(soup),
                "image_optimization": self._analyze_image_optimization(soup),
                "mobile_friendliness": self._analyze_mobile_friendliness(soup),
                "technical_seo": self._analyze_technical_seo(soup)
            }
            
            # Calculate overall score
            scores = [result.get("score", 0) for result in results.values() if isinstance(result, dict)]
            overall_score = sum(scores) / len(scores) if scores else 0
            
            # Collect all issues and recommendations
            all_issues = []
            all_recommendations = []
            metrics = {}
            
            for check_name, result in results.items():
                if isinstance(result, dict):
                    all_issues.extend(result.get("issues", []))
                    all_recommendations.extend(result.get("recommendations", []))
                    metrics[check_name] = {
                        "score": result.get("score", 0),
                        "details": result.get("details", {})
                    }
            
            # Standardize results
            standardized_results = {
                "overall_score": overall_score,
                "issues": all_issues,
                "recommendations": all_recommendations,
                "metrics": metrics,
                "details": results
            }
            
            # Save to JSON
            json_path = self.save_to_json(standardized_results, url, "seo")
            
            return json.dumps({
                "results": {
                    "overall_score": overall_score,
                    "issues": all_issues,
                    "recommendations": all_recommendations,
                    "metrics": metrics
                },
                "json_path": "analysis_results/seoanalyzer_{}_{}.json".format(urlparse(url).netloc, datetime.now().strftime("%Y%m%d_%H%M%S"))
            })
        except Exception as e:
            return json.dumps({
                "error": f"SEO analysis failed: {str(e)}",
                "status": "failed",
                "overall_score": 0.0,
                "details": {},
                "issues": [f"Analysis failed: {str(e)}"],
                "recommendations": ["Fix analyzer implementation"],
                "metrics": {}
            })
    
    def _analyze_meta_tags(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Analyze meta tags for SEO."""
        issues = []
        recommendations = []
        
        # Check for essential meta tags
        title = soup.find("title")
        if not title:
            issues.append("Missing title tag")
        else:
            title_text = title.text.strip()
            if len(title_text) < 30:
                issues.append("Title tag is too short (less than 30 characters)")
            elif len(title_text) > 60:
                issues.append("Title tag is too long (more than 60 characters)")
            else:
                recommendations.append(f"Title tag length is optimal: {len(title_text)} characters")
        
        meta_desc = soup.find("meta", {"name": "description"})
        if not meta_desc:
            issues.append("Missing meta description")
        else:
            desc_text = meta_desc.get("content", "").strip()
            if len(desc_text) < 50:
                issues.append("Meta description is too short (less than 50 characters)")
            elif len(desc_text) > 160:
                issues.append("Meta description is too long (more than 160 characters)")
            else:
                recommendations.append(f"Meta description length is optimal: {len(desc_text)} characters")
        
        # Check for proper Open Graph tags
        og_tags = soup.find_all("meta", {"property": lambda x: x and x.startswith("og:")})
        required_og_tags = ["og:title", "og:description", "og:image", "og:url"]
        missing_og_tags = [tag for tag in required_og_tags
                         if not any(t.get("property") == tag for t in og_tags)]
        if missing_og_tags:
            issues.append(f"Missing required Open Graph tags: {', '.join(missing_og_tags)}")
        else:
            recommendations.append("All required Open Graph tags are present")
        
        # Check for proper Twitter Card tags
        twitter_tags = soup.find_all("meta", {"name": lambda x: x and x.startswith("twitter:")})
        required_twitter_tags = ["twitter:card", "twitter:title", "twitter:description", "twitter:image"]
        missing_twitter_tags = [tag for tag in required_twitter_tags
                             if not any(t.get("name") == tag for t in twitter_tags)]
        if missing_twitter_tags:
            issues.append(f"Missing required Twitter Card tags: {', '.join(missing_twitter_tags)}")
        else:
            recommendations.append("All required Twitter Card tags are present")
        
        # Check for canonical URL
        canonical = soup.find("link", {"rel": "canonical"})
        if not canonical:
            issues.append("Missing canonical URL tag")
        else:
            recommendations.append("Canonical URL tag is present")
        
        # Check for robots meta tag
        robots = soup.find("meta", {"name": "robots"})
        if not robots:
            issues.append("Missing robots meta tag")
        else:
            content = robots.get("content", "").lower()
            if "noindex" in content or "nofollow" in content:
                issues.append("Page is not indexable or followable")
            else:
                recommendations.append("Robots meta tag is properly configured")
        
        # Calculate score based on issues and recommendations
        total_checks = len(issues) + len(recommendations)
        score = (len(recommendations) / total_checks * 100) if total_checks > 0 else 0
        
        return {
            "score": score,
            "issues": issues,
            "recommendations": recommendations
        }
    
    def _analyze_content_structure(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Analyze content structure for SEO."""
        issues = []
        
        # Check for proper heading hierarchy
        headings = soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
        if not any(h.name == "h1" for h in headings):
            issues.append("Missing H1 heading")
        
        # Check for proper content length and analyze keywords
        content = soup.find("body")
        if content:
            text = content.get_text().strip()
            text_length = len(text)
            if text_length < 300:
                issues.append("Content is too short (less than 300 characters)")
            
            # Analyze keywords using spaCy
            doc = self.nlp(text)
            
            # Extract important keywords (nouns and proper nouns)
            keywords = [token.text.lower() for token in doc 
                       if token.pos_ in ["NOUN", "PROPN"] 
                       and not token.is_stop 
                       and len(token.text) > 2]
            
            # Count keyword frequency
            keyword_freq = {}
            for keyword in keywords:
                keyword_freq[keyword] = keyword_freq.get(keyword, 0) + 1
            
            # Sort keywords by frequency
            sorted_keywords = sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)
            
            # Add keyword analysis to results
            if sorted_keywords:
                issues.append(f"Top keywords: {', '.join([f'{k} ({v})' for k, v in sorted_keywords[:5]])}")
            else:
                issues.append("No significant keywords found in content")
        
        return {
            "score": max(100 - len(issues) * 10, 0),
            "issues": issues
        }
    
    def _analyze_url_structure(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Analyze URL structure for SEO."""
        issues = []
        
        # Check for proper URL structure
        links = soup.find_all("a", href=True)
        for link in links:
            url = link["href"]
            if url.startswith("/"):
                # Check for proper URL format
                if "_" in url or " " in url:
                    issues.append(f"URL contains underscores or spaces: {url}")
                
                # Check for proper URL length
                if len(url) > 100:
                    issues.append(f"URL is too long: {url}")
        
        return {
            "score": max(100 - len(issues) * 10, 0),
            "issues": issues
        }
    
    def _analyze_image_optimization(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Analyze image optimization for SEO."""
        issues = []
        recommendations = []
        
        # Check for proper image attributes
        images = soup.find_all("img")
        if not images:
            issues.append("No images found on the page")
            return {
                "score": 0,
                "issues": issues,
                "recommendations": recommendations
            }
        
        optimized_images = 0
        for img in images:
            img_issues = []
            
            # Check for alt text
            if not img.get("alt"):
                img_issues.append("Missing alt text")
            elif len(img.get("alt", "").strip()) < 3:
                img_issues.append("Alt text is too short")
            else:
                recommendations.append(f"Image has proper alt text: {img.get('alt')}")
            
            # Check for src attribute
            if not img.get("src"):
                img_issues.append("Missing src attribute")
            else:
                src = img.get("src")
                if not src.startswith(("http://", "https://", "/")):
                    img_issues.append("Invalid src URL format")
                elif src.endswith((".jpg", ".jpeg", ".png", ".webp")):
                    recommendations.append(f"Image has proper format: {src}")
                else:
                    img_issues.append("Image should use .jpg, .jpeg, .png, or .webp format")
            
            # Check for dimensions
            if not img.get("width") or not img.get("height"):
                img_issues.append("Missing width or height attributes")
            else:
                try:
                    width = int(img.get("width", 0))
                    height = int(img.get("height", 0))
                    if width > 0 and height > 0:
                        recommendations.append(f"Image has proper dimensions: {width}x{height}")
                    else:
                        img_issues.append("Invalid width or height values")
                except ValueError:
                    img_issues.append("Width or height values are not numbers")
            
            # Check for lazy loading
            if not img.get("loading") == "lazy":
                img_issues.append("Missing lazy loading attribute")
            else:
                recommendations.append("Image uses lazy loading")
            
            if not img_issues:
                optimized_images += 1
            else:
                issues.extend([f"Image {src}: {issue}" for issue in img_issues])
        
        # Calculate optimization percentage
        optimization_percentage = (optimized_images / len(images)) * 100
        if optimization_percentage == 100:
            recommendations.append("All images are properly optimized")
        else:
            issues.append(f"Only {optimization_percentage:.1f}% of images are optimized")
        
        return {
            "score": optimization_percentage,
            "issues": issues,
            "recommendations": recommendations
        }
    
    def _analyze_mobile_friendliness(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Analyze mobile friendliness for SEO."""
        issues = []
        
        # Check for proper viewport meta tag
        viewport = soup.find("meta", {"name": "viewport"})
        if not viewport:
            issues.append("Missing viewport meta tag")
        elif "width=device-width" not in viewport.get("content", ""):
            issues.append("Viewport meta tag missing width=device-width")
        
        # Check for proper mobile-friendly elements
        if not soup.find("link", rel="stylesheet", media="screen and (max-width: 768px)"):
            issues.append("Missing mobile-specific stylesheet")
        
        return {
            "score": max(100 - len(issues) * 20, 0),
            "issues": issues
        }
    
    def _analyze_technical_seo(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Analyze technical SEO aspects."""
        issues = []
        
        # Check for proper canonical URL
        if not soup.find("link", rel="canonical"):
            issues.append("Missing canonical URL")
        
        # Check for proper robots meta tag
        if not soup.find("meta", {"name": "robots"}):
            issues.append("Missing robots meta tag")
        
        # Check for proper sitemap
        if not soup.find("link", rel="sitemap"):
            issues.append("Missing sitemap reference")
        
        # Check for proper structured data
        if not soup.find("script", type="application/ld+json"):
            issues.append("Missing structured data")
        
        return {
            "score": max(100 - len(issues) * 20, 0),
            "issues": issues
        }