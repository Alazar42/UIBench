from typing import Dict, Any
from playwright.async_api import Page
from bs4 import BeautifulSoup
from ..utils.error_handler import AnalysisError
from .base_analyzer import BaseAnalyzer
import json
import logging
import asyncio

logger = logging.getLogger(__name__)

class UXAnalyzer(BaseAnalyzer):
    """Analyzes web pages for user experience and usability."""
    
    def __init__(self):
        super().__init__()
    
    async def analyze(self, url: str, page: Page, soup: BeautifulSoup) -> str:
        """
        Perform UX analysis.
        
        Args:
            url: Target URL
            page: Playwright page object
            soup: BeautifulSoup parsed HTML
            
        Returns:
            JSON string containing UX analysis results and JSON file path
        """
        try:
            # Run async checks concurrently
            async_results = await asyncio.gather(
                self._check_navigation(page),
                self._check_interaction_elements(page),
                self._check_feedback_mechanisms(page),
                self._check_error_handling(page),
                self._check_mobile_responsiveness(page),
                self._check_loading_states(page)
            )
            
            # Run sync checks
            sync_results = [
                self._check_visual_hierarchy(soup),
                self._check_consistency(soup),
                self._check_typography(soup),
                self._check_color_contrast(soup)
            ]
            
            # Combine all results
            combined_results = {
                "navigation": async_results[0],
                "interaction_elements": async_results[1],
                "feedback_mechanisms": async_results[2],
                "error_handling": async_results[3],
                "mobile_responsiveness": async_results[4],
                "loading_states": async_results[5],
                "visual_hierarchy": sync_results[0],
                "consistency": sync_results[1],
                "typography": sync_results[2],
                "color_contrast": sync_results[3]
            }
            
            # Calculate overall score
            scores = [result.get("score", 0) for result in combined_results.values()]
            combined_results["overall_score"] = sum(scores) / len(scores) if scores else 0
            
            # Standardize results
            standardized_results = self._standardize_results(combined_results)
            
            # Save to JSON
            json_path = self.save_to_json(standardized_results, url, "ux")
            
            return json.dumps({
                "results": standardized_results,
                "json_path": json_path
            }, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"UX analysis failed: {str(e)}")
            raise AnalysisError(f"UX analysis failed: {str(e)}")
    
    async def _check_navigation(self, page: Page) -> Dict[str, Any]:
        """Check navigation structure and usability."""
        try:
            # Check for main navigation
            nav_elements = await page.query_selector_all('nav, [role="navigation"]')
            has_main_nav = len(nav_elements) > 0
            
            # Check for breadcrumbs
            breadcrumbs = await page.query_selector_all('[class*="breadcrumb"], [aria-label*="breadcrumb"]')
            has_breadcrumbs = len(breadcrumbs) > 0
            
            # Check for search functionality
            search = await page.query_selector('input[type="search"], [role="search"]')
            has_search = search is not None
            
            return {
                "score": 1.0 if has_main_nav and (has_breadcrumbs or has_search) else 0.5,
                "issues": [] if has_main_nav and (has_breadcrumbs or has_search) else ["Navigation structure needs improvement"],
                "recommendations": [] if has_main_nav and (has_breadcrumbs or has_search) else ["Improve navigation structure"],
                "details": {
                    "has_main_nav": has_main_nav,
                    "has_breadcrumbs": has_breadcrumbs,
                    "has_search": has_search
                }
            }
        except Exception as e:
            logger.error(f"Error checking navigation: {str(e)}")
            return {
                "score": 0,
                "issues": [f"Error checking navigation: {str(e)}"],
                "recommendations": ["Fix navigation analysis"],
                "details": {"error": str(e)}
            }
    
    def _check_visual_hierarchy(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Check visual hierarchy and content structure."""
        try:
            # Check heading structure
            headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            heading_levels = [int(h.name[1]) for h in headings]
            has_proper_hierarchy = all(heading_levels[i] <= heading_levels[i-1] + 1 for i in range(1, len(heading_levels)))
            
            # Check for visual separation
            sections = len(soup.find_all(['section', 'article', 'main']))
            
            return {
                "score": 1.0 if has_proper_hierarchy and sections > 0 else 0.5,
                "issues": [] if has_proper_hierarchy and sections > 0 else ["Visual hierarchy needs improvement"],
                "recommendations": [] if has_proper_hierarchy and sections > 0 else ["Improve visual hierarchy"],
                "details": {
                    "has_proper_hierarchy": has_proper_hierarchy,
                    "sections_count": sections
                }
            }
        except Exception as e:
            logger.error(f"Error checking visual hierarchy: {str(e)}")
            return {
                "score": 0,
                "issues": [f"Error checking visual hierarchy: {str(e)}"],
                "recommendations": ["Fix visual hierarchy analysis"],
                "details": {"error": str(e)}
            }
    
    async def _check_interaction_elements(self, page: Page) -> Dict[str, Any]:
        """Check interactive elements usability."""
        try:
            # Check button states
            buttons = await page.query_selector_all('button, [role="button"]')
            has_hover_states = all(await button.evaluate('(el) => window.getComputedStyle(el).getPropertyValue("transition")') for button in buttons)
            
            # Check form elements
            form_elements = await page.query_selector_all('input, select, textarea')
            has_labels = all(await element.evaluate('(el) => el.labels.length > 0 || el.getAttribute("aria-label")') for element in form_elements)
            
            return {
                "score": 1.0 if has_hover_states and has_labels else 0.5,
                "issues": [] if has_hover_states and has_labels else ["Interactive elements need improvement"],
                "recommendations": [] if has_hover_states and has_labels else ["Improve interactive elements"],
                "details": {
                    "has_hover_states": has_hover_states,
                    "has_labels": has_labels
                }
            }
        except Exception as e:
            logger.error(f"Error checking interaction elements: {str(e)}")
            return {
                "score": 0,
                "issues": [f"Error checking interaction elements: {str(e)}"],
                "recommendations": ["Fix interaction elements analysis"],
                "details": {"error": str(e)}
            }
    
    def _check_consistency(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Check design consistency."""
        try:
            # Check for consistent styling
            buttons = soup.find_all('button')
            inputs = soup.find_all('input')
            
            # Convert to tuples to make them hashable
            button_classes = set(tuple(button.get('class', [])) for button in buttons)
            input_types = set(input.get('type', 'text') for input in inputs)
            
            is_consistent = len(button_classes) <= 2 and len(input_types) <= 3
            
            return {
                "score": 1.0 if is_consistent else 0.5,
                "issues": [] if is_consistent else ["Design consistency needs improvement"],
                "recommendations": [] if is_consistent else ["Improve design consistency"],
                "details": {
                    "button_variations": len(button_classes),
                    "input_variations": len(input_types)
                }
            }
        except Exception as e:
            logger.error(f"Error checking consistency: {str(e)}")
            return {
                "score": 0,
                "issues": [f"Error checking consistency: {str(e)}"],
                "recommendations": ["Fix consistency analysis"],
                "details": {"error": str(e)}
            }
    
    async def _check_feedback_mechanisms(self, page: Page) -> Dict[str, Any]:
        """Check user feedback mechanisms."""
        try:
            # Check for loading indicators
            loading_indicators = await page.query_selector_all('[class*="loading"], [class*="spinner"]')
            
            # Check for success/error messages
            feedback_messages = await page.query_selector_all('[class*="alert"], [class*="message"], [role="alert"]')
            
            return {
                "score": 1.0 if len(loading_indicators) > 0 and len(feedback_messages) > 0 else 0.5,
                "issues": [] if len(loading_indicators) > 0 and len(feedback_messages) > 0 else ["Feedback mechanisms need improvement"],
                "recommendations": [] if len(loading_indicators) > 0 and len(feedback_messages) > 0 else ["Improve feedback mechanisms"],
                "details": {
                    "loading_indicators": len(loading_indicators),
                    "feedback_messages": len(feedback_messages)
                }
            }
        except Exception as e:
            logger.error(f"Error checking feedback mechanisms: {str(e)}")
            return {
                "score": 0,
                "issues": [f"Error checking feedback mechanisms: {str(e)}"],
                "recommendations": ["Fix feedback mechanisms analysis"],
                "details": {"error": str(e)}
            }
    
    async def _check_error_handling(self, page: Page) -> Dict[str, Any]:
        """Check error handling and recovery."""
        try:
            # Check for form validation
            forms = await page.query_selector_all('form')
            has_validation = all(await form.evaluate('(f) => f.checkValidity !== undefined') for form in forms)
            
            # Check for error messages
            error_messages = await page.query_selector_all('[class*="error"], [class*="invalid"]')
            
            return {
                "score": 1.0 if has_validation and len(error_messages) > 0 else 0.5,
                "issues": [] if has_validation and len(error_messages) > 0 else ["Error handling needs improvement"],
                "recommendations": [] if has_validation and len(error_messages) > 0 else ["Improve error handling"],
                "details": {
                    "has_validation": has_validation,
                    "error_messages": len(error_messages)
                }
            }
        except Exception as e:
            logger.error(f"Error checking error handling: {str(e)}")
            return {
                "score": 0,
                "issues": [f"Error checking error handling: {str(e)}"],
                "recommendations": ["Fix error handling analysis"],
                "details": {"error": str(e)}
            }
    
    async def _check_mobile_responsiveness(self, page: Page) -> Dict[str, Any]:
        """Check mobile responsiveness."""
        try:
            # Set mobile viewport
            await page.set_viewport_size({"width": 375, "height": 667})
            
            # Check for responsive elements
            responsive_elements = await page.query_selector_all('[class*="responsive"], [class*="mobile"]')
            
            # Check for viewport meta tag
            viewport_meta = await page.query_selector('meta[name="viewport"]')
            
            return {
                "score": 1.0 if len(responsive_elements) > 0 and viewport_meta else 0.5,
                "issues": [] if len(responsive_elements) > 0 and viewport_meta else ["Mobile responsiveness needs improvement"],
                "recommendations": [] if len(responsive_elements) > 0 and viewport_meta else ["Improve mobile responsiveness"],
                "details": {
                    "responsive_elements": len(responsive_elements),
                    "has_viewport_meta": bool(viewport_meta)
                }
            }
        except Exception as e:
            logger.error(f"Error checking mobile responsiveness: {str(e)}")
            return {
                "score": 0,
                "issues": [f"Error checking mobile responsiveness: {str(e)}"],
                "recommendations": ["Fix mobile responsiveness analysis"],
                "details": {"error": str(e)}
            }
    
    async def _check_loading_states(self, page: Page) -> Dict[str, Any]:
        """Check loading states and transitions."""
        try:
            # Check for loading indicators
            loading_indicators = await page.query_selector_all('[class*="loading"], [class*="spinner"]')
            
            # Check for skeleton loaders
            skeleton_loaders = await page.query_selector_all('[class*="skeleton"]')
            
            return {
                "score": 1.0 if len(loading_indicators) > 0 or len(skeleton_loaders) > 0 else 0.5,
                "issues": [] if len(loading_indicators) > 0 or len(skeleton_loaders) > 0 else ["Loading states need improvement"],
                "recommendations": [] if len(loading_indicators) > 0 or len(skeleton_loaders) > 0 else ["Improve loading states"],
                "details": {
                    "loading_indicators": len(loading_indicators),
                    "skeleton_loaders": len(skeleton_loaders)
                }
            }
        except Exception as e:
            logger.error(f"Error checking loading states: {str(e)}")
            return {
                "score": 0,
                "issues": [f"Error checking loading states: {str(e)}"],
                "recommendations": ["Fix loading states analysis"],
                "details": {"error": str(e)}
            }
    
    def _check_typography(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Check typography and readability."""
        try:
            # Check font sizes
            text_elements = soup.find_all(['p', 'span', 'div'])
            font_sizes = set(element.get('style', '').split('font-size:')[1].split(';')[0] for element in text_elements if 'font-size:' in element.get('style', ''))
            
            # Check line heights
            line_heights = set(element.get('style', '').split('line-height:')[1].split(';')[0] for element in text_elements if 'line-height:' in element.get('style', ''))
            
            return {
                "score": 1.0 if len(font_sizes) <= 3 and len(line_heights) <= 2 else 0.5,
                "issues": [] if len(font_sizes) <= 3 and len(line_heights) <= 2 else ["Typography needs improvement"],
                "recommendations": [] if len(font_sizes) <= 3 and len(line_heights) <= 2 else ["Improve typography consistency"],
                "details": {
                    "font_size_variations": len(font_sizes),
                    "line_height_variations": len(line_heights)
                }
            }
        except Exception as e:
            logger.error(f"Error checking typography: {str(e)}")
            return {
                "score": 0,
                "issues": [f"Error checking typography: {str(e)}"],
                "recommendations": ["Fix typography analysis"],
                "details": {"error": str(e)}
            }
    
    def _check_color_contrast(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Check color contrast and accessibility."""
        try:
            # Check for color contrast issues
            text_elements = soup.find_all(['p', 'span', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            has_contrast_issues = any(
                'color:' in element.get('style', '') and 
                'background-color:' in element.get('style', '') 
                for element in text_elements
            )
            
            return {
                "score": 1.0 if not has_contrast_issues else 0.5,
                "issues": [] if not has_contrast_issues else ["Color contrast needs improvement"],
                "recommendations": [] if not has_contrast_issues else ["Improve color contrast"],
                "details": {
                    "has_contrast_issues": has_contrast_issues
                }
            }
        except Exception as e:
            logger.error(f"Error checking color contrast: {str(e)}")
            return {
                "score": 0,
                "issues": [f"Error checking color contrast: {str(e)}"],
                "recommendations": ["Fix color contrast analysis"],
                "details": {"error": str(e)}
            }
    
    def _standardize_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Standardize the analysis results."""
        standardized = {
            "overall_score": results.get("overall_score", 0),
            "issues": [],
            "recommendations": [],
            "metrics": {},
            "details": {}
        }
        
        for key, result in results.items():
            if isinstance(result, dict):
                standardized["issues"].extend(result.get("issues", []))
                standardized["recommendations"].extend(result.get("recommendations", []))
                standardized["metrics"][key] = {
                    "score": result.get("score", 0),
                    "details": result.get("details", {})
                }
                standardized["details"][key] = result
        
        return standardized
    
    def save_to_json(self, results: Dict[str, Any], url: str, analysis_type: str) -> str:
        """Save analysis results to a JSON file."""
        try:
            # Create filename from URL and analysis type
            filename = f"{url.replace('https://', '').replace('http://', '').replace('/', '_')}_{analysis_type}.json"
            
            # Save to file
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            return filename
        except Exception as e:
            logger.error(f"Error saving results to JSON: {str(e)}")
            return ""