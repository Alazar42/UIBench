from typing import Dict, Any
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from ..utils.error_handler import AnalysisError

class SEOAnalyzer:
    """Analyzes web pages for search engine optimization."""
    
    async def analyze(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """
        Perform comprehensive SEO analysis.
        
        Args:
            soup: BeautifulSoup parsed HTML
            
        Returns:
            Dict containing SEO analysis results
        """
        try:
            results = {
                "meta_tags": self._analyze_meta_tags(soup),
                "content_structure": self._analyze_content_structure(soup),
                "url_structure": self._analyze_url_structure(soup),
                "image_optimization": self._analyze_image_optimization(soup),
                "mobile_friendliness": self._analyze_mobile_friendliness(soup),
                "technical_seo": self._analyze_technical_seo(soup)
            }
            
            # Calculate overall SEO score
            scores = [result.get("score", 0) for result in results.values() if isinstance(result, dict)]
            results["overall_score"] = sum(scores) / len(scores) if scores else 0
            
            return results
        except Exception as e:
            raise AnalysisError(f"SEO analysis failed: {str(e)}")
    
    def _analyze_meta_tags(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Analyze meta tags for SEO."""
        issues = []
        
        # Check for essential meta tags
        if not soup.find("title"):
            issues.append("Missing title tag")
        
        meta_desc = soup.find("meta", {"name": "description"})
        if not meta_desc:
            issues.append("Missing meta description")
        elif len(meta_desc.get("content", "")) < 50 or len(meta_desc.get("content", "")) > 160:
            issues.append("Meta description length should be between 50 and 160 characters")
        
        # Check for proper Open Graph tags
        og_tags = soup.find_all("meta", property=lambda x: x and x.startswith("og:"))
        if not og_tags:
            issues.append("Missing Open Graph tags")
        
        # Check for proper Twitter Card tags
        twitter_tags = soup.find_all("meta", name=lambda x: x and x.startswith("twitter:"))
        if not twitter_tags:
            issues.append("Missing Twitter Card tags")
        
        return {
            "score": max(100 - len(issues) * 10, 0),
            "issues": issues
        }
    
    def _analyze_content_structure(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Analyze content structure for SEO."""
        issues = []
        
        # Check for proper heading hierarchy
        headings = soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
        if not any(h.name == "h1" for h in headings):
            issues.append("Missing H1 heading")
        
        # Check for proper content length
        content = soup.find("body")
        if content:
            text_length = len(content.get_text().strip())
            if text_length < 300:
                issues.append("Content is too short (less than 300 characters)")
        
        # Check for proper keyword usage
        # This would typically use a keyword analysis library
        # For now, we'll return a placeholder
        issues.append("Keyword analysis not implemented")
        
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
        
        # Check for proper image attributes
        images = soup.find_all("img")
        for img in images:
            if not img.get("alt"):
                issues.append("Image missing alt text")
            if not img.get("src"):
                issues.append("Image missing src attribute")
            if not img.get("width") or not img.get("height"):
                issues.append("Image missing width or height attributes")
        
        return {
            "score": max(100 - len(issues) * 10, 0),
            "issues": issues
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