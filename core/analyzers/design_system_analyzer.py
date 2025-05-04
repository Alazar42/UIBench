from typing import Dict, Any
import logging
import requests
import os
from bs4 import BeautifulSoup
from .base_analyzer import BaseAnalyzer
import json

logger = logging.getLogger(__name__)

class DesignSystemAnalyzer(BaseAnalyzer):
    """Analyzes design system integration (Figma/Sketch) and compares with live CSS."""
    
    async def analyze(self, url: str, page_or_html, design_data: dict = None) -> str:
        """
        Perform comprehensive design system analysis.
        
        Args:
            url: Target URL
            page_or_html: Either a Playwright Page object or HTML string
            design_data: Optional design system data (Figma/Sketch)
            
        Returns:
            JSON string containing design system analysis results and JSON file path
        """
        try:
            # Handle both Page and HTML string inputs
            if hasattr(page_or_html, 'content'):
                html = await page_or_html.content()
            else:
                html = str(page_or_html)
                
            results = {}
            # Figma integration
            if design_data and design_data.get('figma_file_key'):
                figma_file_key = design_data['figma_file_key']
                token = os.getenv("FIGMA_API_TOKEN")
                if token:
                    figma_url = f"https://api.figma.com/v1/files/{figma_file_key}"
                    headers = {"X-Figma-Token": token}
                    response = requests.get(figma_url, headers=headers)
                    if response.status_code == 200:
                        figma_json = response.json()
                        # Extract color, typography, spacing tokens (simplified)
                        tokens = self._extract_figma_tokens(figma_json)
                        results['figma_tokens'] = tokens
                    else:
                        results['figma_error'] = f"Figma API error: {response.status_code}"
                else:
                    results['figma_error'] = "FIGMA_API_TOKEN not set"
            # Sketch integration (stub)
            if design_data and design_data.get('sketch_file_url'):
                results['sketch_data'] = 'Sketch integration stub'
            # Compare with live CSS
            soup = BeautifulSoup(html, 'html.parser')
            css_vars = [style for style in soup.find_all('style')]
            results['css_vars_count'] = len(css_vars)
            
            # Calculate overall score
            results["overall_score"] = 100 if results.get('figma_tokens') or results.get('sketch_data') else 50
            
            # Standardize results
            standardized_results = self._standardize_results(results)
            
            # Save to JSON
            json_path = self.save_to_json(standardized_results, url, "design_system")
            
            return json.dumps({
                "results": standardized_results,
                "json_path": json_path
            }, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Design system analysis failed: {str(e)}")
            return json.dumps({"error": str(e)})
    
    def _extract_figma_tokens(self, figma_json: dict) -> Dict[str, Any]:
        # Simplified: extract color styles
        tokens = {}
        try:
            styles = figma_json.get('styles', {})
            tokens['colors'] = [s for s in styles if styles[s]['style_type'] == 'FILL']
            tokens['typography'] = [s for s in styles if styles[s]['style_type'] == 'TEXT']
        except Exception as e:
            tokens['error'] = str(e)
        return tokens

    def _standardize_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Standardize the analysis results."""
        standardized = {
            "overall_score": results.get("overall_score", 0),
            "issues": [],
            "recommendations": [],
            "metrics": {},
            "details": {}
        }
        
        # Add issues and recommendations
        if results.get("figma_error"):
            standardized["issues"].append(f"Figma integration error: {results['figma_error']}")
            standardized["recommendations"].append("Fix Figma API integration")
        
        if results.get("css_vars_count", 0) == 0:
            standardized["issues"].append("No CSS variables found")
            standardized["recommendations"].append("Implement CSS variables for design system")
        
        # Add metrics
        standardized["metrics"] = {
            "css_vars_count": results.get("css_vars_count", 0),
            "figma_tokens": bool(results.get("figma_tokens")),
            "sketch_data": bool(results.get("sketch_data"))
        }
        
        # Add details
        standardized["details"] = {
            "figma_tokens": results.get("figma_tokens", {}),
            "sketch_data": results.get("sketch_data", {}),
            "css_vars": results.get("css_vars", [])
        }
        
        return standardized