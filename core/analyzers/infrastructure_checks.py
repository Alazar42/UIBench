from typing import Dict, Any
from playwright.async_api import Page
import logging
import socket
import time
import json
import dns.resolver
from urllib.parse import urlparse
import aiohttp
import asyncio

logger = logging.getLogger(__name__)

class InfrastructureChecks:
    @staticmethod
    async def check_cdn_utilization(page: Page) -> Dict[str, Any]:
        """
        Check if static resources are served from a CDN (by hostname pattern).
        """
        try:
            # Check for CDN-hosted resources
            cdn_resources = await page.evaluate("""
                () => {
                    const resources = Array.from(document.querySelectorAll('link[href], script[src], img[src]'));
                    return resources.filter(r => {
                        const url = r.href || r.src;
                        return url && (
                            url.includes('cdn.') ||
                            url.includes('cloudfront.net') ||
                            url.includes('akamaihd.net') ||
                            url.includes('cloudflare.com')
                        );
                    }).length;
                }
            """)
            
            total_resources = await page.evaluate("""
                () => document.querySelectorAll('link[href], script[src], img[src]').length
            """)
            
            cdn_ratio = cdn_resources / total_resources if total_resources > 0 else 0
            
            return {
                "score": min(1.0, cdn_ratio),
                "issues": [] if cdn_ratio >= 0.5 else ["Low CDN utilization"],
                "recommendations": [] if cdn_ratio >= 0.5 else ["Increase CDN utilization for better performance"],
                "details": {
                    "cdn_resources": cdn_resources,
                    "total_resources": total_resources,
                    "cdn_ratio": cdn_ratio
                }
            }
        except Exception as e:
            logger.error(f"Error checking CDN utilization: {str(e)}")
            return {
                "score": 0,
                "issues": [f"Error checking CDN utilization: {str(e)}"],
                "recommendations": ["Fix CDN utilization check implementation"],
                "details": {"error": str(e)}
            }

    @staticmethod
    async def check_cache_policies(page: Page) -> Dict[str, Any]:
        """
        Check for cache-control headers on static resources.
        """
        try:
            # Check cache headers for main page
            response = await page.goto(page.url)
            cache_headers = response.headers
            
            cache_control = cache_headers.get('cache-control', '')
            has_cache = bool(cache_control)
            
            return {
                "score": 1.0 if has_cache else 0,
                "issues": [] if has_cache else ["No cache headers found"],
                "recommendations": [] if has_cache else ["Implement proper cache headers"],
                "details": {
                    "cache_control": cache_control,
                    "has_cache": has_cache
                }
            }
        except Exception as e:
            logger.error(f"Error checking cache policies: {str(e)}")
            return {
                "score": 0,
                "issues": [f"Error checking cache policies: {str(e)}"],
                "recommendations": ["Fix cache policy check implementation"],
                "details": {"error": str(e)}
            }

    @staticmethod
    async def check_dns_configuration(url: str) -> Dict[str, Any]:
        """
        Check DNS records for the domain.
        """
        try:
            async with aiohttp.ClientSession() as session:
                start_time = asyncio.get_event_loop().time()
                async with session.get(url) as response:
                    dns_time = asyncio.get_event_loop().time() - start_time
                    
                    return {
                        "score": 1.0 if dns_time < 0.5 else 0.5,
                        "issues": [] if dns_time < 0.5 else ["High DNS resolution time"],
                        "recommendations": [] if dns_time < 0.5 else ["Optimize DNS configuration"],
                        "details": {
                            "dns_time": dns_time,
                            "status": response.status
                        }
                    }
        except Exception as e:
            logger.error(f"Error checking DNS configuration: {str(e)}")
            return {
                "score": 0,
                "issues": [f"Error checking DNS configuration: {str(e)}"],
                "recommendations": ["Fix DNS configuration check implementation"],
                "details": {"error": str(e)}
            }

    @staticmethod
    async def check_server_response_times(page: Page) -> Dict[str, Any]:
        """
        Measure server response time for the main page.
        """
        try:
            # Measure time to first byte
            start_time = asyncio.get_event_loop().time()
            response = await page.goto(page.url)
            ttfb = asyncio.get_event_loop().time() - start_time
            
            return {
                "score": 1.0 if ttfb < 0.5 else 0.5,
                "issues": [] if ttfb < 0.5 else ["High server response time"],
                "recommendations": [] if ttfb < 0.5 else ["Optimize server response time"],
                "details": {
                    "ttfb": ttfb,
                    "status": response.status
                }
            }
        except Exception as e:
            logger.error(f"Error checking server response times: {str(e)}")
            return {
                "score": 0,
                "issues": [f"Error checking server response times: {str(e)}"],
                "recommendations": ["Fix server response time check implementation"],
                "details": {"error": str(e)}
            }

    @staticmethod
    async def check_resource_prioritization(page: Page) -> Dict[str, Any]:
        """
        Check if critical resources are prioritized (preload, async, defer).
        """
        try:
            # Check for resource hints and priorities
            resource_hints = await page.evaluate("""
                () => {
                    const hints = document.querySelectorAll('link[rel="preload"], link[rel="prefetch"]');
                    return hints.length;
                }
            """)
            
            return {
                "score": 1.0 if resource_hints > 0 else 0.5,
                "issues": [] if resource_hints > 0 else ["No resource prioritization found"],
                "recommendations": [] if resource_hints > 0 else ["Implement resource prioritization"],
                "details": {
                    "resource_hints": resource_hints
                }
            }
        except Exception as e:
            logger.error(f"Error checking resource prioritization: {str(e)}")
            return {
                "score": 0,
                "issues": [f"Error checking resource prioritization: {str(e)}"],
                "recommendations": ["Fix resource prioritization check implementation"],
                "details": {"error": str(e)}
            }

    @staticmethod
    async def check_third_party_services(page: Page) -> Dict[str, Any]:
        """
        List and score third-party scripts/services.
        """
        try:
            # Count third-party resources
            third_party = await page.evaluate("""
                () => {
                    const resources = Array.from(document.querySelectorAll('link[href], script[src], img[src]'));
                    return resources.filter(r => {
                        const url = r.href || r.src;
                        return url && !url.startsWith(window.location.origin);
                    }).length;
                }
            """)
            
            return {
                "score": 1.0 if third_party < 10 else 0.5,
                "issues": [] if third_party < 10 else ["High number of third-party services"],
                "recommendations": [] if third_party < 10 else ["Reduce third-party service usage"],
                "details": {
                    "third_party_count": third_party
                }
            }
        except Exception as e:
            logger.error(f"Error checking third-party services: {str(e)}")
            return {
                "score": 0,
                "issues": [f"Error checking third-party services: {str(e)}"],
                "recommendations": ["Fix third-party service check implementation"],
                "details": {"error": str(e)}
            }

    @staticmethod
    async def check_error_monitoring(page: Page) -> Dict[str, Any]:
        """
        Check for error monitoring scripts (e.g., Sentry, Bugsnag).
        """
        try:
            # Check for error monitoring scripts
            error_monitoring = await page.evaluate("""
                () => {
                    const scripts = Array.from(document.querySelectorAll('script'));
                    return scripts.some(s => 
                        s.src.includes('sentry') || 
                        s.src.includes('newrelic') || 
                        s.src.includes('datadog')
                    );
                }
            """)
            
            return {
                "score": 1.0 if error_monitoring else 0,
                "issues": [] if error_monitoring else ["No error monitoring found"],
                "recommendations": [] if error_monitoring else ["Implement error monitoring"],
                "details": {
                    "has_error_monitoring": error_monitoring
                }
            }
        except Exception as e:
            logger.error(f"Error checking error monitoring: {str(e)}")
            return {
                "score": 0,
                "issues": [f"Error checking error monitoring: {str(e)}"],
                "recommendations": ["Fix error monitoring check implementation"],
                "details": {"error": str(e)}
            }

    @staticmethod
    async def check_load_balancing(page: Page) -> Dict[str, Any]:
        """Check load balancing configuration."""
        try:
            # Check for load balancer headers
            response = await page.goto(page.url)
            headers = response.headers
            
            has_lb = bool(headers.get('x-lb', '') or headers.get('x-load-balancer', ''))
            
            return {
                "score": 1.0 if has_lb else 0.5,
                "issues": [] if has_lb else ["No load balancing detected"],
                "recommendations": [] if has_lb else ["Implement load balancing"],
                "details": {
                    "has_load_balancer": has_lb
                }
            }
        except Exception as e:
            logger.error(f"Error checking load balancing: {str(e)}")
            return {
                "score": 0,
                "issues": [f"Error checking load balancing: {str(e)}"],
                "recommendations": ["Fix load balancing check implementation"],
                "details": {"error": str(e)}
            }

    @staticmethod
    async def check_security_headers(page: Page) -> Dict[str, Any]:
        """Check security headers."""
        try:
            response = await page.goto(page.url)
            headers = response.headers
            
            security_headers = {
                'content-security-policy': bool(headers.get('content-security-policy')),
                'x-frame-options': bool(headers.get('x-frame-options')),
                'x-content-type-options': bool(headers.get('x-content-type-options')),
                'strict-transport-security': bool(headers.get('strict-transport-security'))
            }
            
            score = sum(1 for v in security_headers.values() if v) / len(security_headers)
            
            return {
                "score": score,
                "issues": [k for k, v in security_headers.items() if not v],
                "recommendations": [f"Add {k} header" for k, v in security_headers.items() if not v],
                "details": security_headers
            }
        except Exception as e:
            logger.error(f"Error checking security headers: {str(e)}")
            return {
                "score": 0,
                "issues": [f"Error checking security headers: {str(e)}"],
                "recommendations": ["Fix security headers check implementation"],
                "details": {"error": str(e)}
            }

    @staticmethod
    async def check_ssl_tls_configuration(url: str) -> Dict[str, Any]:
        """Check SSL/TLS configuration."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    is_https = url.startswith('https://')
                    
                    return {
                        "score": 1.0 if is_https else 0,
                        "issues": [] if is_https else ["Not using HTTPS"],
                        "recommendations": [] if is_https else ["Enable HTTPS"],
                        "details": {
                            "is_https": is_https,
                            "status": response.status
                        }
                    }
        except Exception as e:
            logger.error(f"Error checking SSL/TLS configuration: {str(e)}")
            return {
                "score": 0,
                "issues": [f"Error checking SSL/TLS configuration: {str(e)}"],
                "recommendations": ["Fix SSL/TLS configuration check implementation"],
                "details": {"error": str(e)}
            } 