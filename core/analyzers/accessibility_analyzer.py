from typing import Dict, List, Optional, Any, Callable, AsyncGenerator
from playwright.async_api import Page
from bs4 import BeautifulSoup
import asyncio
import logging
from datetime import datetime
import time
import json
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box
import re
import os

from ..utils.error_handler import AnalysisError
from ..utils.performance_utils import async_timed, PerformanceMonitor
from ..utils.cache import AnalysisCache
from ..config import Settings
from .accessibility_screenreader import ScreenReaderSimulator
from .base_analyzer import BaseAnalyzer

logger = logging.getLogger(__name__)
config = Settings()
console = Console()

class AccessibilityAnalyzer(BaseAnalyzer):
    """Analyzes web pages for accessibility compliance and best practices."""
    
    def __init__(self):
        super().__init__()
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
                ("color_contrast", self._check_color_contrast),
                ("screen_reader", ScreenReaderSimulator.simulate_screen_reader),
                ("focus_order", ScreenReaderSimulator.check_focus_order)
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
    async def analyze(self, url: str, html: str, soup: BeautifulSoup) -> str:
        """Analyze accessibility of a webpage."""
        try:
            # Perform various accessibility checks
            heading_results = self._analyze_headings(soup)
            image_results = self._analyze_images(soup)
            link_results = self._analyze_links(soup)
            color_results = self._analyze_color_contrast(soup)
            form_results = self._analyze_forms(soup)
            landmark_results = self._analyze_landmarks(soup)
            keyboard_results = self._analyze_keyboard_navigation(soup)
            aria_results = self._analyze_aria_attributes(soup)
            
            # Calculate overall score as average of individual scores
            scores = [
                heading_results["score"],
                image_results["score"],
                link_results["score"],
                color_results["score"],
                form_results["score"],
                landmark_results["score"],
                keyboard_results["score"],
                aria_results["score"]
            ]
            overall_score = sum(scores) / len(scores)
            
            # Combine all issues and passes
            all_issues = (
                heading_results["issues"] +
                image_results["issues"] +
                link_results["issues"] +
                color_results["issues"] +
                form_results["issues"] +
                landmark_results["issues"] +
                keyboard_results["issues"] +
                aria_results["issues"]
            )
            
            all_passes = (
                heading_results["passes"] +
                image_results["passes"] +
                link_results["passes"] +
                color_results["passes"] +
                form_results["passes"] +
                landmark_results["passes"] +
                keyboard_results["passes"] +
                aria_results["passes"]
            )
            
            # Generate recommendations based on issues
            recommendations = self._generate_recommendations(all_issues)
            
            # Prepare detailed metrics
            metrics = {
                "headings_score": heading_results["score"],
                "images_score": image_results["score"],
                "links_score": link_results["score"],
                "color_contrast_score": color_results["score"],
                "forms_score": form_results["score"],
                "landmarks_score": landmark_results["score"],
                "keyboard_nav_score": keyboard_results["score"],
                "aria_score": aria_results["score"]
            }
            
            # Prepare detailed results for each category
            details = {
                "headings": heading_results,
                "images": image_results,
                "links": link_results,
                "color_contrast": color_results,
                "forms": form_results,
                "landmarks": landmark_results,
                "keyboard_navigation": keyboard_results,
                "aria": aria_results
            }
            
            results = {
                "overall_score": overall_score,
                "score": overall_score,  # Keep for backward compatibility
                "issues": all_issues,
                "passes": all_passes,
                "recommendations": recommendations,
                "metrics": metrics,
                "details": details
            }
            
            # Save results to a JSON file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_url = re.sub(r'[^\w]', '_', url)
            filename = f"accessibility_{safe_url}_{timestamp}.json"
            json_path = os.path.join("analysis_results", filename)
            
            os.makedirs("analysis_results", exist_ok=True)
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump({"results": results}, f, indent=2)
            
            return json.dumps({
                "results": results,
                "json_path": json_path
            }, indent=2)
            
        except Exception as e:
            logging.error(f"Error in accessibility analysis: {str(e)}")
            raise

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

    def _analyze_semantic_structure(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Analyze semantic structure of the page."""
        issues = []
        passes = []
        
        # Check for proper heading hierarchy
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        if not headings:
            issues.append("No headings found on the page")
        else:
            # Check if h1 exists
            h1_tags = soup.find_all('h1')
            if not h1_tags:
                issues.append("No h1 heading found")
            elif len(h1_tags) > 1:
                issues.append("Multiple h1 headings found")
            else:
                passes.append("Proper h1 heading usage")
            
            # Check heading hierarchy
            current_level = 1
            for heading in headings:
                level = int(heading.name[1])
                if level - current_level > 1:
                    issues.append(f"Skipped heading level from h{current_level} to h{level}")
                current_level = level
        
        # Check for semantic elements
        semantic_elements = ['nav', 'main', 'header', 'footer', 'article', 'section', 'aside']
        found_elements = set()
        for element in semantic_elements:
            if soup.find(element):
                found_elements.add(element)
                passes.append(f"Found semantic {element} element")
        
        missing_elements = set(semantic_elements) - found_elements
        if missing_elements:
            issues.append(f"Missing semantic elements: {', '.join(missing_elements)}")
        
        # Check for proper list structure
        lists = soup.find_all(['ul', 'ol'])
        for list_elem in lists:
            if not list_elem.find_all('li'):
                issues.append(f"Empty {list_elem.name} list found")
            else:
                passes.append(f"Proper {list_elem.name} list structure")
        
        # Check for proper table structure
        tables = soup.find_all('table')
        for table in tables:
            if not table.find('th'):
                issues.append("Table missing header cells (th)")
            if not table.find('caption'):
                issues.append("Table missing caption")
            if table.find('th') and table.find('caption'):
                passes.append("Table has proper structure")
        
        # Calculate score based on issues and passes
        total_checks = len(issues) + len(passes)
        score = (len(passes) / total_checks * 100) if total_checks > 0 else 0
        
        return {
            "score": score,
            "issues": issues,
            "passes": passes
        }

    def _analyze_color_contrast(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Analyze color contrast of text elements."""
        issues = []
        passes = []
        
        # Get all text elements with color properties
        elements = soup.find_all(lambda tag: tag.get('style') and ('color' in tag['style'] or 'background' in tag['style']))
        
        for element in elements:
            style = element.get('style', '')
            
            # Extract color values (simplified for demonstration)
            text_color = None
            bg_color = None
            
            # Check for color declarations
            if 'color:' in style:
                text_color = style.split('color:')[1].split(';')[0].strip()
            if 'background-color:' in style:
                bg_color = style.split('background-color:')[1].split(';')[0].strip()
            
            if text_color and bg_color:
                # For demonstration, we'll just check if colors are specified
                passes.append(f"Found text element with color contrast specification")
            else:
                issues.append("Text element missing color contrast specification")
        
        # Check for CSS variables
        style_tags = soup.find_all('style')
        for style_tag in style_tags:
            if '--color' in style_tag.text or '--bg' in style_tag.text:
                passes.append("Found CSS color variables")
        
        # Calculate score based on issues and passes
        total_checks = len(issues) + len(passes)
        score = (len(passes) / total_checks * 100) if total_checks > 0 else 0
        
        return {
            "score": score,
            "issues": issues,
            "passes": passes
        }

    def _analyze_keyboard_navigation(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Analyze keyboard navigation accessibility."""
        issues = []
        passes = []
        
        # Check for skip links
        skip_links = soup.find_all('a', {'href': '#main'}) or soup.find_all('a', text=lambda t: t and 'skip' in t.lower())
        if not skip_links:
            issues.append("Missing skip navigation link")
        else:
            passes.append("Page has skip navigation link")
        
        # Check tabindex
        elements_with_tabindex = soup.find_all(lambda tag: tag.get('tabindex'))
        for element in elements_with_tabindex:
            tabindex = element.get('tabindex')
            try:
                tabindex_int = int(tabindex)
                if tabindex_int > 0:
                    issues.append(f"Positive tabindex found: {tabindex} on {element.name}")
                elif tabindex_int == 0:
                    passes.append(f"Proper tabindex='0' found on {element.name}")
                else:
                    passes.append(f"Element removed from tab order: {element.name}")
            except ValueError:
                issues.append(f"Invalid tabindex value: {tabindex}")
        
        # Check for keyboard traps
        interactive_elements = soup.find_all(['button', 'a', 'input', 'select', 'textarea'])
        for element in interactive_elements:
            # Check for click handlers without keyboard handlers
            if element.get('onclick') and not (element.get('onkeypress') or element.get('onkeydown')):
                issues.append(f"Element with click handler missing keyboard handler: {element.name}")
            
            # Check for disabled elements
            if element.get('disabled') is not None:
                if not element.get('aria-disabled'):
                    issues.append(f"Disabled element missing aria-disabled: {element.name}")
                else:
                    passes.append(f"Disabled element has aria-disabled: {element.name}")
        
        # Check for focus indicators
        elements_with_outline_none = soup.find_all(style=lambda s: s and 'outline: none' in s)
        if elements_with_outline_none:
            issues.append("Elements found with outline: none style")
        
        # Calculate score
        total_checks = len(issues) + len(passes)
        score = (len(passes) / total_checks * 100) if total_checks > 0 else 0
        
        return {
            "score": score,
            "issues": issues,
            "passes": passes
        }

    def _analyze_screen_reader(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Analyze screen reader accessibility."""
        issues = []
        passes = []
        
        # Check for ARIA landmarks
        landmarks = {
            'banner': 'header',
            'navigation': 'nav',
            'main': 'main',
            'complementary': 'aside',
            'contentinfo': 'footer'
        }
        
        for role, element in landmarks.items():
            elements = soup.find_all(element) + soup.find_all(attrs={'role': role})
            if elements:
                passes.append(f"Found {role} landmark")
            else:
                issues.append(f"Missing {role} landmark")
        
        # Check for ARIA labels and descriptions
        interactive_elements = soup.find_all(['button', 'a', 'input', 'select', 'textarea'])
        for element in interactive_elements:
            # Check for accessible name
            if (element.get('aria-label') or 
                element.get('aria-labelledby') or 
                element.get('title') or 
                element.string or 
                element.get('alt')):
                passes.append(f"Found accessible name for {element.name}")
            else:
                issues.append(f"Missing accessible name for {element.name}")
            
            # Check for ARIA descriptions
            if element.get('aria-describedby'):
                passes.append(f"Found ARIA description for {element.name}")
        
        # Check for proper heading structure
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        if headings:
            # Check for proper nesting
            current_level = 0
            for heading in headings:
                level = int(heading.name[1])
                if level - current_level > 1:
                    issues.append(f"Improper heading structure: h{current_level} to h{level}")
                current_level = level
            passes.append("Found heading structure")
        else:
            issues.append("No headings found")
        
        # Check for form labels
        forms = soup.find_all('form')
        for form in forms:
            inputs = form.find_all(['input', 'select', 'textarea'])
            for input_elem in inputs:
                input_id = input_elem.get('id')
                if input_id:
                    label = soup.find('label', {'for': input_id})
                    if label:
                        passes.append(f"Found label for {input_elem.name}")
                    else:
                        issues.append(f"Missing label for {input_elem.name}")
        
        # Check for image alt text
        images = soup.find_all('img')
        for image in images:
            if image.get('alt') is not None:
                if image.get('alt') == '':
                    passes.append("Found decorative image with empty alt")
                else:
                    passes.append("Found image with alt text")
            else:
                issues.append("Image missing alt attribute")
        
        # Check for table accessibility
        tables = soup.find_all('table')
        for table in tables:
            if table.find('caption'):
                passes.append("Table has caption")
            else:
                issues.append("Table missing caption")
            
            if table.find('th'):
                passes.append("Table has header cells")
            else:
                issues.append("Table missing header cells")
        
        # Calculate score based on issues and passes
        total_checks = len(issues) + len(passes)
        score = (len(passes) / total_checks * 100) if total_checks > 0 else 0
        
        return {
            "score": score,
            "issues": issues,
            "passes": passes
        }

    def _analyze_forms(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Analyze form accessibility."""
        issues = []
        passes = []
        
        # Find all forms
        forms = soup.find_all('form')
        
        if not forms:
            issues.append("No forms found on the page")
            return {
                "score": 0,
                "issues": issues,
                "passes": passes
            }
        
        for form in forms:
            # Check for form labels
            inputs = form.find_all(['input', 'select', 'textarea'])
            for input_elem in inputs:
                input_type = input_elem.get('type', '')
                input_id = input_elem.get('id')
                
                # Skip hidden and submit inputs
                if input_type in ['hidden', 'submit', 'button']:
                    continue
                
                # Check for label
                if input_id:
                    label = soup.find('label', {'for': input_id})
                    if label:
                        passes.append(f"Found label for {input_elem.name}")
                    else:
                        issues.append(f"Missing label for {input_elem.name}")
                else:
                    issues.append(f"Input missing ID attribute: {input_elem.name}")
                
                # Check for placeholder
                if input_elem.get('placeholder'):
                    passes.append(f"Found placeholder for {input_elem.name}")
                
                # Check for required field indication
                if input_elem.get('required'):
                    if input_elem.get('aria-required') == 'true':
                        passes.append(f"Required field properly indicated for {input_elem.name}")
                    else:
                        issues.append(f"Missing aria-required for required field: {input_elem.name}")
                
                # Check for error handling
                if input_elem.get('aria-invalid'):
                    passes.append(f"Error state handling found for {input_elem.name}")
                
                # Check for input validation
                if input_elem.get('pattern') or input_elem.get('minlength') or input_elem.get('maxlength'):
                    passes.append(f"Input validation found for {input_elem.name}")
            
            # Check for fieldsets and legends
            fieldsets = form.find_all('fieldset')
            for fieldset in fieldsets:
                if fieldset.find('legend'):
                    passes.append("Found fieldset with legend")
                else:
                    issues.append("Fieldset missing legend")
            
            # Check for form submission feedback
            submit_button = form.find('button', {'type': 'submit'}) or form.find('input', {'type': 'submit'})
            if submit_button:
                if submit_button.get('aria-label') or submit_button.string:
                    passes.append("Submit button has accessible name")
                else:
                    issues.append("Submit button missing accessible name")
            else:
                issues.append("Form missing submit button")
            
            # Check for form validation
            if form.get('novalidate'):
                issues.append("Form validation disabled with novalidate")
            
            # Check for ARIA roles and properties
            if form.get('role'):
                passes.append("Form has ARIA role")
            if form.get('aria-label') or form.get('aria-labelledby'):
                passes.append("Form has ARIA label")
        
        # Calculate score based on issues and passes
        total_checks = len(issues) + len(passes)
        score = (len(passes) / total_checks * 100) if total_checks > 0 else 0
        
        return {
            "score": score,
            "issues": issues,
            "passes": passes
        }

    def _analyze_headings(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Analyze heading structure."""
        issues = []
        passes = []
        
        # Find all headings
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        
        if not headings:
            issues.append("No headings found on the page")
            return {
                "score": 0,
                "issues": issues,
                "passes": passes
            }
        
        # Check for h1
        h1_tags = soup.find_all('h1')
        if not h1_tags:
            issues.append("Missing main heading (h1)")
        elif len(h1_tags) > 1:
            issues.append("Multiple h1 headings found")
        else:
            passes.append("Page has exactly one main heading (h1)")
        
        # Check heading hierarchy
        prev_level = 0
        for heading in headings:
            current_level = int(heading.name[1])
            
            # Check for skipped levels
            if current_level - prev_level > 1 and prev_level != 0:
                issues.append(f"Heading level skipped from h{prev_level} to h{current_level}")
            else:
                passes.append(f"Proper heading level sequence: h{prev_level} to h{current_level}")
            
            # Check for empty headings
            if not heading.get_text(strip=True):
                issues.append(f"Empty heading found: {heading.name}")
            
            prev_level = current_level
        
        # Calculate score
        total_checks = len(issues) + len(passes)
        score = (len(passes) / total_checks * 100) if total_checks > 0 else 0
        
        return {
            "score": score,
            "issues": issues,
            "passes": passes
        }

    def _analyze_images(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Analyze image accessibility."""
        issues = []
        passes = []
        
        # Find all images
        images = soup.find_all('img')
        
        if not images:
            return {
                "score": 100,  # No images means no accessibility issues
                "issues": [],
                "passes": ["No images found on the page"]
            }
        
        for img in images:
            # Check for alt text
            alt_text = img.get('alt')
            if alt_text is None:
                issues.append(f"Image missing alt attribute: {img.get('src', 'unknown source')}")
            elif alt_text == "":
                if not img.get('role') == 'presentation':
                    issues.append(f"Decorative image should have role='presentation': {img.get('src', 'unknown source')}")
                else:
                    passes.append(f"Decorative image properly marked: {img.get('src', 'unknown source')}")
            else:
                passes.append(f"Image has alt text: {img.get('src', 'unknown source')}")
            
            # Check for title attribute
            if img.get('title'):
                passes.append(f"Image has title attribute: {img.get('src', 'unknown source')}")
            
            # Check for width and height
            if img.get('width') and img.get('height'):
                passes.append(f"Image has dimensions specified: {img.get('src', 'unknown source')}")
            else:
                issues.append(f"Image missing dimensions: {img.get('src', 'unknown source')}")
        
        # Calculate score
        total_checks = len(issues) + len(passes)
        score = (len(passes) / total_checks * 100) if total_checks > 0 else 0
        
        return {
            "score": score,
            "issues": issues,
            "passes": passes
        }

    def _analyze_links(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Analyze link accessibility."""
        issues = []
        passes = []
        
        # Find all links
        links = soup.find_all('a')
        
        if not links:
            return {
                "score": 100,
                "issues": [],
                "passes": ["No links found on the page"]
            }
        
        for link in links:
            # Check for href
            href = link.get('href')
            if not href:
                issues.append("Link missing href attribute")
                continue
            
            # Check for text content
            text = link.get_text(strip=True)
            if not text:
                # Check for aria-label or title
                aria_label = link.get('aria-label')
                title = link.get('title')
                if not (aria_label or title):
                    issues.append(f"Link has no text content or aria-label: {href}")
                else:
                    passes.append(f"Link has aria-label or title: {href}")
            else:
                # Check for generic text
                generic_texts = ['click here', 'read more', 'learn more', 'more', 'link']
                if text.lower() in generic_texts:
                    issues.append(f"Link uses generic text: {text}")
                else:
                    passes.append(f"Link has descriptive text: {text}")
            
            # Check for title attribute
            if link.get('title'):
                passes.append(f"Link has title attribute: {href}")
            
            # Check for target="_blank"
            if link.get('target') == '_blank':
                if not link.get('rel') or 'noopener' not in link.get('rel'):
                    issues.append(f"Link with target='_blank' missing rel='noopener': {href}")
                else:
                    passes.append(f"Link with target='_blank' has rel='noopener': {href}")
        
        # Calculate score
        total_checks = len(issues) + len(passes)
        score = (len(passes) / total_checks * 100) if total_checks > 0 else 0
        
        return {
            "score": score,
            "issues": issues,
            "passes": passes
        }

    def _analyze_landmarks(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Analyze landmark regions."""
        issues = []
        passes = []
        
        # Check for main landmark
        main = soup.find(['main', 'div[role="main"]'])
        if not main:
            issues.append("Missing main landmark")
        else:
            passes.append("Page has main landmark")
        
        # Check for navigation
        nav = soup.find(['nav', 'div[role="navigation"]'])
        if not nav:
            issues.append("Missing navigation landmark")
        else:
            passes.append("Page has navigation landmark")
        
        # Check for header
        header = soup.find(['header', 'div[role="banner"]'])
        if not header:
            issues.append("Missing header landmark")
        else:
            passes.append("Page has header landmark")
        
        # Check for footer
        footer = soup.find(['footer', 'div[role="contentinfo"]'])
        if not footer:
            issues.append("Missing footer landmark")
        else:
            passes.append("Page has footer landmark")
        
        # Check for complementary content
        aside = soup.find(['aside', 'div[role="complementary"]'])
        if aside:
            passes.append("Page has complementary content landmark")
        
        # Check for search
        search = soup.find('form[role="search"]')
        if search:
            passes.append("Page has search landmark")
        
        # Calculate score
        total_checks = 4  # Required landmarks: main, nav, header, footer
        found_landmarks = len([p for p in passes if any(x in p for x in ['main', 'navigation', 'header', 'footer'])])
        score = (found_landmarks / total_checks * 100)
        
        return {
            "score": score,
            "issues": issues,
            "passes": passes
        }

    def _analyze_aria_attributes(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Analyze ARIA attributes."""
        issues = []
        passes = []
        
        # Check for proper ARIA roles
        elements_with_roles = soup.find_all(lambda tag: tag.get('role'))
        valid_roles = [
            'alert', 'alertdialog', 'application', 'article', 'banner', 'button', 'cell',
            'checkbox', 'columnheader', 'combobox', 'complementary', 'contentinfo',
            'definition', 'dialog', 'directory', 'document', 'feed', 'figure', 'form',
            'grid', 'gridcell', 'group', 'heading', 'img', 'link', 'list', 'listbox',
            'listitem', 'log', 'main', 'marquee', 'math', 'menu', 'menubar', 'menuitem',
            'menuitemcheckbox', 'menuitemradio', 'navigation', 'none', 'note', 'option',
            'presentation', 'progressbar', 'radio', 'radiogroup', 'region', 'row',
            'rowgroup', 'rowheader', 'scrollbar', 'search', 'searchbox', 'separator',
            'slider', 'spinbutton', 'status', 'switch', 'tab', 'table', 'tablist',
            'tabpanel', 'term', 'textbox', 'timer', 'toolbar', 'tooltip', 'tree',
            'treegrid', 'treeitem'
        ]
        
        for element in elements_with_roles:
            role = element.get('role')
            if role in valid_roles:
                passes.append(f"Valid ARIA role '{role}' found on {element.name}")
            else:
                issues.append(f"Invalid ARIA role '{role}' found on {element.name}")
        
        # Check for required ARIA attributes
        elements_with_aria = soup.find_all(lambda tag: any(attr for attr in tag.attrs if attr.startswith('aria-')))
        for element in elements_with_aria:
            # Check aria-label and aria-labelledby
            if element.get('aria-labelledby'):
                referenced_id = element.get('aria-labelledby')
                if soup.find(id=referenced_id):
                    passes.append(f"aria-labelledby references valid ID: {referenced_id}")
                else:
                    issues.append(f"aria-labelledby references non-existent ID: {referenced_id}")
            
            # Check aria-describedby
            if element.get('aria-describedby'):
                referenced_id = element.get('aria-describedby')
                if soup.find(id=referenced_id):
                    passes.append(f"aria-describedby references valid ID: {referenced_id}")
                else:
                    issues.append(f"aria-describedby references non-existent ID: {referenced_id}")
            
            # Check for proper use of aria-hidden
            if element.get('aria-hidden') == 'true':
                if element.find_all(['a', 'button', 'input', 'select', 'textarea']):
                    issues.append("Interactive elements found inside aria-hidden='true'")
                else:
                    passes.append("Proper use of aria-hidden='true'")
        
        # Check for proper use of aria-expanded
        expandable_elements = soup.find_all(lambda tag: tag.get('aria-expanded'))
        for element in expandable_elements:
            if element.get('aria-expanded') in ['true', 'false']:
                passes.append(f"Proper use of aria-expanded on {element.name}")
            else:
                issues.append(f"Invalid aria-expanded value on {element.name}")
        
        # Calculate score
        total_checks = len(issues) + len(passes)
        score = (len(passes) / total_checks * 100) if total_checks > 0 else 0
        
        return {
            "score": score,
            "issues": issues,
            "passes": passes
        }

    def _generate_recommendations(self, issues: List[str]) -> List[str]:
        """Generate recommendations based on issues."""
        recommendations = []
        
        # Map common issues to recommendations
        issue_recommendations = {
            "missing alt": "Add descriptive alt text to all images",
            "empty heading": "Ensure all headings have content",
            "heading level skipped": "Maintain proper heading hierarchy",
            "missing label": "Add labels to all form controls",
            "missing main": "Add a main landmark to the page",
            "missing navigation": "Add a navigation landmark",
            "missing skip": "Add a skip navigation link",
            "positive tabindex": "Avoid using positive tabindex values",
            "outline: none": "Maintain visible focus indicators",
            "aria-hidden": "Ensure no interactive elements inside aria-hidden regions",
            "invalid aria": "Use only valid ARIA attributes and values"
        }
        
        # Generate recommendations based on issues
        for issue in issues:
            for key, recommendation in issue_recommendations.items():
                if key.lower() in issue.lower() and recommendation not in recommendations:
                    recommendations.append(recommendation)
        
        return recommendations