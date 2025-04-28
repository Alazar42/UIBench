import aiohttp
import logging
from typing import Optional, Dict, Any, List
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import asyncio
from datetime import datetime

from ..utils.error_handler import ResourceError
from ..utils.cache import NetworkCache
from ..utils.performance_utils import async_timed, RateLimiter
from ..config import Settings

logger = logging.getLogger(__name__)
config = Settings()

class RequestManager:
    """Manages HTTP requests with caching and rate limiting."""
    
    def __init__(self):
        self.cache = NetworkCache()
        self.rate_limiter = RateLimiter(
            max_requests=config.network.max_concurrent_requests,
            time_window=1.0
        )
        self.session: Optional[aiohttp.ClientSession] = None
        self._lock = asyncio.Lock()
    
    async def get_session(self) -> aiohttp.ClientSession:
        """Get or create an aiohttp session."""
        if not self.session:
            async with self._lock:
                if not self.session:
                    self.session = aiohttp.ClientSession(
                        headers={"User-Agent": config.network.user_agent},
                        timeout=aiohttp.ClientTimeout(
                            total=config.network.request_timeout
                        )
                    )
        return self.session
    
    async def close(self):
        """Close the session."""
        if self.session:
            await self.session.close()
            self.session = None
    
    @async_timed()
    async def fetch(self, url: str, force_refresh: bool = False) -> Dict[str, Any]:
        """Fetch a URL with caching and rate limiting."""
        if not force_refresh:
            cached = self.cache.get_response(url)
            if cached:
                return cached
        
        async with self.rate_limiter:
            session = await self.get_session()
            try:
                for attempt in range(config.network.max_retries):
                    try:
                        async with session.get(url) as response:
                            response.raise_for_status()
                            content = await response.text()
                            headers = dict(response.headers)
                            
                            result = {
                                'content': content,
                                'headers': headers,
                                'status': response.status,
                                'url': str(response.url),
                                'timestamp': datetime.now().isoformat()
                            }
                            
                            self.cache.cache_response(url, content, headers)
                            return result
                            
                    except aiohttp.ClientError as e:
                        if attempt == config.network.max_retries - 1:
                            raise
                        await asyncio.sleep(
                            config.network.retry_delay * (config.network.retry_backoff ** attempt)
                        )
                        
            except aiohttp.ClientError as e:
                raise ResourceError(f"Failed to fetch {url}: {str(e)}")
            except asyncio.TimeoutError:
                raise ResourceError(f"Timeout while fetching {url}")

# Global request manager instance
request_manager = RequestManager()

@async_timed()
async def fetch_page_html(url: str, force_refresh: bool = False) -> str:
    """
    Fetch HTML content from a URL.
    
    Args:
        url: The URL to fetch
        force_refresh: Whether to bypass cache
        
    Returns:
        str: HTML content
        
    Raises:
        ResourceError: If fetching fails
    """
    try:
        response = await request_manager.fetch(url, force_refresh)
        return response['content']
    except Exception as e:
        raise ResourceError(f"Failed to fetch {url}: {str(e)}")

@async_timed()
def parse_html(html: str) -> BeautifulSoup:
    """
    Parse HTML content into a BeautifulSoup object.
    
    Args:
        html: HTML content to parse
        
    Returns:
        BeautifulSoup: Parsed HTML
        
    Raises:
        ResourceError: If parsing fails
    """
    try:
        return BeautifulSoup(html, "html.parser")
    except Exception as e:
        raise ResourceError(f"Failed to parse HTML: {str(e)}")

def is_valid_url(url: str) -> bool:
    """
    Check if a URL is valid.
    
    Args:
        url: URL to validate
        
    Returns:
        bool: True if URL is valid
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False

def normalize_url(url: str) -> str:
    """
    Normalize a URL by removing fragments and trailing slashes.
    
    Args:
        url: URL to normalize
        
    Returns:
        str: Normalized URL
    """
    parsed = urlparse(url)
    normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path.rstrip('/')}"
    if parsed.query:
        normalized += f"?{parsed.query}"
    return normalized

async def cleanup():
    """Clean up resources."""
    await request_manager.close() 