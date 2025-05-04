"""
Browser management module for UIBench.
"""
from typing import Dict, Any, Optional, List
import asyncio
from playwright.async_api import async_playwright, Browser, Page

class BrowserPool:
    """Manages a pool of browser pages."""
    
    def __init__(self, browser: Browser, max_pages: int = 5):
        self._browser = browser
        self._max_pages = max_pages
        self._available_pages: List[Page] = []
        self._in_use_pages: List[Page] = []
        self._lock = asyncio.Lock()
        
    async def get_page(self) -> Page:
        """Get a page from the pool."""
        async with self._lock:
            if not self._available_pages:
                if len(self._in_use_pages) < self._max_pages:
                    page = await self._browser.new_page()
                else:
                    # Wait for a page to become available
                    while not self._available_pages:
                        await asyncio.sleep(0.1)
                    page = self._available_pages.pop()
            else:
                page = self._available_pages.pop()
            
            self._in_use_pages.append(page)
            return page
            
    async def release_page(self, page: Page):
        """Release a page back to the pool."""
        async with self._lock:
            if page in self._in_use_pages:
                self._in_use_pages.remove(page)
                self._available_pages.append(page)

class BrowserManager:
    """Manages browser instances for website evaluation."""
    
    _instance = None
    _lock = asyncio.Lock()
    
    def __init__(self):
        self._browser: Optional[Browser] = None
        self._context = None
        self._page: Optional[Page] = None
        self._pool: Optional[BrowserPool] = None
        
    @classmethod
    async def get_instance(cls) -> 'BrowserManager':
        """Get the singleton instance of BrowserManager."""
        if not cls._instance:
            async with cls._lock:
                if not cls._instance:
                    cls._instance = cls()
                    await cls._instance.initialize()
        return cls._instance
        
    async def initialize(self, browser_type: str = 'chromium', headless: bool = True) -> None:
        """Initialize the browser instance."""
        playwright = await async_playwright().start()
        browser_class = getattr(playwright, browser_type)
        self._browser = await browser_class.launch(headless=headless)
        self._context = await self._browser.new_context()
        self._page = await self._context.new_page()
        self._pool = BrowserPool(self._browser)
        
    async def get_pool(self) -> BrowserPool:
        """Get the browser pool."""
        if not self._pool:
            raise RuntimeError("Browser not initialized. Call initialize() first.")
        return self._pool
        
    async def navigate(self, url: str) -> None:
        """Navigate to a URL."""
        if not self._page:
            raise RuntimeError("Browser not initialized. Call initialize() first.")
        await self._page.goto(url)
        
    async def get_page_content(self) -> str:
        """Get the current page content."""
        if not self._page:
            raise RuntimeError("Browser not initialized. Call initialize() first.")
        return await self._page.content()
        
    async def evaluate_javascript(self, script: str) -> Any:
        """Evaluate JavaScript code on the page."""
        if not self._page:
            raise RuntimeError("Browser not initialized. Call initialize() first.")
        return await self._page.evaluate(script)
        
    async def get_page_metrics(self) -> Dict[str, Any]:
        """Get page performance metrics."""
        if not self._page:
            raise RuntimeError("Browser not initialized. Call initialize() first.")
        metrics = await self._page.metrics()
        timing = await self._page.evaluate('() => JSON.stringify(window.performance.timing)')
        return {
            'metrics': metrics,
            'timing': timing
        }
        
    async def close(self) -> None:
        """Close the browser instance."""
        if self._page:
            await self._page.close()
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
            
    async def close_all(self) -> None:
        """Close all browser instances and clean up."""
        await self.close()
        BrowserManager._instance = None
            
    async def screenshot(self, path: str) -> None:
        """Take a screenshot of the current page."""
        if not self._page:
            raise RuntimeError("Browser not initialized. Call initialize() first.")
        await self._page.screenshot(path=path)
        
    async def get_accessibility_tree(self) -> Dict[str, Any]:
        """Get the accessibility tree of the current page."""
        if not self._page:
            raise RuntimeError("Browser not initialized. Call initialize() first.")
        return await self._page.accessibility.snapshot()
        
    @property
    def page(self) -> Optional[Page]:
        """Get the current page instance."""
        return self._page 