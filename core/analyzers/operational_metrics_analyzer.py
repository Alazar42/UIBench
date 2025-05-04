from typing import Dict, Any
from playwright.async_api import Page
from .operational_metrics_checks import OperationalMetricsChecks
import logging
import json

logger = logging.getLogger(__name__)

class OperationalMetricsAnalyzer:
    """Analyzes web pages for operational metrics (uptime, error budgets, deployment, MTTR, etc.)."""
    async def analyze(self, url: str, page: Page, soup=None) -> str:
        """
        Analyze operational metrics for a web page.
        
        Args:
            url: Target URL
            page: Playwright page object
            soup: Optional BeautifulSoup object (not used)
            
        Returns:
            JSON string containing operational metrics analysis results
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
            
            # Standardize results
            standardized_results = {
                "overall_score": overall_score,
                "issues": [],
                "recommendations": [],
                "metrics": {},
                "details": results
            }
            
            # Aggregate issues and recommendations
            for check_name, check_result in results.items():
                if isinstance(check_result, dict):
                    standardized_results["issues"].extend(check_result.get("issues", []))
                    standardized_results["recommendations"].extend(check_result.get("recommendations", []))
                    standardized_results["metrics"][check_name] = check_result.get("score", 0)
            
            return json.dumps({
                "results": standardized_results,
                "json_path": f"operational_metrics_{url.replace('/', '_')}.json"
            }, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Operational metrics analysis failed: {str(e)}")
            return json.dumps({"error": str(e)})