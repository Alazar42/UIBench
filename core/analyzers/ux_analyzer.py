from typing import Dict, Any
from playwright.async_api import Page
from bs4 import BeautifulSoup
from ..utils.error_handler import AnalysisError

class UXAnalyzer:
    """Analyzes web pages for user experience and usability."""
    
    async def analyze(self, page: Page, soup: BeautifulSoup) -> Dict[str, Any]:
        """
        Perform comprehensive UX analysis.
        
        Args:
            page: Playwright page object
            soup: BeautifulSoup parsed HTML
            
        Returns:
            Dict containing UX analysis results
        """
        try:
            results = {
                "navigation": await self._check_navigation(page, soup),
                "content_readability": self._check_content_readability(soup),
                "form_usability": await self._check_form_usability(page),
                "mobile_responsiveness": await self._check_mobile_responsiveness(page),
                "interaction_design": await self._check_interaction_design(page),
                "visual_hierarchy": self._check_visual_hierarchy(soup)
            }
            
            # Calculate overall UX score
            scores = [result.get("score", 0) for result in results.values() if isinstance(result, dict)]
            results["overall_score"] = sum(scores) / len(scores) if scores else 0
            
            return results
        except Exception as e:
            raise AnalysisError(f"UX analysis failed: {str(e)}")
    
    async def _check_navigation(self, page: Page, soup: BeautifulSoup) -> Dict[str, Any]:
        """Check navigation structure and usability."""
        issues = []
        
        # Check for navigation menu
        nav = soup.find("nav")
        if not nav:
            issues.append("Missing navigation menu")
        
        # Check for breadcrumbs
        breadcrumbs = soup.find(class_="breadcrumbs")
        if not breadcrumbs:
            issues.append("Missing breadcrumbs")
        
        # Check for skip links
        skip_links = soup.find("a", {"href": "#main-content"})
        if not skip_links:
            issues.append("Missing skip to main content link")
        
        # Check for proper link text
        links = soup.find_all("a")
        for link in links:
            if not link.text.strip() and not link.find("img"):
                issues.append("Link missing descriptive text")
        
        return {
            "score": max(100 - len(issues) * 20, 0),
            "issues": issues
        }
    
    def _check_content_readability(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Check content readability and structure."""
        issues = []
        
        # Check for proper heading hierarchy
        headings = soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
        if not any(h.name == "h1" for h in headings):
            issues.append("Missing H1 heading")
        
        # Check for proper paragraph length
        paragraphs = soup.find_all("p")
        for p in paragraphs:
            if len(p.text.split()) > 100:
                issues.append("Paragraph too long")
        
        # Check for proper list usage
        lists = soup.find_all(["ul", "ol"])
        for lst in lists:
            if len(lst.find_all("li")) > 10:
                issues.append("List too long")
        
        return {
            "score": max(100 - len(issues) * 10, 0),
            "issues": issues
        }
    
    async def _check_form_usability(self, page: Page) -> Dict[str, Any]:
        """Check form usability and accessibility."""
        issues = []
        
        # Check form inputs
        forms = await page.query_selector_all("form")
        for form in forms:
            inputs = await form.query_selector_all("input, textarea")
            for input in inputs:
                # Check for proper labels
                if not await input.get_attribute("aria-label"):
                    issues.append("Input missing aria-label")
                
                # Check for proper error handling
                if not await form.query_selector(".error-message"):
                    issues.append("Form missing error message container")
        
        return {
            "score": max(100 - len(issues) * 10, 0),
            "issues": issues
        }
    
    async def _check_mobile_responsiveness(self, page: Page) -> Dict[str, Any]:
        """Check mobile responsiveness and touch targets."""
        issues = []
        
        # Set mobile viewport
        await page.set_viewport_size({"width": 375, "height": 667})
        
        # Check for proper viewport meta tag
        viewport = await page.query_selector('meta[name="viewport"]')
        if not viewport:
            issues.append("Missing viewport meta tag")
        
        # Check for touch targets
        touch_targets = await page.query_selector_all("a, button, input, select")
        for target in touch_targets:
            box = await target.bounding_box()
            if box and (box["width"] < 44 or box["height"] < 44):
                issues.append("Touch target too small")
        
        return {
            "score": max(100 - len(issues) * 20, 0),
            "issues": issues
        }
    
    async def _check_interaction_design(self, page: Page) -> Dict[str, Any]:
        """Check interaction design and feedback."""
        issues = []
        
        # Check for hover states
        elements = await page.query_selector_all("a, button")
        for element in elements:
            if not await element.evaluate("el => getComputedStyle(el).cursor === 'pointer'"):
                issues.append("Interactive element missing hover state")
        
        # Check for loading states
        if not await page.query_selector(".loading-indicator"):
            issues.append("Missing loading indicator")
        
        # Check for proper feedback
        if not await page.query_selector(".feedback-message"):
            issues.append("Missing feedback message container")
        
        return {
            "score": max(100 - len(issues) * 20, 0),
            "issues": issues
        }
    
    def _check_visual_hierarchy(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Check visual hierarchy and design consistency."""
        issues = []
        
        # Check for consistent heading styles
        headings = soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
        for heading in headings:
            if not heading.get("class"):
                issues.append(f"{heading.name} missing style class")
        
        # Check for proper spacing
        elements = soup.find_all(["p", "div", "section"])
        for element in elements:
            if not element.get("class") and not element.get("style"):
                issues.append("Element missing spacing class")
        
        # Check for proper color contrast
        # This would typically use a color contrast checking library
        # For now, we'll return a placeholder
        issues.append("Color contrast check not implemented")
        
        return {
            "score": max(100 - len(issues) * 10, 0),
            "issues": issues
        } 