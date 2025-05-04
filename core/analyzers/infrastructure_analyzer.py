from typing import Dict, Any
from playwright.async_api import Page
from .infrastructure_checks import InfrastructureChecks
import logging
import json
from .base_analyzer import BaseAnalyzer
from .exceptions import AnalysisError

logger = logging.getLogger(__name__)

class InfrastructureAnalyzer(BaseAnalyzer):
    """Analyzes web pages for infrastructure and architecture best practices."""
    
    async def analyze(self, url: str, page: Page) -> str:
        """
        Perform comprehensive infrastructure analysis.
        
        Args:
            url: Target URL
            page: Playwright page object
            
        Returns:
            JSON string containing infrastructure analysis results and JSON file path
        """
        try:
            # Run all infrastructure checks
            infrastructure_checks = {
                "cdn_utilization": await InfrastructureChecks.check_cdn_utilization(page),
                "cache_policies": await InfrastructureChecks.check_cache_policies(page),
                "dns_configuration": await InfrastructureChecks.check_dns_configuration(url),
                "server_response_times": await InfrastructureChecks.check_server_response_times(page),
                "resource_prioritization": await InfrastructureChecks.check_resource_prioritization(page),
                "third_party_services": await InfrastructureChecks.check_third_party_services(page),
                "error_monitoring": await InfrastructureChecks.check_error_monitoring(page),
                "load_balancing": await InfrastructureChecks.check_load_balancing(page),
                "security_headers": await InfrastructureChecks.check_security_headers(page),
                "ssl_tls": await InfrastructureChecks.check_ssl_tls_configuration(url)
            }

            # Calculate overall score
            scores = [result.get("score", 0) for result in infrastructure_checks.values() if isinstance(result, dict)]
            overall_score = sum(scores) / len(scores) if scores else 0

            # Collect all issues and recommendations
            all_issues = []
            all_recommendations = []
            metrics = {}

            for check_name, result in infrastructure_checks.items():
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
                "details": infrastructure_checks
            }

            # Save to JSON
            json_path = self.save_to_json(standardized_results, url, "infrastructure")

            return json.dumps({
                "results": standardized_results,
                "json_path": json_path
            }, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Infrastructure analysis failed: {str(e)}")
            raise AnalysisError(f"Infrastructure analysis failed: {str(e)}")