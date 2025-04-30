import asyncio
from playwright.async_api import async_playwright
from core.analyzers.accessibility_analyzer import AccessibilityAnalyzer
from core.utils.browser_manager import BrowserManager

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

if __name__ == "__main__":
    # Run tests
    asyncio.run(test_accessibility_analysis())
    asyncio.run(test_accessibility_analysis_with_browser_manager()) 