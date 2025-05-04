from typing import Dict, Any
from playwright.async_api import Page
from .compliance_checks import ComplianceChecks
import logging
import json
from .base_analyzer import BaseAnalyzer

logger = logging.getLogger(__name__)

class ComplianceAnalyzer(BaseAnalyzer):
    """Analyzes web pages for compliance with privacy, accessibility, and data protection requirements."""
    
    async def analyze(self, url: str, page: Page) -> str:
        """
        Perform comprehensive compliance analysis.
        
        Args:
            url: Target URL
            page: Playwright page object
            
        Returns:
            JSON string containing compliance analysis results and JSON file path
        """
        try:
            # Run all compliance checks
            compliance_checks = {
                "cookie_consent": await ComplianceChecks.check_cookie_consent(page),
                "privacy_policy": await ComplianceChecks.check_privacy_policy_link(page),
                "accessibility_statement": await ComplianceChecks.check_accessibility_statement(page),
                "data_access_controls": await ComplianceChecks.check_data_access_controls(page),
                "gdpr_compliance": await ComplianceChecks.check_gdpr_compliance(page),
                "ccpa_compliance": await ComplianceChecks.check_ccpa_compliance(page),
                "data_retention": await ComplianceChecks.check_data_retention_policy(page)
            }

            # Calculate overall score
            scores = [result.get("score", 0) for result in compliance_checks.values() if isinstance(result, dict)]
            overall_score = sum(scores) / len(scores) if scores else 0

            # Collect all issues and recommendations
            all_issues = []
            all_recommendations = []
            metrics = {}

            for check_name, result in compliance_checks.items():
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
                "details": compliance_checks
            }

            # Save to JSON
            json_path = self.save_to_json(standardized_results, url, "compliance")

            return json.dumps({
                "results": standardized_results,
                "json_path": json_path
            }, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Compliance analysis failed: {str(e)}")
            raise AnalysisError(f"Compliance analysis failed: {str(e)}")