from typing import Dict, Any, List
from playwright.async_api import Page
import logging
import json

logger = logging.getLogger(__name__)

class SecurityChecks:
    @staticmethod
    async def check_cookie_security_flags(page: Page) -> Dict[str, Any]:
        """
        Check all cookies for Secure, HttpOnly, and SameSite flags.
        """
        try:
            cookies = await page.context.cookies()
            issues = []
            passes = []
            for cookie in cookies:
                missing_flags = []
                if not cookie.get('secure', False):
                    missing_flags.append('Secure')
                if not cookie.get('httpOnly', False):
                    missing_flags.append('HttpOnly')
                if not cookie.get('sameSite', None):
                    missing_flags.append('SameSite')
                if missing_flags:
                    issues.append({
                        'name': cookie.get('name'),
                        'domain': cookie.get('domain'),
                        'missing_flags': missing_flags
                    })
                else:
                    passes.append({
                        'name': cookie.get('name'),
                        'domain': cookie.get('domain'),
                        'status': 'All security flags set'
                    })
            return {
                'score': max(100 - len(issues) * 10, 0),
                'issues': issues,
                'passes': passes,
                'details': {
                    'total_cookies': len(cookies),
                    'secure_cookies': len(passes),
                    'insecure_cookies': len(issues)
                }
            }
        except Exception as e:
            logger.error(f"Cookie security flag check failed: {str(e)}")
            return {'error': str(e)}

    @staticmethod
    async def check_input_sanitization(page: Page) -> Dict[str, Any]:
        """
        Check input fields for basic sanitization and validation attributes.
        """
        try:
            inputs = await page.query_selector_all('input, textarea')
            issues = []
            passes = []
            for input_elem in inputs:
                attrs = await input_elem.evaluate('el => ({pattern: el.getAttribute("pattern"), maxlength: el.getAttribute("maxlength"), minlength: el.getAttribute("minlength"), required: el.hasAttribute("required"), type: el.getAttribute("type")})')
                has_validation = attrs['pattern'] or attrs['maxlength'] or attrs['minlength'] or attrs['required']
                is_text = attrs['type'] in (None, '', 'text', 'search', 'email', 'url', 'tel', 'password')
                if is_text and not has_validation:
                    issues.append({
                        'type': attrs['type'],
                        'missing_validation': True,
                        'details': attrs
                    })
                else:
                    passes.append({
                        'type': attrs['type'],
                        'validation': True,
                        'details': attrs
                    })
            return {
                'score': max(100 - len(issues) * 10, 0),
                'issues': issues,
                'passes': passes,
                'details': {
                    'total_inputs': len(inputs),
                    'validated_inputs': len(passes),
                    'unvalidated_inputs': len(issues)
                }
            }
        except Exception as e:
            logger.error(f"Input sanitization check failed: {str(e)}")
            return {'error': str(e)}

    @staticmethod
    async def check_clickjacking_protection(page: Page) -> Dict[str, Any]:
        """
        Check for X-Frame-Options and CSP frame-ancestors headers to prevent clickjacking.
        """
        try:
            # Playwright does not expose response headers directly from the page object,
            # so we fetch them via a request.
            response = await page.goto(page.url)
            headers = response.headers if response else {}
            issues = []
            passes = []
            xfo = headers.get('x-frame-options', '')
            csp = headers.get('content-security-policy', '')
            has_xfo = xfo.lower() in ('deny', 'sameorigin')
            has_csp_frame_ancestors = 'frame-ancestors' in csp.lower()
            if not has_xfo and not has_csp_frame_ancestors:
                issues.append('Missing X-Frame-Options and CSP frame-ancestors headers')
            else:
                if has_xfo:
                    passes.append('X-Frame-Options header present and secure')
                if has_csp_frame_ancestors:
                    passes.append('CSP frame-ancestors directive present')
            return {
                'score': 100 if not issues else 50,
                'issues': issues,
                'passes': passes,
                'details': headers
            }
        except Exception as e:
            logger.error(f"Clickjacking protection check failed: {str(e)}")
            return {'error': str(e)}

    @staticmethod
    async def check_csp_xss(page: Page) -> Dict[str, Any]:
        """
        Check for strong Content-Security-Policy and XSS vectors.
        """
        try:
            response = await page.goto(page.url)
            headers = response.headers if response else {}
            csp = headers.get('content-security-policy', '')
            issues = []
            passes = []
            if not csp:
                issues.append('Missing Content-Security-Policy header')
            else:
                if 'unsafe-inline' in csp or 'unsafe-eval' in csp:
                    issues.append('CSP allows unsafe-inline or unsafe-eval')
                else:
                    passes.append('CSP does not allow unsafe-inline or unsafe-eval')
            # Check for inline scripts
            inline_scripts = await page.evaluate("""
                () => Array.from(document.querySelectorAll('script:not([src])')).length
            """)
            if inline_scripts > 0:
                issues.append(f"Found {inline_scripts} inline scripts (potential XSS risk)")
            # Check for event handler attributes
            event_attrs = await page.evaluate("""
                () => Array.from(document.querySelectorAll('*')).some(el =>
                    Array.from(el.attributes).some(attr => attr.name.startsWith('on')))
            """)
            if event_attrs:
                issues.append('Found elements with inline event handlers (potential XSS risk)')
            return {
                'score': max(100 - len(issues) * 20, 0),
                'issues': issues,
                'passes': passes,
                'details': {'csp': csp}
            }
        except Exception as e:
            logger.error(f"CSP/XSS check failed: {str(e)}")
            return {'error': str(e)}

    @staticmethod
    async def check_csrf_tokens(page: Page) -> Dict[str, Any]:
        """
        Check forms for CSRF token fields.
        """
        try:
            forms = await page.query_selector_all('form')
            issues = []
            passes = []
            for form in forms:
                has_token = False
                inputs = await form.query_selector_all('input[type="hidden"]')
                for input_elem in inputs:
                    name = await input_elem.get_attribute('name')
                    if name and any(token in name.lower() for token in ['csrf', 'token', 'authenticity']):
                        has_token = True
                        break
                if not has_token:
                    issues.append('Form missing CSRF token')
                else:
                    passes.append('Form has CSRF token')
            return {
                'score': max(100 - len(issues) * 20, 0),
                'issues': issues,
                'passes': passes,
                'details': {'total_forms': len(forms), 'forms_with_token': len(passes)}
            }
        except Exception as e:
            logger.error(f"CSRF token check failed: {str(e)}")
            return {'error': str(e)}

    @staticmethod
    async def check_mixed_content(page: Page) -> Dict[str, Any]:
        """
        Check for mixed content (HTTP resources on HTTPS pages).
        """
        try:
            url = page.url
            if not url.startswith('https://'):
                return {'score': 100, 'issues': [], 'passes': ['Not an HTTPS page'], 'details': {}}
            # Check all resource URLs
            resources = await page.evaluate("""
                () => Array.from(document.querySelectorAll('img, script, link, iframe, video, audio, source')).map(el => el.src || el.href || '')
            """)
            mixed = [r for r in resources if r.startswith('http://')]
            issues = []
            passes = []
            if mixed:
                issues.append(f"Mixed content: {len(mixed)} HTTP resources found")
            else:
                passes.append('No mixed content detected')
            return {
                'score': 100 if not mixed else 50,
                'issues': issues,
                'passes': passes,
                'details': {'mixed_content': mixed}
            }
        except Exception as e:
            logger.error(f"Mixed content check failed: {str(e)}")
            return {'error': str(e)} 