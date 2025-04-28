import asyncio
import sys
import os
from pathlib import Path
import pytest
from playwright.async_api import async_playwright

# Add the project root to the Python path
project_root = str(Path(__file__).parent.parent.parent)
sys.path.append(project_root)

from core.evaluators.website_evaluator import WebsiteEvaluator
from core.utils.error_handler import handle_evaluation_error
from ..analyzers.accessibility_analyzer import AccessibilityAnalyzer
from ..utils.browser_manager import BrowserManager

async def evaluate_website(url: str):
    """
    Evaluate a website using the core functionality.
    
    Args:
        url: The URL of the website to evaluate
    """
    try:
        print(f"\nEvaluating website: {url}")
        print("=" * 50)
        
        # Create evaluator instance
        evaluator = WebsiteEvaluator(
            root_url=url,
            max_subpages=5,  # Limit to 5 subpages for testing
            max_depth=2      # Limit depth to 2 for testing
        )
        
        # Run evaluation
        print("\nStarting evaluation...")
        results = await evaluator.evaluate(crawl=True)
        
        # Print results
        print("\nEvaluation Results:")
        print("-" * 30)
        
        # Print overall scores
        print("\nOverall Scores:")
        for category, score in results.get("aggregated_scores", {}).items():
            print(f"{category}: {score:.2f}")
        
        # Print critical issues
        print("\nCritical Issues:")
        for issue in results.get("defect_details", {}).get("critical", []):
            print(f"- {issue}")
        
        # Print recommendations
        print("\nRecommendations:")
        for rec in results.get("recommendations", []):
            print(f"- {rec}")
        
        return results
        
    except Exception as e:
        error_response = handle_evaluation_error(e)
        print("\nError during evaluation:")
        print(f"Message: {error_response['message']}")
        if error_response.get('details'):
            print("Details:", error_response['details'])
        return None

async def main():
    # Use Cursor website URL
    url = "https://www.cursor.com/"
    await evaluate_website(url)

async def test_accessibility_analysis():
    """Test the accessibility analyzer with real-time progress updates."""
    async with async_playwright() as playwright:
        # Initialize browser
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Test URL - using a simple test page
        test_url = "https://example.com"
        
        try:
            # Navigate to test page
            await page.goto(test_url)
            
            # Initialize analyzer
            analyzer = AccessibilityAnalyzer()
            
            # Run analysis with progress updates
            print("\nStarting accessibility analysis...")
            async for update in analyzer.analyze_with_progress(test_url, page):
                analyzer.print_progress(update)
            
            print("\nAnalysis completed successfully!")
            
        except Exception as e:
            print(f"\nError during analysis: {str(e)}")
            raise
        finally:
            await browser.close()

async def test_accessibility_analysis_with_browser_manager():
    """Test the accessibility analyzer using the browser manager."""
    browser_manager = await BrowserManager.get_instance()
    browser_pool = await browser_manager.get_pool()
    
    try:
        # Get a page from the pool
        page = await browser_pool.get_page()
        
        # Test URL
        test_url = "https://example.com"
        
        # Navigate to test page
        await page.goto(test_url)
        
        # Initialize analyzer
        analyzer = AccessibilityAnalyzer()
        
        # Run analysis with progress updates
        print("\nStarting accessibility analysis with browser manager...")
        async for update in analyzer.analyze_with_progress(test_url, page):
            analyzer.print_progress(update)
        
        print("\nAnalysis completed successfully!")
        
    except Exception as e:
        print(f"\nError during analysis: {str(e)}")
        raise
    finally:
        await browser_pool.release_page(page)
        await browser_manager.close_all()

async def run_all_tests():
    """Run all accessibility analyzer tests."""
    print("\n=== Running Accessibility Analyzer Tests ===\n")
    
    print("Test 1: Basic Accessibility Analysis")
    await test_accessibility_analysis()
    
    print("\nTest 2: Accessibility Analysis with Browser Manager")
    await test_accessibility_analysis_with_browser_manager()
    
    print("\n=== All Tests Completed Successfully ===\n")

if __name__ == "__main__":
    # Run all tests
    asyncio.run(run_all_tests()) 