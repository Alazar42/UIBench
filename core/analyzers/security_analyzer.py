from typing import Dict, Any
from playwright.async_api import Page
import asyncio
from ..utils.error_handler import AnalysisError
import logging
from .security_checks import SecurityChecks
from .base_analyzer import BaseAnalyzer
import json

logger = logging.getLogger(__name__)

class SecurityAnalyzer(BaseAnalyzer):
    """Analyzes web pages for security vulnerabilities and best practices."""
    
    async def analyze(self, url: str, page: Page) -> str:
        """
        Perform comprehensive security analysis.
        Returns:
            JSON string containing security analysis results and JSON file path
        """
        try:
            # Run all security checks
            security_checks = {
                "headers": await self._check_security_headers(page),
                "content_security": await self._check_content_security(page),
                "authentication": await self._check_authentication(page),
                "input_validation": await self._check_input_validation(page),
                "data_protection": await self._check_data_protection(page),
                "api_security": await self._check_api_security(page),
                "cookie_security": await SecurityChecks.check_cookie_security_flags(page),
                "input_sanitization": await SecurityChecks.check_input_sanitization(page),
                "clickjacking_protection": await SecurityChecks.check_clickjacking_protection(page),
                "csp_xss": await SecurityChecks.check_csp_xss(page),
                "csrf_tokens": await SecurityChecks.check_csrf_tokens(page),
                "mixed_content": await SecurityChecks.check_mixed_content(page)
            }

            # Calculate overall score
            scores = [result.get("score", 0) for result in security_checks.values() if isinstance(result, dict)]
            overall_score = sum(scores) / len(scores) if scores else 0

            # Collect all issues and recommendations
            all_issues = []
            all_recommendations = []
            metrics = {}

            for check_name, result in security_checks.items():
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
                "details": security_checks
            }

            # Save to JSON
            json_path = self.save_to_json(standardized_results, url, "security")

            return json.dumps({
                "results": standardized_results,
                "json_path": json_path
            }, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Security analysis failed: {str(e)}")
            raise AnalysisError(f"Security analysis failed: {str(e)}")
    
    async def _check_security_headers(self, page: Page) -> Dict[str, Any]:
        """Check security-related HTTP headers."""
        issues = []
        
        # Get response headers
        response = await page.goto(page.url)
        headers = response.headers
        
        # Check for essential security headers
        required_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": ["DENY", "SAMEORIGIN"],
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=",
            "Content-Security-Policy": None
        }
        
        for header, value in required_headers.items():
            if header not in headers:
                issues.append(f"Missing {header} header")
            elif value and not any(v in headers[header] for v in (value if isinstance(value, list) else [value])):
                issues.append(f"Invalid {header} header value")
        
        return {
            "score": max(100 - len(issues) * 20, 0),
            "issues": issues
        }
    
    async def _check_content_security(self, page: Page) -> Dict[str, Any]:
        """Check Content Security Policy and related security measures."""
        issues = []
        
        # Check for inline scripts
        inline_scripts = await page.evaluate("""
            () => {
                const scripts = document.querySelectorAll('script:not([src])');
                return scripts.length;
            }
        """)
        
        if inline_scripts > 0:
            issues.append(f"Found {inline_scripts} inline scripts")
        
        # Check for unsafe eval
        unsafe_eval = await page.evaluate("""
            () => {
                const scripts = document.querySelectorAll('script');
                return Array.from(scripts).some(script => 
                    script.textContent.includes('eval(') || 
                    script.textContent.includes('new Function')
                );
            }
        """)
        
        if unsafe_eval:
            issues.append("Found unsafe eval usage")
        
        return {
            "score": max(100 - len(issues) * 20, 0),
            "issues": issues
        }
    
    async def _check_authentication(self, page: Page) -> Dict[str, Any]:
        """Check authentication mechanisms."""
        issues = []
        
        # Check for secure cookie settings
        cookies = await page.context.cookies()
        for cookie in cookies:
            if not cookie.get("secure"):
                issues.append(f"Cookie {cookie['name']} missing secure flag")
            if not cookie.get("httpOnly"):
                issues.append(f"Cookie {cookie['name']} missing httpOnly flag")
        
        # Check for proper session management
        session_cookie = next((c for c in cookies if "session" in c["name"].lower()), None)
        if session_cookie and not session_cookie.get("secure"):
            issues.append("Session cookie not marked as secure")
        
        return {
            "score": max(100 - len(issues) * 20, 0),
            "issues": issues
        }
    
    async def _check_input_validation(self, page: Page) -> Dict[str, Any]:
        """Check input validation and sanitization."""
        issues = []
        
        # Check form inputs
        forms = await page.query_selector_all("form")
        for form in forms:
            inputs = await form.query_selector_all("input, textarea")
            for input in inputs:
                # Check for proper input validation
                if not await input.get_attribute("pattern"):
                    issues.append("Input missing pattern validation")
                
                # Check for proper input sanitization
                if not await input.get_attribute("data-sanitize"):
                    issues.append("Input missing sanitization")
        
        return {
            "score": max(100 - len(issues) * 10, 0),
            "issues": issues
        }
    
    async def _check_data_protection(self, page: Page) -> Dict[str, Any]:
        """Check data protection measures."""
        issues = []
        
        # Check for sensitive data exposure
        sensitive_data = await page.evaluate("""
            () => {
                const text = document.body.innerText;
                const patterns = [
                    /\\b\\d{16}\\b/,  // Credit card
                    /\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}\\b/,  // Email
                    /\\b\\d{3}-\\d{2}-\\d{4}\\b/  // SSN
                ];
                return patterns.some(pattern => pattern.test(text));
            }
        """)
        
        if sensitive_data:
            issues.append("Found potential sensitive data exposure")
        
        return {
            "score": max(100 - len(issues) * 50, 0),
            "issues": issues
        }
    
    async def _check_api_security(self, page: Page) -> Dict[str, Any]:
        """Check API security measures."""
        issues = []
        
        # Check for API endpoints
        api_calls = await page.evaluate("""
            () => {
                const resources = performance.getEntriesByType('resource');
                return resources.filter(r => 
                    r.name.includes('/api/') || 
                    r.name.includes('/v1/') || 
                    r.name.includes('/v2/')
                );
            }
        """)
        
        for call in api_calls:
            if not call["name"].startswith("https"):
                issues.append(f"Insecure API endpoint: {call['name']}")
        
        return {
            "score": max(100 - len(issues) * 20, 0),
            "issues": issues
        }