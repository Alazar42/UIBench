"""
Operational metrics analyzer for evaluating system performance.
"""
import json
import os
from datetime import datetime
from typing import Dict, Any
from playwright.async_api import Page
from .operational_metrics_checks import OperationalMetricsChecks
import logging
from core.utils.error_handler import AnalysisError

logger = logging.getLogger(__name__)

class OperationalMetricsAnalyzer:
    """Analyzer for operational metrics evaluation."""
    
    def _save_results(self, url: str, results: Dict[str, Any]) -> str:
        """Save analysis results to a JSON file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"operational_metrics_{url.replace('://', '_').replace('/', '_')}_{timestamp}.json"
        output_dir = "analysis_results"
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        return filepath
    
    async def analyze(self, url: str, page: Page, soup=None) -> str:
        """
        Analyze the page for operational metrics.
        
        Args:
            url: The URL of the page to analyze
            page: Playwright page object
            soup: Optional BeautifulSoup object (not used)
            
        Returns:
            JSON string containing analysis results
        """
        try:
            results = {
                "uptime_monitoring": await OperationalMetricsChecks.check_uptime_monitoring(page),
                "error_budgets": await OperationalMetricsChecks.check_error_budgets(page),
                "deployment_frequency": await OperationalMetricsChecks.check_deployment_frequency(page),
                "mttr": await OperationalMetricsChecks.check_mttr(page),
                "performance_budgets": await OperationalMetricsChecks.check_performance_budgets(page),
                "audit_trails": await OperationalMetricsChecks.check_audit_trails(page)
            }
            
            # Calculate overall score
            scores = [result.get("score", 0) for result in results.values() if isinstance(result, dict)]
            overall_score = sum(scores) / len(scores) if scores else 0
            
            # Collect issues and recommendations
            issues = []
            recommendations = []
            for check_name, result in results.items():
                if isinstance(result, dict):
                    issues.extend(result.get("issues", []))
                    recommendations.extend(result.get("recommendations", []))
            
            # Standardize results
            standardized_results = {
                "overall_score": overall_score,
                "issues": issues,
                "recommendations": recommendations,
                "metrics": {
                    "execution_time": 0,  # TODO: Add actual execution time
                    "operational_score": overall_score,
                    "total_checks": len(results)
                },
                "details": results
            }
            
            # Save results to file
            json_path = self._save_results(url, standardized_results)
            
            # Return results with json_path at root level
            return json.dumps({
                "json_path": json_path,
                "results": standardized_results
            })
            
        except Exception as e:
            logger.error(f"Operational metrics analysis failed: {str(e)}")
            return json.dumps({
                "json_path": "",
                "results": {
                    "overall_score": 0,
                    "issues": [f"Analysis failed: {str(e)}"],
                    "recommendations": ["Fix operational metrics analysis"],
                    "metrics": {
                        "execution_time": 0,
                        "operational_score": 0,
                        "total_checks": 0
                    },
                    "details": {}
                }
            })