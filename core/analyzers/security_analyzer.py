"""
Security analyzer for evaluating page security.
"""
import json
import os
from datetime import datetime
from typing import Dict, Any
from playwright.async_api import Page
from bs4 import BeautifulSoup
from core.utils.error_handler import AnalysisError
import logging
from .security_checks import SecurityChecks
from .base_analyzer import BaseAnalyzer

logger = logging.getLogger(__name__)

class SecurityAnalyzer:
    """Analyzer for security evaluation."""
    
    def _save_results(self, url: str, results: Dict[str, Any]) -> str:
        """Save analysis results to a JSON file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"security_{url.replace('://', '_').replace('/', '_')}_{timestamp}.json"
        output_dir = "analysis_results"
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        return filepath
    
    async def analyze(self, url: str, page: Page, soup: BeautifulSoup) -> str:
        """
        Analyze the page for security issues.
        
        Args:
            url: The URL of the page to analyze
            page: Playwright page object
            soup: BeautifulSoup object of the page
            
        Returns:
            JSON string containing analysis results
        """
        try:
            # Initialize results structure
            results = {
                "results": {
                    "overall_score": 0,
                    "security_headers": 0,
                    "content_security": 0,
                    "issues": [],
                    "recommendations": [],
                    "metrics": {
                        "security_score": 0,
                        "total_checks": 0,
                        "execution_time": 0
                    }
                },
                "json_path": None
            }
            
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
            
            # Process check results
            total_score = 0
            total_checks = len(security_checks)
            
            for check_name, check_result in security_checks.items():
                if isinstance(check_result, dict):
                    score = check_result.get("score", 0)
                    issues = check_result.get("issues", [])
                    recommendations = check_result.get("recommendations", [])
                    
                    total_score += score
                    results["results"]["issues"].extend(issues)
                    results["results"]["recommendations"].extend(recommendations)
            
            # Calculate overall score
            results["results"]["overall_score"] = total_score / total_checks if total_checks > 0 else 0
            results["results"]["metrics"]["security_score"] = results["results"]["overall_score"]
            results["results"]["metrics"]["total_checks"] = total_checks
            
            # Save results to file
            results["json_path"] = self._save_results(url, results)
            
            return json.dumps(results, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"Security analysis failed: {str(e)}")
            raise
    
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