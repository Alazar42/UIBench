from typing import Dict, List, Optional, Any, Callable, AsyncGenerator
from playwright.async_api import Page
from bs4 import BeautifulSoup
import asyncio
import logging
from datetime import datetime
import time
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

from ..utils.error_handler import AnalysisError
from ..utils.performance_utils import async_timed, PerformanceMonitor
from ..utils.cache import AnalysisCache
from ..config import Settings

logger = logging.getLogger(__name__)
config = Settings()
console = Console()

class AccessibilityAnalyzer:
    """Analyzes web pages for accessibility compliance and best practices."""
    
    def __init__(self):
        self.performance_monitor = PerformanceMonitor()
        self.cache = AnalysisCache()
        self.console = Console()
    
    def _format_score(self, score: float) -> Text:
        """Format score with color based on value."""
        if score >= 90:
            return Text(f"{score:.1f}", style="bold green")
        elif score >= 70:
            return Text(f"{score:.1f}", style="bold yellow")
        else:
            return Text(f"{score:.1f}", style="bold red")
    
    def _create_progress_table(self, results: Dict[str, Any]) -> Table:
        """Create a rich table for progress display."""
        table = Table(box=box.ROUNDED, show_header=True, header_style="bold magenta")
        table.add_column("Category", style="cyan")
        table.add_column("Score", justify="right")
        table.add_column("Issues", justify="right")
        table.add_column("Passes", justify="right")
        table.add_column("Status", style="bold")
        
        for category, data in results.items():
            if not isinstance(data, dict):
                continue
                
            score_data = data.get("score", {})
            if isinstance(score_data, dict):
                score = score_data.get("score", 0)
            else:
                score = score_data
                
            issues = len(data.get("issues", []))
            passes = len(data.get("passes", []))
            
            status = "✓" if score >= 90 else "⚠" if score >= 70 else "✗"
            status_style = "green" if score >= 90 else "yellow" if score >= 70 else "red"
            
            table.add_row(
                category.replace("_", " ").title(),
                self._format_score(score),
                str(issues),
                str(passes),
                Text(status, style=status_style)
            )
        
        return table
    
    def print_progress(self, update: Dict[str, Any]) -> None:
        """Print progress updates to terminal with rich formatting."""
        update_type = update.get("type")
        timestamp = update.get("timestamp", "")
        
        if update_type == "step_start":
            self.console.print(Panel(
                f"[bold cyan]Starting {update['category'].replace('_', ' ').title()} analysis...[/]",
                border_style="cyan"
            ))
        elif update_type == "step_complete":
            result = update.get("result", {})
            score = result.get("score", {}).get("score", 0)
            issues = len(result.get("issues", []))
            passes = len(result.get("passes", []))
            
            self.console.print(Panel(
                f"[bold green]✓ {update['category'].replace('_', ' ').title()} analysis complete[/]\n"
                f"Score: {self._format_score(score)}\n"
                f"Issues: {issues}\n"
                f"Passes: {passes}",
                border_style="green"
            ))
        elif update_type == "step_error":
            self.console.print(Panel(
                f"[bold red]✗ Error in {update['category'].replace('_', ' ').title()} analysis[/]\n"
                f"Error: {update['error']}",
                border_style="red"
            ))
        elif update_type == "analysis_complete":
            results = update.get("results", {})
            overall_score = results.get("overall_score", 0)
            
            self.console.print("\n")
            self.console.print(Panel(
                f"[bold green]Analysis Complete![/]\n"
                f"Overall Score: {self._format_score(overall_score)}",
                border_style="green"
            ))
            
            # Display detailed results table
            self.console.print("\nDetailed Results:")
            self.console.print(self._create_progress_table(results))
            
            # Display recommendations
            recommendations = results.get("detailed_report", {}).get("recommendations", [])
            if recommendations:
                self.console.print("\nRecommendations:")
                for rec in recommendations:
                    priority_style = {
                        "high": "red",
                        "medium": "yellow",
                        "low": "blue"
                    }.get(rec["priority"], "white")
                    
                    self.console.print(Panel(
                        f"[bold {priority_style}]{rec['issue']}[/]\n"
                        f"Help: {rec['help']}",
                        border_style=priority_style
                    ))
        elif update_type == "analysis_error":
            self.console.print(Panel(
                f"[bold red]Analysis Failed[/]\n"
                f"Error: {update['error']}",
                border_style="red"
            ))
        elif update_type == "cached_result":
            self.console.print(Panel(
                "[bold yellow]Using cached results[/]",
                border_style="yellow"
            ))
    
    async def analyze_with_progress(self, url: str, page: Page) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Analyze with progress updates using async generator and progress bar.
        
        Args:
            url: Target URL
            page: Playwright page object
            
        Yields:
            Dict containing progress updates and results
        """
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeRemainingColumn(),
            console=self.console
        ) as progress:
            # Create main task
            main_task = progress.add_task("[cyan]Running accessibility analysis...", total=100)
            
            # Define analysis steps
            analysis_steps = [
                ("images", self._check_images),
                ("headings", self._check_headings),
                ("forms", self._check_forms),
                ("aria", self._check_aria),
                ("keyboard_navigation", self._check_keyboard_navigation),
                ("color_contrast", self._check_color_contrast)
            ]
            
            step_progress = 100 / len(analysis_steps)
            results = {}
            
            try:
                # Check cache first
                cache_key = f"accessibility_{url}"
                cached_result = await self.cache.get_analysis(url, "accessibility")
                if cached_result:
                    yield {
                        "type": "cached_result",
                        "timestamp": datetime.now().isoformat(),
                        "results": cached_result
                    }
                    return
                
                for category, check_func in analysis_steps:
                    # Yield step start
                    yield {
                        "type": "step_start",
                        "timestamp": datetime.now().isoformat(),
                        "category": category
                    }
                    progress.update(main_task, advance=step_progress/2)
                    
                    try:
                        result = await check_func(page)
                        results[category] = result
                        
                        # Yield step complete
                        yield {
                            "type": "step_complete",
                            "timestamp": datetime.now().isoformat(),
                            "category": category,
                            "result": result
                        }
                        progress.update(main_task, advance=step_progress/2)
                        
                    except Exception as e:
                        # Yield step error
                        yield {
                            "type": "step_error",
                            "timestamp": datetime.now().isoformat(),
                            "category": category,
                            "error": str(e)
                        }
                        logger.error(f"Error in {category} analysis: {str(e)}")
                        continue
                
                # Calculate overall results
                overall_results = self._generate_report(results)
                
                # Cache results
                await self.cache.cache_analysis(url, "accessibility", overall_results)
                
                # Yield final results
                yield {
                    "type": "analysis_complete",
                    "timestamp": datetime.now().isoformat(),
                    "results": overall_results
                }
                progress.update(main_task, completed=100)
                
            except Exception as e:
                yield {
                    "type": "analysis_error",
                    "timestamp": datetime.now().isoformat(),
                    "error": str(e)
                }
                logger.error(f"Analysis failed: {str(e)}")
                raise AnalysisError(f"Accessibility analysis failed: {str(e)}")

    @async_timed()
    async def analyze(self, url: str, page: Page, callback: Optional[Callable[[Dict[str, Any]], None]] = None) -> Dict[str, Any]:
        """
        Perform comprehensive accessibility analysis with step-by-step results.
        
        Args:
            url: Target URL
            page: Playwright page object
            callback: Optional callback function to receive results as they become available
            
        Returns:
            Dict containing accessibility analysis results
        """
        try:
            # Check cache first
            cached_result = self.cache.get_result(url, "accessibility")
            if cached_result and self.cache.is_valid(cached_result):
                if callback:
                    callback({
                        "type": "cached_result",
                        "data": cached_result.results
                    })
                return cached_result.results
            
            with self.performance_monitor.monitor("accessibility_analysis"):
                analysis_results = {}
                
                # Define analysis steps
                analysis_steps = [
                    ("images", self._check_images),
                    ("headings", self._check_headings),
                    ("forms", self._check_forms),
                    ("aria", self._check_aria),
                    ("keyboard_navigation", self._check_keyboard_navigation),
                    ("color_contrast", self._check_color_contrast)
                ]
                
                # Process each step sequentially
                for category, check_func in analysis_steps:
                    try:
                        # Send start notification
                        if callback:
                            callback({
                                "type": "step_start",
                                "category": category,
                                "timestamp": datetime.now().isoformat()
                            })
                        
                        # Run the check
                        result = await check_func(page)
                        
                        # Process and store result
                        analysis_results[category] = result
                        
                        # Calculate current overall score
                        valid_scores = [
                            r.get("score", {}).get("score", 0)
                            for r in analysis_results.values()
                            if isinstance(r, dict)
                        ]
                        current_score = (
                            sum(valid_scores) / len(valid_scores)
                            if valid_scores else 0
                        )
                        
                        # Send step completion notification
                        if callback:
                            callback({
                                "type": "step_complete",
                                "category": category,
                                "result": result,
                                "current_score": current_score,
                                "timestamp": datetime.now().isoformat()
                            })
                            
                    except Exception as e:
                        logger.error(f"Error in {category} analysis: {str(e)}")
                        error_result = {
                            "score": self._calculate_score([], [], 0),
                            "error": str(e),
                            "issues": [f"Analysis failed: {str(e)}"]
                        }
                        analysis_results[category] = error_result
                        
                        if callback:
                            callback({
                                "type": "step_error",
                                "category": category,
                                "error": str(e),
                                "timestamp": datetime.now().isoformat()
                            })
                
                # Add performance metrics
                analysis_results["analysis_performance"] = {
                    "execution_time": self.performance_monitor.get_average_execution_time("accessibility_analysis"),
                    "memory_usage": self.performance_monitor.get_peak_memory_usage("accessibility_analysis")
                }
                
                # Generate detailed report
                analysis_results["detailed_report"] = self._generate_report(analysis_results)
                
                # Cache the results
                self.cache.store_result({
                    "analyzer_id": "accessibility",
                    "url": url,
                    "timestamp": datetime.now(),
                    "results": analysis_results,
                    "metadata": {},
                    "version": "1.0.0"
                })
                
                # Send final completion notification
                if callback:
                    callback({
                        "type": "analysis_complete",
                        "results": analysis_results,
                        "timestamp": datetime.now().isoformat()
                    })
                
                return analysis_results
                
        except Exception as e:
            logger.error(f"Accessibility analysis failed: {str(e)}")
            if callback:
                callback({
                    "type": "analysis_error",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
            raise AnalysisError(f"Accessibility analysis failed: {str(e)}")

    def _calculate_score(self, issues: List[Dict[str, Any]], passes: List[Dict[str, Any]], total_elements: int) -> Dict[str, Any]:
        """Calculate a weighted score based on issues and passes with detailed breakdown."""
        if not total_elements:
            return {
                "score": 100.0,
                "breakdown": {
                    "base_score": 100,
                    "issue_penalty": 0,
                    "pass_bonus": 0,
                    "impact_breakdown": {
                        "serious": 0,
                        "moderate": 0,
                        "minor": 0
                    }
                }
            }
            
        # Define impact weights and penalties
        impact_weights = {
            'serious': 1.0,
            'moderate': 0.7,
            'minor': 0.3
        }
        
        impact_penalties = {
            'serious': 20,
            'moderate': 10,
            'minor': 5
        }
        
        # Calculate impact breakdown
        impact_breakdown = {
            'serious': 0,
            'moderate': 0,
            'minor': 0
        }
        
        for issue in issues:
            impact = issue.get('impact', 'moderate')
            impact_breakdown[impact] = impact_breakdown.get(impact, 0) + 1
        
        # Calculate weighted issue score
        issue_score = sum(
            impact_weights.get(issue.get('impact', 'moderate'), 0.7)
            for issue in issues
        )
        
        # Calculate issue penalties
        issue_penalty = sum(
            impact_penalties.get(issue.get('impact', 'moderate'), 10)
            for issue in issues
        )
        
        # Calculate pass score with diminishing returns
        pass_count = len(passes)
        pass_bonus = min(pass_count * 5, 50)  # Cap pass bonus at 50
        
        # Calculate base score
        base_score = 100
        
        # Calculate final score with weighted components
        final_score = max(0, min(100, base_score - issue_penalty + pass_bonus))
        
        return {
            "score": final_score,
            "breakdown": {
                "base_score": base_score,
                "issue_penalty": issue_penalty,
                "pass_bonus": pass_bonus,
                "impact_breakdown": impact_breakdown,
                "weighted_components": {
                    "issue_weight": issue_score,
                    "pass_weight": pass_count / total_elements if total_elements > 0 else 0
                }
            }
        }

    def _generate_report(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a detailed accessibility report."""
        # Calculate overall score from individual category scores
        valid_scores = []
        total_issues = 0
        total_passes = 0
        category_details = {}
        
        for category, data in results.items():
            if not isinstance(data, dict) or category in ['analysis_performance', 'detailed_report']:
                continue
                
            score_data = data.get("score", {})
            if isinstance(score_data, dict):
                score = score_data.get("score", 0)
                breakdown = score_data.get("breakdown", {})
            else:
                score = score_data
                breakdown = {}
            
            if score is not None:
                valid_scores.append(score)
            
            issues = len(data.get("issues", []))
            passes = len(data.get("passes", []))
            total_issues += issues
            total_passes += passes
            
            category_details[category] = {
                "score": score,
                "issues": issues,
                "passes": passes,
                "impact_breakdown": breakdown.get("impact_breakdown", {}),
                "score_breakdown": breakdown,
                "details": data.get("details", {})
            }
        
        overall_score = sum(valid_scores) / len(valid_scores) if valid_scores else 0
        
        report = {
            "summary": {
                "overall_score": overall_score,
                "total_issues": total_issues,
                "total_passes": total_passes,
                "categories_analyzed": list(category_details.keys())
            },
            "category_details": category_details,
            "recommendations": [],
            "performance_metrics": results.get("analysis_performance", {})
        }
        
        # Generate recommendations based on issues
        for category, data in category_details.items():
            for issue in data.get("details", {}).get("issues", []):
                recommendation = {
                    "category": category,
                    "issue": issue.get("description", ""),
                    "help": issue.get("help", ""),
                    "impact": issue.get("impact", "moderate"),
                    "priority": "high" if issue.get("impact") == "serious" else "medium"
                }
                report["recommendations"].append(recommendation)
        
        # Sort recommendations by priority
        report["recommendations"].sort(
            key=lambda x: {"high": 0, "medium": 1, "low": 2}.get(x["priority"], 3)
        )
        
        return report

    @async_timed()
    async def _check_images(self, page: Page) -> Dict[str, Any]:
        """Check image accessibility."""
        try:
            images = await page.query_selector_all('img')
            issues = []
            passes = []
            
            for img in images:
                alt = await img.get_attribute('alt')
                role = await img.get_attribute('role')
                aria_label = await img.get_attribute('aria-label')
                
                if not alt and not role and not aria_label:
                    issues.append({
                        'id': 'img-alt',
                        'impact': 'serious',
                        'description': 'Image missing alt text or ARIA label',
                        'help': 'Add alt text or ARIA label to images',
                        'nodes': [{'html': await img.evaluate('el => el.outerHTML')}]
                    })
                else:
                    passes.append({
                        'id': 'img-alt',
                        'impact': 'none',
                        'description': 'Image has accessibility attributes',
                        'help': 'Accessibility attributes are present',
                        'nodes': [{'html': await img.evaluate('el => el.outerHTML')}]
                    })
            
            return {
                "score": self._calculate_score(issues, passes, len(images)),
                "issues": issues,
                "passes": passes,
                "details": {
                    "total_images": len(images),
                    "images_with_alt": len(passes),
                    "images_without_alt": len(issues),
                    "score_breakdown": {
                        "base_score": 100,
                        "issue_penalty": len(issues) * 20,
                        "pass_bonus": len(passes) * 5
                    }
                }
            }
        except Exception as e:
            logger.error(f"Image accessibility check failed: {str(e)}")
            raise
    
    @async_timed()
    async def _check_headings(self, page: Page) -> Dict[str, Any]:
        """Check heading structure."""
        try:
            headings = await page.query_selector_all('h1, h2, h3, h4, h5, h6')
            issues = []
            passes = []
            
            if not headings:
                issues.append({
                    'id': 'heading-structure',
                    'impact': 'serious',
                    'description': 'No headings found on the page',
                    'help': 'Add headings to structure the content',
                    'nodes': [{'html': await page.content()}]
                })
            else:
                # Check heading hierarchy
                prev_level = 0
                for heading in headings:
                    level = int(await heading.evaluate('el => parseInt(el.tagName[1])'))
                    if level - prev_level > 1:
                        issues.append({
                            'id': 'heading-hierarchy',
                            'impact': 'moderate',
                            'description': f'Heading level skipped from h{prev_level} to h{level}',
                            'help': 'Maintain proper heading hierarchy',
                            'nodes': [{'html': await heading.evaluate('el => el.outerHTML')}]
                        })
                    prev_level = level
                    passes.append({
                        'id': 'heading-structure',
                        'impact': 'none',
                        'description': 'Heading structure is valid',
                        'help': 'Heading structure is present',
                        'nodes': [{'html': await heading.evaluate('el => el.outerHTML')}]
                    })
            
            return {
                "score": self._calculate_score(issues, passes, len(headings)),
                "issues": issues,
                "passes": passes,
                "details": {
                    "total_headings": len(headings),
                    "valid_headings": len(passes),
                    "invalid_headings": len(issues),
                    "score_breakdown": {
                        "base_score": 100,
                        "issue_penalty": len(issues) * 20,
                        "pass_bonus": len(passes) * 5
                    }
                }
            }
        except Exception as e:
            logger.error(f"Heading structure check failed: {str(e)}")
            raise
    
    @async_timed()
    async def _check_forms(self, page: Page) -> Dict[str, Any]:
        """Check form accessibility."""
        try:
            inputs = await page.query_selector_all('input, select, textarea')
            issues = []
            passes = []
            
            for input_elem in inputs:
                label = await input_elem.evaluate('el => el.labels?.[0]?.textContent')
                aria_label = await input_elem.get_attribute('aria-label')
                id = await input_elem.get_attribute('id')
                
                if not label and not aria_label and not id:
                    issues.append({
                        'id': 'form-label',
                        'impact': 'serious',
                        'description': 'Form control missing label',
                        'help': 'Add labels to form controls',
                        'nodes': [{'html': await input_elem.evaluate('el => el.outerHTML')}]
                    })
                else:
                    passes.append({
                        'id': 'form-label',
                        'impact': 'none',
                        'description': 'Form control has label',
                        'help': 'Label is present',
                        'nodes': [{'html': await input_elem.evaluate('el => el.outerHTML')}]
                    })
            
            return {
                "score": self._calculate_score(issues, passes, len(inputs)),
                "issues": issues,
                "passes": passes,
                "details": {
                    "total_controls": len(inputs),
                    "labeled_controls": len(passes),
                    "unlabeled_controls": len(issues),
                    "score_breakdown": {
                        "base_score": 100,
                        "issue_penalty": len(issues) * 20,
                        "pass_bonus": len(passes) * 5
                    }
                }
            }
        except Exception as e:
            logger.error(f"Form accessibility check failed: {str(e)}")
            raise
    
    @async_timed()
    async def _check_aria(self, page: Page) -> Dict[str, Any]:
        """Check ARIA attributes."""
        try:
            # Get elements with role attribute first
            role_elements = await page.query_selector_all('[role]')
            
            # Get elements with aria attributes using JavaScript evaluation
            aria_elements = await page.evaluate("""() => {
                return Array.from(document.querySelectorAll('*')).filter(el => {
                    return Array.from(el.attributes).some(attr => attr.name.startsWith('aria-'));
                });
            }""")
            
            # Combine unique elements
            elements = list(set(role_elements + aria_elements))
            issues = []
            passes = []
            
            for elem in elements:
                role = await elem.get_attribute('role')
                aria_attrs = await elem.evaluate("""el => {
                    const attrs = {};
                    for (const attr of el.attributes) {
                        if (attr.name.startsWith("aria-")) {
                            attrs[attr.name] = attr.value;
                        }
                    }
                    return attrs;
                }""")
                
                if role and not aria_attrs:
                    issues.append({
                        'id': 'aria-attributes',
                        'impact': 'moderate',
                        'description': 'Element has role but missing required ARIA attributes',
                        'help': 'Add required ARIA attributes for the role',
                        'nodes': [{'html': await elem.evaluate('el => el.outerHTML')}]
                    })
                else:
                    passes.append({
                        'id': 'aria-attributes',
                        'impact': 'none',
                        'description': 'ARIA attributes are valid',
                        'help': 'ARIA attributes are present',
                        'nodes': [{'html': await elem.evaluate('el => el.outerHTML')}]
                    })
            
            return {
                "score": self._calculate_score(issues, passes, len(elements)),
                "issues": issues,
                "passes": passes,
                "details": {
                    "total_elements": len(elements),
                    "valid_elements": len(passes),
                    "invalid_elements": len(issues),
                    "score_breakdown": {
                        "base_score": 100,
                        "issue_penalty": len(issues) * 20,
                        "pass_bonus": len(passes) * 5
                    }
                }
            }
        except Exception as e:
            logger.error(f"ARIA attributes check failed: {str(e)}")
            raise
    
    @async_timed()
    async def _check_keyboard_navigation(self, page: Page) -> Dict[str, Any]:
        """Check keyboard navigation."""
        try:
            interactive_elements = await page.query_selector_all('a, button, input, select, textarea, [role="button"], [role="link"]')
            issues = []
            passes = []
            
            for elem in interactive_elements:
                tabindex = await elem.get_attribute('tabindex')
                if tabindex and int(tabindex) < 0:
                    issues.append({
                        'id': 'keyboard-navigation',
                        'impact': 'serious',
                        'description': 'Element is not keyboard focusable',
                        'help': 'Ensure element is keyboard focusable',
                        'nodes': [{'html': await elem.evaluate('el => el.outerHTML')}]
                    })
                else:
                    passes.append({
                        'id': 'keyboard-navigation',
                        'impact': 'none',
                        'description': 'Element is keyboard focusable',
                        'help': 'Keyboard navigation is supported',
                        'nodes': [{'html': await elem.evaluate('el => el.outerHTML')}]
                    })
            
            return {
                "score": self._calculate_score(issues, passes, len(interactive_elements)),
                "issues": issues,
                "passes": passes,
                "details": {
                    "total_elements": len(interactive_elements),
                    "focusable_elements": len(passes),
                    "unfocusable_elements": len(issues),
                    "score_breakdown": {
                        "base_score": 100,
                        "issue_penalty": len(issues) * 20,
                        "pass_bonus": len(passes) * 5
                    }
                }
            }
        except Exception as e:
            logger.error(f"Keyboard navigation check failed: {str(e)}")
            raise
    
    @async_timed()
    async def _check_color_contrast(self, page: Page) -> Dict[str, Any]:
        """Check color contrast using WCAG guidelines."""
        try:
            text_elements = await page.query_selector_all('p, span, div, h1, h2, h3, h4, h5, h6')
            issues = []
            passes = []
            
            for elem in text_elements:
                contrast_info = await elem.evaluate("""el => {
                    const style = window.getComputedStyle(el);
                    const bgColor = style.backgroundColor;
                    const textColor = style.color;
                    
                    // Convert colors to RGB
                    function parseColor(color) {
                        const div = document.createElement('div');
                        div.style.color = color;
                        document.body.appendChild(div);
                        const computed = window.getComputedStyle(div).color;
                        document.body.removeChild(div);
                        
                        const match = computed.match(/\\d+/g);
                        return match ? match.map(Number) : [0, 0, 0];
                    }
                    
                    // Calculate relative luminance
                    function getLuminance(rgb) {
                        const [r, g, b] = rgb.map(c => {
                            c = c / 255;
                            return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
                        });
                        return 0.2126 * r + 0.7152 * g + 0.0722 * b;
                    }
                    
                    // Calculate contrast ratio
                    function getContrastRatio(l1, l2) {
                        const lighter = Math.max(l1, l2);
                        const darker = Math.min(l1, l2);
                        return (lighter + 0.05) / (darker + 0.05);
                    }
                    
                    const bgRGB = parseColor(bgColor);
                    const textRGB = parseColor(textColor);
                    
                    const bgLuminance = getLuminance(bgRGB);
                    const textLuminance = getLuminance(textRGB);
                    
                    const contrastRatio = getContrastRatio(bgLuminance, textLuminance);
                    
                    return {
                        contrastRatio,
                        bgColor,
                        textColor
                    };
                }""")
                
                # WCAG 2.1 Level AA requires:
                # - 4.5:1 for normal text
                # - 3:1 for large text (18pt or 14pt bold)
                min_contrast = 4.5
                
                if contrast_info['contrastRatio'] < min_contrast:
                    issues.append({
                        'id': 'color-contrast',
                        'impact': 'serious',
                        'description': f'Insufficient color contrast ratio: {contrast_info["contrastRatio"]:.2f}:1',
                        'help': f'Ensure text has a contrast ratio of at least {min_contrast}:1',
                        'nodes': [{'html': await elem.evaluate('el => el.outerHTML')}]
                    })
                else:
                    passes.append({
                        'id': 'color-contrast',
                        'impact': 'none',
                        'description': f'Color contrast ratio: {contrast_info["contrastRatio"]:.2f}:1',
                        'help': 'Color contrast meets WCAG guidelines',
                        'nodes': [{'html': await elem.evaluate('el => el.outerHTML')}]
                    })
            
            return {
                "score": self._calculate_score(issues, passes, len(text_elements)),
                "issues": issues,
                "passes": passes,
                "details": {
                    "total_elements": len(text_elements),
                    "valid_contrast": len(passes),
                    "invalid_contrast": len(issues),
                    "score_breakdown": {
                        "base_score": 100,
                        "issue_penalty": len(issues) * 20,
                        "pass_bonus": len(passes) * 5
                    }
                }
            }
        except Exception as e:
            logger.error(f"Color contrast check failed: {str(e)}")
            raise 