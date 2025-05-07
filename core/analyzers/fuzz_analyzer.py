"""
Fuzz testing analyzer for UI components.
"""
import json
import random
import string
import asyncio
import os
from datetime import datetime
from typing import Dict, Any
from playwright.async_api import Page
from core.utils.error_handler import AnalysisError

class FuzzAnalyzer:
    """Analyzer for fuzz testing of UI components."""
    
    def _generate_fuzz_input(self, length: int = 10) -> str:
        """Generate random fuzz input."""
        return ''.join(random.choices(string.ascii_letters + string.digits + string.punctuation, k=length))
    
    def _save_results(self, url: str, results: Dict[str, Any]) -> str:
        """Save analysis results to a JSON file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"fuzz_{url.replace('://', '_').replace('/', '_')}_{timestamp}.json"
        output_dir = "analysis_results"
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        return filepath
    
    async def analyze(self, url: str, page: Page) -> str:
        """
        Analyze the page using fuzz testing.
        
        Args:
            url: The URL of the page to analyze
            page: Playwright page object
            
        Returns:
            JSON string containing analysis results
        """
        try:
            # Initialize results structure
            results = {
                "results": {
                    "overall_score": 0,
                    "executions": 0,
                    "crashes": 0,
                    "coverage": 0,
                    "metrics": {
                        "fuzz_score": 0,
                        "total_inputs": 0,
                        "execution_time": 0
                    }
                },
                "json_path": None
            }
            
            # Define fuzz test targets
            targets = [
                {"selector": "input[type='text']", "type": "text"},
                {"selector": "input[type='number']", "type": "number"},
                {"selector": "textarea", "type": "text"},
                {"selector": "form", "type": "submit"}
            ]
            
            executions = 0
            crashes = 0
            
            for target in targets:
                try:
                    # Set a timeout for each fuzz test
                    async with asyncio.timeout(2.0):  # 2 second timeout per test
                        # Generate and apply fuzz input
                        if target["type"] == "text":
                            fuzz_input = self._generate_fuzz_input()
                            await page.fill(target["selector"], fuzz_input)
                        elif target["type"] == "number":
                            fuzz_input = str(random.randint(-1000000, 1000000))
                            await page.fill(target["selector"], fuzz_input)
                        elif target["type"] == "submit":
                            await page.evaluate(f"document.querySelector('{target['selector']}').submit()")
                        
                        executions += 1
                        
                except asyncio.TimeoutError:
                    # Test timed out
                    crashes += 1
                except Exception:
                    crashes += 1
            
            # Calculate metrics
            total_inputs = len(targets)
            fuzz_score = ((executions - crashes) / executions) * 100 if executions > 0 else 0
            
            # Update results
            results["results"].update({
                "overall_score": fuzz_score,
                "executions": executions,
                "crashes": crashes,
                "coverage": (executions / total_inputs) * 100 if total_inputs > 0 else 0,
                "metrics": {
                    "fuzz_score": fuzz_score,
                    "total_inputs": total_inputs,
                    "execution_time": 0  # In a real implementation, measure actual execution time
                }
            })
            
            # Save results to file
            results["json_path"] = self._save_results(url, results)
            
            return json.dumps(results)
            
        except Exception as e:
            raise AnalysisError(f"Fuzz analysis failed: {str(e)}")