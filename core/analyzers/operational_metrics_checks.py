from typing import Dict, Any
from playwright.async_api import Page
import logging
import json

logger = logging.getLogger(__name__)

class OperationalMetricsChecks:
    @staticmethod
    async def check_uptime_monitoring(page: Page) -> Dict[str, Any]:
        """
        Check for presence of uptime monitoring scripts/services.
        """
        try:
            patterns = ['pingdom', 'uptimerobot', 'statuspage', 'freshping', 'betteruptime']
            scripts = await page.evaluate("""
                () => Array.from(document.querySelectorAll('script[src]')).map(el => el.src)
            """)
            found = [s for s in scripts if any(p in s for p in patterns)]
            issues = [] if found else ['No uptime monitoring scripts detected']
            passes = [f'Uptime monitoring script: {s}' for s in found]
            return {
                'score': 100 if found else 50,
                'issues': issues,
                'passes': passes,
                'details': {'uptime_scripts': found}
            }
        except Exception as e:
            logger.error(f"Uptime monitoring check failed: {str(e)}")
            return {'error': str(e)}

    @staticmethod
    async def check_error_budgets(page: Page) -> Dict[str, Any]:
        """
        Stub: Check for error budget documentation or monitoring integration.
        """
        try:
            found = await page.evaluate("""
                () => Array.from(document.querySelectorAll('a, button')).some(el =>
                    el.innerText && el.innerText.toLowerCase().includes('error budget')
                )
            """)
            issues = [] if found else ['No error budget documentation found']
            passes = ['Error budget documentation found'] if found else []
            return {
                'score': 100 if found else 50,
                'issues': issues,
                'passes': passes
            }
        except Exception as e:
            logger.error(f"Error budget check failed: {str(e)}")
            return {'error': str(e)}

    @staticmethod
    async def check_deployment_frequency(page: Page) -> Dict[str, Any]:
        """
        Stub: Check for deployment/version info in meta tags or headers.
        """
        try:
            found = await page.evaluate("""
                () => Array.from(document.querySelectorAll('meta')).some(meta =>
                    meta.name && meta.name.toLowerCase().includes('version')
                )
            """)
            issues = [] if found else ['No deployment/version info found']
            passes = ['Deployment/version info found'] if found else []
            return {
                'score': 100 if found else 50,
                'issues': issues,
                'passes': passes
            }
        except Exception as e:
            logger.error(f"Deployment frequency check failed: {str(e)}")
            return {'error': str(e)}

    @staticmethod
    async def check_mttr(page: Page) -> Dict[str, Any]:
        """
        Stub: Check for incident response/monitoring integration.
        """
        try:
            found = await page.evaluate("""
                () => Array.from(document.querySelectorAll('a, button')).some(el =>
                    el.innerText && (
                        el.innerText.toLowerCase().includes('incident') ||
                        el.innerText.toLowerCase().includes('status')
                    )
                )
            """)
            issues = [] if found else ['No incident response/status page found']
            passes = ['Incident response/status page found'] if found else []
            return {
                'score': 100 if found else 50,
                'issues': issues,
                'passes': passes
            }
        except Exception as e:
            logger.error(f"MTTR check failed: {str(e)}")
            return {'error': str(e)}

    @staticmethod
    async def check_performance_budgets(page: Page) -> Dict[str, Any]:
        """
        Check for performance budget meta tags or config in the page.
        """
        try:
            found = await page.evaluate("""
                () => Array.from(document.querySelectorAll('meta')).some(meta =>
                    meta.name && meta.name.toLowerCase().includes('performance-budget')
                )
            """)
            issues = [] if found else ['No performance budget meta tag found']
            passes = ['Performance budget meta tag found'] if found else []
            return {
                'score': 100 if found else 50,
                'issues': issues,
                'passes': passes
            }
        except Exception as e:
            logger.error(f"Performance budget check failed: {str(e)}")
            return {'error': str(e)}

    @staticmethod
    async def check_audit_trails(page: Page) -> Dict[str, Any]:
        """
        Check for audit trail scripts or links (e.g., "audit log", "activity log").
        """
        try:
            found = await page.evaluate("""
                () => Array.from(document.querySelectorAll('a, button')).some(el =>
                    el.innerText && (
                        el.innerText.toLowerCase().includes('audit log') ||
                        el.innerText.toLowerCase().includes('activity log')
                    )
                )
            """)
            issues = [] if found else ['No audit trail/activity log found']
            passes = ['Audit trail/activity log found'] if found else []
            return {
                'score': 100 if found else 50,
                'issues': issues,
                'passes': passes
            }
        except Exception as e:
            logger.error(f"Audit trail check failed: {str(e)}")
            return {'error': str(e)} 