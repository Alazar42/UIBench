from typing import Dict, Any
from bs4 import BeautifulSoup
import tinycss2
from io import StringIO
import pylint.lint
import json
from pylint.reporters.text import TextReporter
from ..utils.error_handler import AnalysisError
from .base_analyzer import BaseAnalyzer

class CodeAnalyzer(BaseAnalyzer):
    """Analyzes web pages for code quality and best practices."""
    
    async def analyze(self, url: str, html: str) -> str:
        """
        Perform comprehensive code analysis.
        Returns:
            JSON string containing code analysis results and JSON file path
        """
        try:
            # Parse the HTML content with BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")

            # Run all code analysis checks
            code_checks = {
                "html_quality": self._analyze_html_quality(html, soup),
                "css_quality": self._analyze_css_quality(soup),
                "javascript_quality": self._analyze_javascript_quality(soup),
                "code_optimization": self._analyze_code_optimization(soup),
                "best_practices": self._analyze_best_practices(soup),
                "semantic_html": self._analyze_semantic_html(soup),
                "responsive_design": self._analyze_responsive_design(soup),
                "performance_optimization": self._analyze_performance_optimization(soup)
            }

            # Calculate overall score
            scores = [result.get("score", 0) for result in code_checks.values() if isinstance(result, dict)]
            overall_score = sum(scores) / len(scores) if scores else 0

            # Collect all issues and recommendations
            all_issues = []
            all_recommendations = []
            metrics = {}

            for check_name, result in code_checks.items():
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
                "details": code_checks
            }

            # Save to JSON
            json_path = self.save_to_json(standardized_results, url, "code")

            return json.dumps({
                "results": {
                    "overall_score": overall_score,
                    "issues": all_issues,
                    "recommendations": all_recommendations,
                    "metrics": metrics
                },
                "json_path": "analysis_results/codeanalyzer_{}_{}.json".format(urlparse(url).netloc, datetime.now().strftime("%Y%m%d_%H%M%S"))
            })
        except Exception as e:
            return json.dumps({
                "error": f"Code analysis failed: {str(e)}",
                "status": "failed",
                "overall_score": 0.0,
                "details": {},
                "issues": [f"Analysis failed: {str(e)}"],
                "recommendations": ["Fix analyzer implementation"],
                "metrics": {}
            })
    
    def _analyze_html_quality(self, html: str, soup: BeautifulSoup) -> Dict[str, Any]:
        """Analyze HTML code quality."""
        issues = []
        
        # Check for deprecated tags
        deprecated_tags = {'center', 'font', 'strike', 'tt'}
        found_deprecated = [tag.name for tag in soup.find_all(deprecated_tags)]
        if found_deprecated:
            issues.append(f"Deprecated HTML tags found: {', '.join(found_deprecated)}")
        
        # Check for proper HTML structure
        if not soup.find("html"):
            issues.append("Missing HTML root element")
        if not soup.find("head"):
            issues.append("Missing head element")
        if not soup.find("body"):
            issues.append("Missing body element")
        
        # Check for proper DOCTYPE
        if not html.strip().startswith("<!DOCTYPE"):
            issues.append("Missing DOCTYPE declaration")
        
        # Check for proper character encoding
        if not soup.find("meta", {"charset": True}):
            issues.append("Missing character encoding declaration")
        
        return {
            "score": max(100 - len(issues) * 10, 0),
            "issues": issues
        }
    
    def _analyze_css_quality(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Analyze CSS code quality."""
        issues = []
        
        # Get all CSS content
        styles = soup.find_all("style")
        links = soup.find_all("link", rel="stylesheet")
        
        for style in styles:
            try:
                if style.string:
                    rules = tinycss2.parse_stylesheet(style.string)
                    for rule in rules:
                        if rule.type == 'qualified-rule':
                            # Check declarations within the rule
                            declarations = tinycss2.parse_declaration_list(rule.content)
                            for decl in declarations:
                                if decl.type == 'declaration':
                                    # Check for vendor prefixes
                                    if decl.name.startswith('-'):
                                        issues.append(f"Vendor prefix detected: {decl.name}")
                                    
                                    # Check for !important
                                    if decl.important:
                                        issues.append("Use of !important detected")
                                    
                                    # Check for proper units in specific properties
                                    if decl.name in ['width', 'height', 'margin', 'padding']:
                                        value_str = tinycss2.serialize(decl.value)
                                        if not any(unit in value_str for unit in ['px', 'em', 'rem', '%']):
                                            issues.append(f"Invalid unit in {decl.name}: {value_str}")
            except Exception as e:
                issues.append(f"CSS parsing error: {str(e)}")
        
        return {
            "score": max(100 - len(issues) * 5, 0),
            "issues": issues
        }
    
    def _analyze_javascript_quality(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Analyze JavaScript code quality."""
        issues = []
        
        # Get all JavaScript content
        scripts = soup.find_all("script")
        
        for script in scripts:
            if script.string:
                # Check for common issues
                if "eval(" in script.string:
                    issues.append("Use of eval() detected")
                if "document.write" in script.string:
                    issues.append("Use of document.write() detected")
                if "innerHTML" in script.string:
                    issues.append("Use of innerHTML detected")
        
        # Check for proper script loading
        for script in scripts:
            if script.get("src"):
                if not script.get("async") and not script.get("defer"):
                    issues.append("Script missing async or defer attribute")
        
        return {
            "score": max(100 - len(issues) * 10, 0),
            "issues": issues
        }
    
    def _analyze_code_optimization(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Analyze code optimization."""
        issues = []
        
        # Check for minified resources
        scripts = soup.find_all("script", src=True)
        styles = soup.find_all("link", rel="stylesheet")
        
        for script in scripts:
            if not ".min" in script["src"]:
                issues.append(f"Unminified script: {script['src']}")
        
        for style in styles:
            if not ".min" in style["href"]:
                issues.append(f"Unminified stylesheet: {style['href']}")
        
        # Check for proper resource loading
        for script in scripts:
            if not script.get("async") and not script.get("defer"):
                issues.append(f"Script missing async/defer: {script['src']}")
        
        return {
            "score": max(100 - len(issues) * 10, 0),
            "issues": issues
        }
    
    def _analyze_best_practices(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Analyze code best practices."""
        issues = []
        
        # Check for proper meta tags
        if not soup.find("meta", {"name": "viewport"}):
            issues.append("Missing viewport meta tag")
        if not soup.find("meta", {"name": "description"}):
            issues.append("Missing description meta tag")
        
        # Check for proper favicon
        if not soup.find("link", rel="icon"):
            issues.append("Missing favicon")
        
        # Check for proper language attribute
        if not soup.find("html").get("lang"):
            issues.append("Missing language attribute")
        
        # Check for proper ARIA attributes
        interactive_elements = soup.find_all(["button", "a", "input", "select", "textarea"])
        for element in interactive_elements:
            if not element.get("aria-label") and not element.get("aria-labelledby"):
                issues.append(f"Interactive element missing ARIA label: {element.name}")
        
        return {
            "score": max(100 - len(issues) * 10, 0),
            "issues": issues
        }

    def _analyze_semantic_html(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Analyze semantic HTML usage."""
        issues = []
        recommendations = []
        
        # Check for semantic HTML elements
        semantic_elements = ['header', 'nav', 'main', 'article', 'section', 'aside', 'footer']
        for element in semantic_elements:
            if not soup.find(element):
                recommendations.append(f"Consider using <{element}> element for better semantics")
        
        # Check for proper heading hierarchy
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        if not any(h.name == 'h1' for h in headings):
            issues.append("Missing H1 heading")
        
        # Check for proper list usage
        if soup.find('ul') and not soup.find('li'):
            issues.append("Unordered list without list items")
        if soup.find('ol') and not soup.find('li'):
            issues.append("Ordered list without list items")
        
        return {
            "score": max(100 - len(issues) * 10, 0),
            "issues": issues,
            "recommendations": recommendations
        }

    def _analyze_responsive_design(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Analyze responsive design implementation."""
        issues = []
        recommendations = []
        
        # Check for viewport meta tag
        if not soup.find('meta', {'name': 'viewport'}):
            issues.append("Missing viewport meta tag")
        
        # Check for responsive images
        images = soup.find_all('img')
        for img in images:
            if not img.get('srcset') and not img.get('sizes'):
                recommendations.append(f"Consider adding srcset and sizes attributes to image: {img.get('src', '')}")
        
        # Check for media queries
        styles = soup.find_all('style')
        has_media_queries = any('@media' in style.string for style in styles if style.string)
        if not has_media_queries:
            recommendations.append("Consider adding media queries for responsive design")
        
        return {
            "score": max(100 - len(issues) * 10, 0),
            "issues": issues,
            "recommendations": recommendations
        }

    def _analyze_performance_optimization(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Analyze performance optimization."""
        issues = []
        recommendations = []
        
        # Check for resource optimization
        scripts = soup.find_all('script', src=True)
        styles = soup.find_all('link', rel='stylesheet')
        
        for script in scripts:
            if not script.get('async') and not script.get('defer'):
                recommendations.append(f"Consider adding async or defer to script: {script['src']}")
        
        for style in styles:
            if not style.get('media'):
                recommendations.append(f"Consider adding media attribute to stylesheet: {style['href']}")
        
        # Check for image optimization
        images = soup.find_all('img')
        for img in images:
            if not img.get('loading') == 'lazy':
                recommendations.append(f"Consider adding loading='lazy' to image: {img.get('src', '')}")
        
        return {
            "score": max(100 - len(issues) * 10, 0),
            "issues": issues,
            "recommendations": recommendations
        }