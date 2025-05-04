from typing import Dict, Any, List, Optional
from playwright.async_api import Page, Response
import asyncio
import logging
from datetime import datetime
from bs4 import BeautifulSoup
import os
import json

from ..utils.error_handler import AnalysisError
from ..utils.performance_utils import async_timed, PerformanceMonitor
from ..utils.cache import AnalysisCache
from ..config import Settings
from .base_analyzer import BaseAnalyzer

logger = logging.getLogger(__name__)
config = Settings()

class PerformanceAnalyzer(BaseAnalyzer):
    """Analyzes website performance metrics."""
    
    def __init__(self):
        super().__init__()
        self.performance_monitor = PerformanceMonitor()
        self.cache = AnalysisCache()
    
    async def analyze(self, url: str, page: Page, soup: BeautifulSoup) -> str:
        """
        Perform performance analysis.
        
        Args:
            url: Target URL
            page: Playwright page object
            soup: BeautifulSoup parsed HTML
            
        Returns:
            JSON string containing performance analysis results and JSON file path
        """
        try:
            # Get page content for size analysis
            content = await page.content()
            
            results = {
                "page_size": self._analyze_page_size(content),
                "resource_loading": self._analyze_resource_loading(soup),
                "render_blocking": self._analyze_render_blocking(soup),
                "caching": self._analyze_caching(soup),
                "compression": self._analyze_compression(soup)
            }
            
            # Calculate overall performance score
            scores = [result.get("score", 0) for result in results.values() if isinstance(result, dict)]
            results["overall_score"] = sum(scores) / len(scores) if scores else 0
            
            # Standardize results
            standardized_results = self._standardize_results(results)
            
            # Save to JSON
            json_path = self.save_to_json(standardized_results, url, "performance")
            
            return json.dumps({
                "results": standardized_results,
                "json_path": json_path
            }, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Performance analysis failed: {str(e)}")
            raise AnalysisError(f"Performance analysis failed: {str(e)}")
    
    @async_timed()
    async def _check_core_web_vitals(self, page: Page) -> Dict[str, Any]:
        """Check Core Web Vitals metrics."""
        try:
            # Run all measurements concurrently
            lcp, fid, cls = await asyncio.gather(
                self._measure_lcp(page),
                self._measure_fid(page),
                self._measure_cls(page)
            )
            
            issues = []
            if lcp > 2500:
                issues.append(f"LCP is too high ({lcp:.2f}ms)")
            if fid > 100:
                issues.append(f"FID is too high ({fid:.2f}ms)")
            if cls > 0.1:
                issues.append(f"CLS is too high ({cls:.3f})")
            
            return {
                "score": self._calculate_vitals_score(lcp, fid, cls),
                "metrics": {
                    "lcp": lcp,
                    "fid": fid,
                    "cls": cls
                },
                "issues": issues
            }
        except Exception as e:
            logger.error(f"Core Web Vitals check failed: {str(e)}")
            raise
    
    async def _measure_lcp(self, page: Page) -> float:
        """Measure Largest Contentful Paint."""
        return await page.evaluate("""
            () => new Promise((resolve) => {
                let lcp = 0;
                new PerformanceObserver((entryList) => {
                    const entries = entryList.getEntries();
                    const lastEntry = entries[entries.length - 1];
                    lcp = lastEntry.startTime;
                }).observe({ entryTypes: ['largest-contentful-paint'] });
                
                // Resolve after a reasonable timeout
                setTimeout(() => resolve(lcp), 5000);
            });
        """)
    
    async def _measure_fid(self, page: Page) -> float:
        """Measure First Input Delay."""
        return await page.evaluate("""
            () => new Promise((resolve) => {
                let fid = 0;
                new PerformanceObserver((entryList) => {
                    const entries = entryList.getEntries();
                    if (entries.length > 0) {
                        fid = entries[0].duration;
                    }
                }).observe({ entryTypes: ['first-input'] });
                
                // Resolve after a reasonable timeout
                setTimeout(() => resolve(fid), 5000);
            });
        """)
    
    async def _measure_cls(self, page: Page) -> float:
        """Measure Cumulative Layout Shift."""
        return await page.evaluate("""
            () => new Promise((resolve) => {
                let cls = 0;
                new PerformanceObserver((entryList) => {
                    for (const entry of entryList.getEntries()) {
                        if (!entry.hadRecentInput) {
                            cls += entry.value;
                        }
                    }
                }).observe({ entryTypes: ['layout-shift'] });
                
                // Resolve after a reasonable timeout
                setTimeout(() => resolve(cls), 5000);
            });
        """)
    
    def _calculate_vitals_score(self, lcp: float, fid: float, cls: float) -> float:
        """Calculate Core Web Vitals score."""
        lcp_score = 100 if lcp <= 2500 else (75 if lcp <= 4000 else 0)
        fid_score = 100 if fid <= 100 else (75 if fid <= 300 else 0)
        cls_score = 100 if cls <= 0.1 else (75 if cls <= 0.25 else 0)
        return (lcp_score + fid_score + cls_score) / 3
    
    @async_timed()
    async def _check_resource_optimization(self, page: Page) -> Dict[str, Any]:
        """Check resource optimization."""
        try:
            # Run checks concurrently
            images, scripts, styles = await asyncio.gather(
                self._analyze_images(page),
                self._analyze_scripts(page),
                self._analyze_styles(page)
            )
            
            issues = []
            issues.extend(images["issues"])
            issues.extend(scripts["issues"])
            issues.extend(styles["issues"])
            
            return {
                "score": max(100 - len(issues) * 10, 0),
                "issues": issues,
                "details": {
                    "images": images["details"],
                    "scripts": scripts["details"],
                    "styles": styles["details"]
                }
            }
        except Exception as e:
            logger.error(f"Resource optimization check failed: {str(e)}")
            raise
    
    async def _analyze_images(self, page: Page) -> Dict[str, Any]:
        """Analyze image optimization."""
        images = await page.evaluate("""
            () => {
                const images = document.querySelectorAll('img');
                return Array.from(images).map(img => ({
                    src: img.src,
                    width: img.naturalWidth,
                    height: img.naturalHeight,
                    displayWidth: img.width,
                    displayHeight: img.height,
                    loading: img.loading,
                    srcset: img.srcset
                }));
            }
        """)
        
        issues = []
        for img in images:
            if img["width"] > img["displayWidth"] * 2:
                issues.append(f"Image {img['src']} is too large for its display size")
            if not img["loading"] == "lazy" and not img["srcset"]:
                issues.append(f"Image {img['src']} should use lazy loading or responsive images")
        
        return {
            "issues": issues,
            "details": {
                "total_images": len(images),
                "oversized_images": len([i for i in images if i["width"] > i["displayWidth"] * 2]),
                "non_optimized_images": len([i for i in images if not i["loading"] == "lazy" and not i["srcset"]])
            }
        }
    
    async def _analyze_scripts(self, page: Page) -> Dict[str, Any]:
        """Analyze script optimization."""
        scripts = await page.evaluate("""
            () => {
                const scripts = document.querySelectorAll('script');
                return Array.from(scripts).map(script => ({
                    src: script.src,
                    async: script.async,
                    defer: script.defer,
                    type: script.type,
                    size: script.innerHTML.length
                }));
            }
        """)
        
        issues = []
        for script in scripts:
            if script["src"] and not (script["async"] or script["defer"]):
                issues.append(f"Script {script['src']} should be async or deferred")
            if script["size"] > 50000:
                issues.append(f"Script {script['src'] or 'inline'} is too large ({script['size']} bytes)")
        
        return {
            "issues": issues,
            "details": {
                "total_scripts": len(scripts),
                "blocking_scripts": len([s for s in scripts if s["src"] and not (s["async"] or s["defer"])]),
                "large_scripts": len([s for s in scripts if s["size"] > 50000])
            }
        }
    
    async def _analyze_styles(self, page: Page) -> Dict[str, Any]:
        """Analyze style optimization."""
        styles = await page.evaluate("""
            () => {
                const links = document.querySelectorAll('link[rel="stylesheet"]');
                const styles = document.querySelectorAll('style');
                return {
                    links: Array.from(links).map(link => ({
                        href: link.href,
                        media: link.media
                    })),
                    inlineStyles: Array.from(styles).map(style => ({
                        size: style.innerHTML.length,
                        media: style.media
                    }))
                };
            }
        """)
        
        issues = []
        for link in styles["links"]:
            if not link["media"]:
                issues.append(f"Stylesheet {link['href']} should use media queries for optimization")
        
        for style in styles["inlineStyles"]:
            if style["size"] > 50000:
                issues.append(f"Inline style is too large ({style['size']} bytes)")
        
        return {
            "issues": issues,
            "details": {
                "total_stylesheets": len(styles["links"]),
                "total_inline_styles": len(styles["inlineStyles"]),
                "non_optimized_stylesheets": len([s for s in styles["links"] if not s["media"]])
            }
        }
    
    @async_timed()
    async def _check_caching(self, page: Page) -> Dict[str, Any]:
        """Check caching configuration."""
        try:
            response = await page.goto(page.url)
            headers = response.headers
            
            issues = []
            cache_score = 100
            
            # Check cache headers
            if "Cache-Control" not in headers:
                issues.append("Missing Cache-Control header")
                cache_score -= 30
            else:
                cache_control = headers["Cache-Control"]
                if "no-store" in cache_control or "no-cache" in cache_control:
                    issues.append("Cache-Control prevents caching")
                    cache_score -= 20
                elif "max-age" not in cache_control:
                    issues.append("Cache-Control missing max-age directive")
                    cache_score -= 10
            
            if "ETag" not in headers and "Last-Modified" not in headers:
                issues.append("Missing ETag and Last-Modified headers")
                cache_score -= 20
            
            return {
                "score": max(cache_score, 0),
                "issues": issues,
                "headers": dict(headers)
            }
        except Exception as e:
            logger.error(f"Caching check failed: {str(e)}")
            raise
    
    @async_timed()
    async def _check_rendering_performance(self, page: Page) -> Dict[str, Any]:
        """Check rendering performance."""
        try:
            metrics = await page.evaluate("""
                () => {
                    const paint = performance.getEntriesByType('paint');
                    const navigation = performance.getEntriesByType('navigation')[0];
                    const resources = performance.getEntriesByType('resource');
                    
                    return {
                        fcp: paint.find(p => p.name === 'first-contentful-paint')?.startTime,
                        domComplete: navigation.domComplete,
                        renderBlocking: resources.filter(r => r.renderBlocking === 'blocking').length,
                        resourceCount: resources.length,
                        totalBlockingTime: performance.now() - navigation.responseEnd
                    };
                }
            """)
            
            issues = []
            if metrics["fcp"] > 1000:
                issues.append(f"First Contentful Paint is too high ({metrics['fcp']:.2f}ms)")
            if metrics["renderBlocking"] > 0:
                issues.append(f"Found {metrics['renderBlocking']} render-blocking resources")
            if metrics["totalBlockingTime"] > 300:
                issues.append(f"Total Blocking Time is too high ({metrics['totalBlockingTime']:.2f}ms)")
            
            return {
                "score": max(100 - len(issues) * 20, 0),
                "issues": issues,
                "metrics": metrics
            }
        except Exception as e:
            logger.error(f"Rendering performance check failed: {str(e)}")
            raise
    
    @async_timed()
    async def _check_network_performance(self, page: Page) -> Dict[str, Any]:
        """Check network performance."""
        try:
            timing = await page.evaluate("""
                () => {
                    const navigation = performance.getEntriesByType('navigation')[0];
                    const resources = performance.getEntriesByType('resource');
                    
                    return {
                        dns: navigation.domainLookupEnd - navigation.domainLookupStart,
                        tcp: navigation.connectEnd - navigation.connectStart,
                        ttfb: navigation.responseStart - navigation.requestStart,
                        download: navigation.responseEnd - navigation.responseStart,
                        totalResources: resources.length,
                        totalSize: resources.reduce((sum, r) => sum + r.transferSize, 0),
                        compression: resources.reduce((sum, r) => sum + (r.encodedBodySize / r.decodedBodySize), 0) / resources.length
                    };
                }
            """)
            
            issues = []
            if timing["dns"] > 100:
                issues.append(f"DNS lookup time is too high ({timing['dns']:.2f}ms)")
            if timing["tcp"] > 100:
                issues.append(f"TCP connection time is too high ({timing['tcp']:.2f}ms)")
            if timing["ttfb"] > 200:
                issues.append(f"Time to First Byte is too high ({timing['ttfb']:.2f}ms)")
            if timing["totalSize"] > 5000000:
                issues.append(f"Total page size is too large ({timing['totalSize'] / 1000000:.2f}MB)")
            
            return {
                "score": max(100 - len(issues) * 20, 0),
                "metrics": timing,
                "issues": issues
            }
        except Exception as e:
            logger.error(f"Network performance check failed: {str(e)}")
            raise
    
    @async_timed()
    async def _check_mobile_performance(self, page: Page) -> Dict[str, Any]:
        """Check mobile performance."""
        try:
            # Set mobile viewport
            await page.set_viewport_size({"width": 375, "height": 667})
            
            # Run mobile-specific checks concurrently
            viewport_check, touch_targets, content_width = await asyncio.gather(
                self._check_viewport_meta(page),
                self._check_touch_targets(page),
                self._check_content_width(page)
            )
            
            issues = []
            if not viewport_check:
                issues.append("Missing proper mobile viewport meta tag")
            
            if touch_targets["small_targets"] > 0:
                issues.append(f"Found {touch_targets['small_targets']} touch targets that are too small")
            
            if content_width["overflow"]:
                issues.append("Content width causes horizontal scrolling on mobile")
            
            return {
                "score": max(100 - len(issues) * 20, 0),
                "issues": issues,
                "metrics": {
                    "touch_targets": touch_targets,
                    "content_width": content_width
                }
            }
        except Exception as e:
            logger.error(f"Mobile performance check failed: {str(e)}")
            raise
    
    async def _check_viewport_meta(self, page: Page) -> bool:
        """Check for proper mobile viewport meta tag."""
        return await page.evaluate("""
            () => {
                const meta = document.querySelector('meta[name="viewport"]');
                return meta && meta.content.includes('width=device-width');
            }
        """)
    
    async def _check_touch_targets(self, page: Page) -> Dict[str, Any]:
        """Check for properly sized touch targets."""
        return await page.evaluate("""
            () => {
                const targets = document.querySelectorAll('a, button, input, select');
                const smallTargets = Array.from(targets).filter(el => {
                    const rect = el.getBoundingClientRect();
                    return rect.width < 44 || rect.height < 44;
                });
                
                return {
                    total_targets: targets.length,
                    small_targets: smallTargets.length,
                    small_target_details: smallTargets.map(el => ({
                        tag: el.tagName.toLowerCase(),
                        width: el.getBoundingClientRect().width,
                        height: el.getBoundingClientRect().height
                    }))
                };
            }
        """)
    
    async def _check_content_width(self, page: Page) -> Dict[str, Any]:
        """Check for content width issues on mobile."""
        return await page.evaluate("""
            () => {
                const viewport = {
                    width: window.innerWidth,
                    height: window.innerHeight
                };
                const content = {
                    width: document.documentElement.scrollWidth,
                    height: document.documentElement.scrollHeight
                };
                return {
                    viewport: viewport,
                    content: content,
                    overflow: content.width > viewport.width
                };
            }
        """)

    def _analyze_page_size(self, html: str) -> Dict[str, Any]:
        """Analyze the page size and provide recommendations."""
        try:
            size_bytes = len(html.encode('utf-8'))
            size_kb = size_bytes / 1024
            
            return {
                "score": 1.0 if size_kb < 100 else 0.5,
                "issues": [] if size_kb < 100 else [f"Large page size: {size_kb:.2f} KB"],
                "recommendations": [] if size_kb < 100 else ["Optimize page size"],
                "details": {
                    "size_bytes": size_bytes,
                    "size_kb": size_kb
                }
            }
        except Exception as e:
            logger.error(f"Error analyzing page size: {str(e)}")
            return {
                "score": 0,
                "issues": [f"Error analyzing page size: {str(e)}"],
                "recommendations": ["Fix page size analysis"],
                "details": {"error": str(e)}
            }

    def _analyze_resource_loading(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Analyze resource loading patterns."""
        try:
            # Count async/defer scripts
            scripts = soup.find_all('script')
            async_scripts = sum(1 for s in scripts if s.get('async') or s.get('defer'))
            
            # Count preloaded resources
            preloads = len(soup.find_all('link', rel='preload'))
            
            return {
                "score": 1.0 if async_scripts > 0 or preloads > 0 else 0.5,
                "issues": [] if async_scripts > 0 or preloads > 0 else ["No resource optimization found"],
                "recommendations": [] if async_scripts > 0 or preloads > 0 else ["Optimize resource loading"],
                "details": {
                    "async_scripts": async_scripts,
                    "preloads": preloads
                }
            }
        except Exception as e:
            logger.error(f"Error analyzing resource loading: {str(e)}")
            return {
                "score": 0,
                "issues": [f"Error analyzing resource loading: {str(e)}"],
                "recommendations": ["Fix resource loading analysis"],
                "details": {"error": str(e)}
            }

    def _analyze_render_blocking(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Analyze render-blocking resources."""
        try:
            # Count render-blocking resources
            blocking_css = len(soup.find_all('link', rel='stylesheet'))
            blocking_js = len(soup.find_all('script', attrs={'defer': False, 'async': False}))
            
            return {
                "score": 1.0 if blocking_css + blocking_js < 3 else 0.5,
                "issues": [] if blocking_css + blocking_js < 3 else ["Too many render-blocking resources"],
                "recommendations": [] if blocking_css + blocking_js < 3 else ["Reduce render-blocking resources"],
                "details": {
                    "blocking_css": blocking_css,
                    "blocking_js": blocking_js
                }
            }
        except Exception as e:
            logger.error(f"Error analyzing render blocking: {str(e)}")
            return {
                "score": 0,
                "issues": [f"Error analyzing render blocking: {str(e)}"],
                "recommendations": ["Fix render blocking analysis"],
                "details": {"error": str(e)}
            }

    def _analyze_caching(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Analyze caching configuration."""
        try:
            # Check for cache-control meta tags
            cache_meta = len(soup.find_all('meta', attrs={'http-equiv': 'cache-control'}))
            
            return {
                "score": 1.0 if cache_meta > 0 else 0.5,
                "issues": [] if cache_meta > 0 else ["No cache-control meta tags found"],
                "recommendations": [] if cache_meta > 0 else ["Add cache-control meta tags"],
                "details": {
                    "cache_meta_tags": cache_meta
                }
            }
        except Exception as e:
            logger.error(f"Error analyzing caching: {str(e)}")
            return {
                "score": 0,
                "issues": [f"Error analyzing caching: {str(e)}"],
                "recommendations": ["Fix caching analysis"],
                "details": {"error": str(e)}
            }

    def _analyze_compression(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Analyze compression usage."""
        try:
            # Check for compressed resources
            compressed = len(soup.find_all(['script', 'link', 'img'], attrs={'data-compressed': True}))
            total = len(soup.find_all(['script', 'link', 'img']))
            
            compression_ratio = compressed / total if total > 0 else 0
            
            return {
                "score": 1.0 if compression_ratio >= 0.5 else 0.5,
                "issues": [] if compression_ratio >= 0.5 else ["Low compression usage"],
                "recommendations": [] if compression_ratio >= 0.5 else ["Enable compression for more resources"],
                "details": {
                    "compressed_resources": compressed,
                    "total_resources": total,
                    "compression_ratio": compression_ratio
                }
            }
        except Exception as e:
            logger.error(f"Error analyzing compression: {str(e)}")
            return {
                "score": 0,
                "issues": [f"Error analyzing compression: {str(e)}"],
                "recommendations": ["Fix compression analysis"],
                "details": {"error": str(e)}
            }

    def _standardize_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Standardize the analysis results."""
        standardized = {
            "overall_score": results.get("overall_score", 0),
            "issues": [],
            "recommendations": [],
            "metrics": {},
            "details": {}
        }
        
        for key, result in results.items():
            if isinstance(result, dict):
                standardized["issues"].extend(result.get("issues", []))
                standardized["recommendations"].extend(result.get("recommendations", []))
                standardized["metrics"][key] = {
                    "score": result.get("score", 0),
                    "details": result.get("details", {})
                }
                standardized["details"][key] = result
        
        return standardized

    def save_to_json(self, results: Dict[str, Any], url: str, analysis_type: str) -> str:
        """Save analysis results to a JSON file."""
        try:
            # Create filename from URL and analysis type
            filename = f"{url.replace('https://', '').replace('http://', '').replace('/', '_')}_{analysis_type}.json"
            
            # Save to file
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            return filename
        except Exception as e:
            logger.error(f"Error saving results to JSON: {str(e)}")
            return ""