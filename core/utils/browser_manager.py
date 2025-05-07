"""
Browser pool management for efficient browser instance handling.
"""
import asyncio
from typing import Dict, Optional, List, Any
import logging
from playwright.async_api import async_playwright, Browser, Page
from .async_utils import AsyncPool

logger = logging.getLogger(__name__)

class BrowserPool:
    """Manages a pool of browser instances for parallel processing."""
    
    def __init__(self, max_browsers: int = 5, max_pages_per_browser: int = 5):
        self.max_browsers = max_browsers
        self.max_pages_per_browser = max_pages_per_browser
        self.browsers: List[Browser] = []
        self.pages: Dict[Browser, List[Page]] = {}
        self.page_pool = AsyncPool(max_concurrency=max_browsers * max_pages_per_browser)
        self._lock = asyncio.Lock()
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the browser pool."""
        if self._initialized:
            return
            
        async with self._lock:
            if self._initialized:
                return
                
            try:
                self.playwright = await async_playwright().start()
                self._initialized = True
            except Exception as e:
                logger.error(f"Failed to initialize playwright: {str(e)}")
                raise
    
    async def get_browser(self) -> Browser:
        """Get an available browser instance or create a new one."""
        await self.initialize()
        
        async with self._lock:
            # Find browser with fewest pages
            available_browser = None
            min_pages = self.max_pages_per_browser
            
            for browser in self.browsers:
                page_count = len(self.pages[browser])
                if page_count < min_pages:
                    available_browser = browser
                    min_pages = page_count
            
            # Create new browser if needed and possible
            if available_browser is None and len(self.browsers) < self.max_browsers:
                try:
                    browser = await self.playwright.chromium.launch(
                        headless=True,
                        args=['--no-sandbox', '--disable-dev-shm-usage']
                    )
                    self.browsers.append(browser)
                    self.pages[browser] = []
                    available_browser = browser
                except Exception as e:
                    logger.error(f"Failed to launch browser: {str(e)}")
                    raise
            
            return available_browser
    
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
    
    async def release_page(self, page: Page) -> None:
        """Release a page back to the pool."""
        async with self._lock:
            for browser, pages in self.pages.items():
                if page in pages:
                    pages.remove(page)
                    try:
                        await page.close()
                    except Exception as e:
                        logger.error(f"Failed to close page: {str(e)}")
                    
                    # Close browser if no pages left and we have excess capacity
                    if not pages and len(self.browsers) > 1:
                        try:
                            await browser.close()
                            self.browsers.remove(browser)
                            del self.pages[browser]
                        except Exception as e:
                            logger.error(f"Failed to close browser: {str(e)}")
                    break
    
    async def execute_in_page(self, task, *args, **kwargs) -> Any:
        """Execute a task in an available page from the pool."""
        page = await self.get_page()
        if not page:
            raise RuntimeError("No available pages in the pool")
            
        try:
            return await task(page, *args, **kwargs)
        finally:
            await self.release_page(page)
    
    async def close(self) -> None:
        """Close all browsers and clean up resources."""
        async with self._lock:
            for browser in self.browsers:
                try:
                    await browser.close()
                except Exception as e:
                    logger.error(f"Failed to close browser: {str(e)}")
            
            self.browsers.clear()
            self.pages.clear()
            
            if self._initialized:
                try:
                    await self.playwright.stop()
                except Exception as e:
                    logger.error(f"Failed to stop playwright: {str(e)}")
                self._initialized = False

class BrowserManager:
    """Singleton manager for browser pools."""
    
    _instance = None
    _lock = asyncio.Lock()
    
    def __init__(self):
        self.pools: Dict[str, BrowserPool] = {}
    
    @classmethod
    async def get_instance(cls) -> 'BrowserManager':
        """Get or create the singleton instance."""
        if not cls._instance:
            async with cls._lock:
                if not cls._instance:
                    cls._instance = BrowserManager()
        return cls._instance
    
    async def get_pool(self, name: str = "default", 
                      max_browsers: int = 5,
                      max_pages_per_browser: int = 5) -> BrowserPool:
        """Get or create a browser pool."""
        if name not in self.pools:
            async with self._lock:
                if name not in self.pools:
                    pool = BrowserPool(max_browsers, max_pages_per_browser)
                    await pool.initialize()
                    self.pools[name] = pool
        return self.pools[name]
    
    async def close_all(self) -> None:
        """Close all browser pools."""
        async with self._lock:
            for pool in self.pools.values():
                await pool.close()
            self.pools.clear() 