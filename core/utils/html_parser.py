import aiohttp
import logging
from typing import Optional
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from ..utils.error_handler import ResourceError

logger = logging.getLogger(__name__)

async def fetch_page_html(url: str, timeout: int = 30) -> str:
    """
    Fetch HTML content from a URL.
    
    Args:
        url: The URL to fetch
        timeout: Request timeout in seconds
        
    Returns:
        str: HTML content
        
    Raises:
        ResourceError: If fetching fails
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=timeout) as response:
                response.raise_for_status()
                return await response.text()
    except aiohttp.ClientError as e:
        raise ResourceError(f"Failed to fetch {url}: {str(e)}")
    except asyncio.TimeoutError:
        raise ResourceError(f"Timeout while fetching {url}")

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
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path.rstrip('/')}" 