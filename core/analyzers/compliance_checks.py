from typing import Dict, Any
from playwright.async_api import Page
import logging

logger = logging.getLogger(__name__)

class ComplianceChecks:
    """Class containing methods for compliance checks."""
    
    @staticmethod
    async def check_cookie_consent(page: Page) -> Dict[str, Any]:
        """Check if cookie consent banner is present and functional."""
        try:
            # Check for common cookie consent elements
            cookie_banner = await page.query_selector('[class*="cookie"], [id*="cookie"], [class*="consent"], [id*="consent"]')
            if not cookie_banner:
                return {
                    "score": 0,
                    "issues": ["No cookie consent banner found"],
                    "recommendations": ["Implement a cookie consent banner"],
                    "details": {"banner_found": False}
                }
            
            # Check if banner has accept/reject buttons
            accept_button = await cookie_banner.query_selector('[class*="accept"], [id*="accept"]')
            reject_button = await cookie_banner.query_selector('[class*="reject"], [id*="reject"]')
            
            return {
                "score": 1.0 if accept_button and reject_button else 0.5,
                "issues": [] if accept_button and reject_button else ["Cookie consent banner missing accept/reject buttons"],
                "recommendations": [] if accept_button and reject_button else ["Add accept and reject buttons to cookie consent banner"],
                "details": {
                    "banner_found": True,
                    "has_accept_button": bool(accept_button),
                    "has_reject_button": bool(reject_button)
                }
            }
        except Exception as e:
            logger.error(f"Error checking cookie consent: {str(e)}")
            return {
                "score": 0,
                "issues": [f"Error checking cookie consent: {str(e)}"],
                "recommendations": ["Fix cookie consent banner implementation"],
                "details": {"error": str(e)}
            }
    
    @staticmethod
    async def check_privacy_policy_link(page: Page) -> Dict[str, Any]:
        """Check if privacy policy link is present and accessible."""
        try:
            privacy_link = await page.query_selector('a[href*="privacy"], a[href*="policy"]')
            if not privacy_link:
                return {
                    "score": 0,
                    "issues": ["No privacy policy link found"],
                    "recommendations": ["Add a privacy policy link"],
                    "details": {"link_found": False}
                }
            
            return {
                "score": 1.0,
                "issues": [],
                "recommendations": [],
                "details": {"link_found": True}
            }
        except Exception as e:
            logger.error(f"Error checking privacy policy link: {str(e)}")
            return {
                "score": 0,
                "issues": [f"Error checking privacy policy link: {str(e)}"],
                "recommendations": ["Fix privacy policy link implementation"],
                "details": {"error": str(e)}
            }
    
    @staticmethod
    async def check_accessibility_statement(page: Page) -> Dict[str, Any]:
        """Check if accessibility statement is present."""
        try:
            accessibility_link = await page.query_selector('a[href*="accessibility"], a[href*="a11y"]')
            if not accessibility_link:
                return {
                    "score": 0,
                    "issues": ["No accessibility statement found"],
                    "recommendations": ["Add an accessibility statement"],
                    "details": {"statement_found": False}
                }
            
            return {
                "score": 1.0,
                "issues": [],
                "recommendations": [],
                "details": {"statement_found": True}
            }
        except Exception as e:
            logger.error(f"Error checking accessibility statement: {str(e)}")
            return {
                "score": 0,
                "issues": [f"Error checking accessibility statement: {str(e)}"],
                "recommendations": ["Fix accessibility statement implementation"],
                "details": {"error": str(e)}
            }
    
    @staticmethod
    async def check_data_access_controls(page: Page) -> Dict[str, Any]:
        """Check if data access controls are implemented."""
        try:
            # Check for data access request form or link
            data_access = await page.query_selector('[class*="data-access"], [id*="data-access"]')
            if not data_access:
                return {
                    "score": 0,
                    "issues": ["No data access controls found"],
                    "recommendations": ["Implement data access controls"],
                    "details": {"controls_found": False}
                }
            
            return {
                "score": 1.0,
                "issues": [],
                "recommendations": [],
                "details": {"controls_found": True}
            }
        except Exception as e:
            logger.error(f"Error checking data access controls: {str(e)}")
            return {
                "score": 0,
                "issues": [f"Error checking data access controls: {str(e)}"],
                "recommendations": ["Fix data access controls implementation"],
                "details": {"error": str(e)}
            }
    
    @staticmethod
    async def check_gdpr_compliance(page: Page) -> Dict[str, Any]:
        """Check GDPR compliance requirements."""
        try:
            # Check for GDPR-specific elements
            gdpr_elements = await page.query_selector('[class*="gdpr"], [id*="gdpr"]')
            if not gdpr_elements:
                return {
                    "score": 0,
                    "issues": ["No GDPR compliance elements found"],
                    "recommendations": ["Implement GDPR compliance elements"],
                    "details": {"gdpr_elements_found": False}
                }
            
            return {
                "score": 1.0,
                "issues": [],
                "recommendations": [],
                "details": {"gdpr_elements_found": True}
            }
        except Exception as e:
            logger.error(f"Error checking GDPR compliance: {str(e)}")
            return {
                "score": 0,
                "issues": [f"Error checking GDPR compliance: {str(e)}"],
                "recommendations": ["Fix GDPR compliance implementation"],
                "details": {"error": str(e)}
            }
    
    @staticmethod
    async def check_ccpa_compliance(page: Page) -> Dict[str, Any]:
        """Check CCPA compliance requirements."""
        try:
            # Check for CCPA-specific elements
            ccpa_elements = await page.query_selector('[class*="ccpa"], [id*="ccpa"]')
            if not ccpa_elements:
                return {
                    "score": 0,
                    "issues": ["No CCPA compliance elements found"],
                    "recommendations": ["Implement CCPA compliance elements"],
                    "details": {"ccpa_elements_found": False}
                }
            
            return {
                "score": 1.0,
                "issues": [],
                "recommendations": [],
                "details": {"ccpa_elements_found": True}
            }
        except Exception as e:
            logger.error(f"Error checking CCPA compliance: {str(e)}")
            return {
                "score": 0,
                "issues": [f"Error checking CCPA compliance: {str(e)}"],
                "recommendations": ["Fix CCPA compliance implementation"],
                "details": {"error": str(e)}
            }
    
    @staticmethod
    async def check_data_retention_policy(page: Page) -> Dict[str, Any]:
        """Check if data retention policy is present."""
        try:
            # Check for data retention policy link or section
            retention_policy = await page.query_selector('[class*="retention"], [id*="retention"]')
            if not retention_policy:
                return {
                    "score": 0,
                    "issues": ["No data retention policy found"],
                    "recommendations": ["Add a data retention policy"],
                    "details": {"policy_found": False}
                }
            
            return {
                "score": 1.0,
                "issues": [],
                "recommendations": [],
                "details": {"policy_found": True}
            }
        except Exception as e:
            logger.error(f"Error checking data retention policy: {str(e)}")
            return {
                "score": 0,
                "issues": [f"Error checking data retention policy: {str(e)}"],
                "recommendations": ["Fix data retention policy implementation"],
                "details": {"error": str(e)}
            } 