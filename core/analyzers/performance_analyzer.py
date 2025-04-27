from typing import Dict, Any
from playwright.async_api import Page
import asyncio
from ..utils.error_handler import AnalysisError

class PerformanceAnalyzer:
    """Analyzes web pages for performance metrics and optimization."""
    
    async def analyze(self, url: str, page: Page) -> Dict[str, Any]:
        """
        Perform comprehensive performance analysis.
        
        Args:
            url: Target URL
            page: Playwright page object
            
        Returns:
            Dict containing performance analysis results
        """
        try:
            results = {
                "core_web_vitals": await self._check_core_web_vitals(page),
                "resource_optimization": await self._check_resource_optimization(page),
                "caching": await self._check_caching(page),
                "rendering_performance": await self._check_rendering_performance(page),
                "network_performance": await self._check_network_performance(page),
                "mobile_performance": await self._check_mobile_performance(page)
            }
            
            # Calculate overall performance score
            scores = [result.get("score", 0) for result in results.values() if isinstance(result, dict)]
            results["overall_score"] = sum(scores) / len(scores) if scores else 0
            
            return results
        except Exception as e:
            raise AnalysisError(f"Performance analysis failed: {str(e)}")
    
    async def _check_core_web_vitals(self, page: Page) -> Dict[str, Any]:
        """Check Core Web Vitals metrics."""
        try:
            # Get LCP (Largest Contentful Paint)
            lcp = await page.evaluate("""
                () => {
                    return new Promise((resolve) => {
                        new PerformanceObserver((entryList) => {
                            const entries = entryList.getEntries();
                            resolve(entries[entries.length - 1].startTime);
                        }).observe({ entryTypes: ['largest-contentful-paint'] });
                    });
                }
            """)
            
            # Get FID (First Input Delay)
            fid = await page.evaluate("""
                () => {
                    return new Promise((resolve) => {
                        new PerformanceObserver((entryList) => {
                            const entries = entryList.getEntries();
                            resolve(entries[0].duration);
                        }).observe({ entryTypes: ['first-input'] });
                    });
                }
            """)
            
            # Get CLS (Cumulative Layout Shift)
            cls = await page.evaluate("""
                () => {
                    return new Promise((resolve) => {
                        new PerformanceObserver((entryList) => {
                            let cls = 0;
                            for (const entry of entryList.getEntries()) {
                                cls += entry.value;
                            }
                            resolve(cls);
                        }).observe({ entryTypes: ['layout-shift'] });
                    });
                }
            """)
            
            issues = []
            if lcp > 2500:
                issues.append("LCP is too high")
            if fid > 100:
                issues.append("FID is too high")
            if cls > 0.1:
                issues.append("CLS is too high")
            
            return {
                "score": max(100 - len(issues) * 20, 0),
                "metrics": {
                    "lcp": lcp,
                    "fid": fid,
                    "cls": cls
                },
                "issues": issues
            }
        except Exception as e:
            raise AnalysisError(f"Core Web Vitals check failed: {str(e)}")
    
    async def _check_resource_optimization(self, page: Page) -> Dict[str, Any]:
        """Check resource optimization."""
        issues = []
        
        # Check image optimization
        images = await page.evaluate("""
            () => {
                const images = document.querySelectorAll('img');
                return Array.from(images).map(img => ({
                    src: img.src,
                    width: img.naturalWidth,
                    height: img.naturalHeight,
                    displayWidth: img.width,
                    displayHeight: img.height
                }));
            }
        """)
        
        for img in images:
            if img["width"] > img["displayWidth"] * 2:
                issues.append(f"Image {img['src']} is too large for its display size")
        
        # Check script optimization
        scripts = await page.evaluate("""
            () => {
                const scripts = document.querySelectorAll('script');
                return Array.from(scripts).map(script => ({
                    src: script.src,
                    async: script.async,
                    defer: script.defer
                }));
            }
        """)
        
        for script in scripts:
            if script["src"] and not (script["async"] or script["defer"]):
                issues.append(f"Script {script['src']} should be async or deferred")
        
        return {
            "score": max(100 - len(issues) * 10, 0),
            "issues": issues
        }
    
    async def _check_caching(self, page: Page) -> Dict[str, Any]:
        """Check caching configuration."""
        issues = []
        
        # Check cache headers
        response = await page.goto(page.url)
        headers = response.headers
        
        if "Cache-Control" not in headers:
            issues.append("Missing Cache-Control header")
        if "ETag" not in headers:
            issues.append("Missing ETag header")
        
        return {
            "score": max(100 - len(issues) * 20, 0),
            "issues": issues
        }
    
    async def _check_rendering_performance(self, page: Page) -> Dict[str, Any]:
        """Check rendering performance."""
        issues = []
        
        # Check for render-blocking resources
        render_blocking = await page.evaluate("""
            () => {
                const resources = performance.getEntriesByType('resource');
                return resources.filter(r => r.renderBlocking === 'blocking');
            }
        """)
        
        if render_blocking:
            issues.append(f"Found {len(render_blocking)} render-blocking resources")
        
        return {
            "score": max(100 - len(issues) * 20, 0),
            "issues": issues
        }
    
    async def _check_network_performance(self, page: Page) -> Dict[str, Any]:
        """Check network performance."""
        issues = []
        
        # Get network timing metrics
        timing = await page.evaluate("""
            () => {
                const timing = performance.timing;
                return {
                    dns: timing.domainLookupEnd - timing.domainLookupStart,
                    tcp: timing.connectEnd - timing.connectStart,
                    ttfb: timing.responseStart - timing.requestStart,
                    download: timing.responseEnd - timing.responseStart
                };
            }
        """)
        
        if timing["dns"] > 100:
            issues.append("DNS lookup time is too high")
        if timing["tcp"] > 100:
            issues.append("TCP connection time is too high")
        if timing["ttfb"] > 200:
            issues.append("Time to First Byte is too high")
        
        return {
            "score": max(100 - len(issues) * 20, 0),
            "metrics": timing,
            "issues": issues
        }
    
    async def _check_mobile_performance(self, page: Page) -> Dict[str, Any]:
        """Check mobile performance."""
        issues = []
        
        # Set mobile viewport
        await page.set_viewport_size({"width": 375, "height": 667})
        
        # Check for mobile-specific issues
        if not await page.evaluate("""
            () => {
                const meta = document.querySelector('meta[name="viewport"]');
                return meta && meta.content.includes('width=device-width');
            }
        """):
            issues.append("Missing proper mobile viewport meta tag")
        
        # Check for touch targets
        touch_targets = await page.evaluate("""
            () => {
                const targets = document.querySelectorAll('a, button, input, select');
                return Array.from(targets).filter(el => {
                    const rect = el.getBoundingClientRect();
                    return rect.width < 44 || rect.height < 44;
                });
            }
        """)
        
        if touch_targets:
            issues.append(f"Found {len(touch_targets)} touch targets that are too small")
        
        return {
            "score": max(100 - len(issues) * 20, 0),
            "issues": issues
        } 