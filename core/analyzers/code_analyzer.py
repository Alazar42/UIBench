from typing import Dict, Any
from bs4 import BeautifulSoup
import tinycss2
from io import StringIO
import pylint.lint
from pylint.reporters.text import TextReporter
from ..utils.error_handler import AnalysisError

class CodeAnalyzer:
    """Analyzes web pages for code quality and best practices."""
    
    async def analyze(self, html: str, soup: BeautifulSoup) -> Dict[str, Any]:
        """
        Perform comprehensive code analysis.
        
        Args:
            html: Raw HTML content
            soup: BeautifulSoup parsed HTML
            
        Returns:
            Dict containing code analysis results
        """
        try:
            results = {
                "html_quality": self._analyze_html_quality(html, soup),
                "css_quality": self._analyze_css_quality(soup),
                "javascript_quality": self._analyze_javascript_quality(soup),
                "code_optimization": self._analyze_code_optimization(soup),
                "best_practices": self._analyze_best_practices(soup)
            }
            
            # Calculate overall code quality score
            scores = [result.get("score", 0) for result in results.values() if isinstance(result, dict)]
            results["overall_score"] = sum(scores) / len(scores) if scores else 0
            
            return results
        except Exception as e:
            raise AnalysisError(f"Code analysis failed: {str(e)}")
    
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