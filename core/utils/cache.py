"""
Caching implementation for network requests and analysis results.
"""
import time
from typing import Any, Optional, Dict, TypeVar, Generic
import json
import os
from pathlib import Path
import logging
from datetime import datetime, timedelta
import aiofiles
import asyncio

logger = logging.getLogger(__name__)

K = TypeVar('K')
V = TypeVar('V')

class Cache(Generic[K, V]):
    """Generic cache implementation with TTL support."""
    
    def __init__(self, ttl: int = 3600):
        self._cache: Dict[K, tuple[V, float]] = {}
        self.ttl = ttl
    
    def get(self, key: K) -> Optional[V]:
        """Get value from cache if it exists and hasn't expired."""
        if key in self._cache:
            value, timestamp = self._cache[key]
            if time.time() - timestamp <= self.ttl:
                return value
            else:
                del self._cache[key]
        return None
    
    def set(self, key: K, value: V) -> None:
        """Set value in cache with current timestamp."""
        self._cache[key] = (value, time.time())
    
    def clear(self) -> None:
        """Clear all cached items."""
        self._cache.clear()

class DiskCache:
    """Persistent disk-based cache implementation."""
    
    def __init__(self, cache_dir: str = ".cache", ttl: int = 86400):
        self.cache_dir = Path(cache_dir)
        self.ttl = ttl
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._lock = asyncio.Lock()
    
    def _get_cache_path(self, key: str) -> Path:
        """Get the file path for a cache key."""
        # Use hash of key to avoid filesystem issues with long URLs
        return self.cache_dir / f"{hash(key)}.json"
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from disk cache if it exists and hasn't expired."""
        cache_path = self._get_cache_path(key)
        
        if cache_path.exists():
            try:
                async with self._lock:
                    async with aiofiles.open(cache_path, 'r') as f:
                        content = await f.read()
                        data = json.loads(content)
                        timestamp = datetime.fromisoformat(data['timestamp'])
                        
                        if datetime.now() - timestamp <= timedelta(seconds=self.ttl):
                            return data['value']
                        else:
                            await self._remove_file(cache_path)
            except (json.JSONDecodeError, KeyError, OSError) as e:
                logger.error(f"Cache read error for {key}: {str(e)}")
                if cache_path.exists():
                    await self._remove_file(cache_path)
        return None
    
    async def set(self, key: str, value: Any) -> None:
        """Save value to disk cache with current timestamp."""
        cache_path = self._get_cache_path(key)
        
        try:
            data = {
                'timestamp': datetime.now().isoformat(),
                'value': value
            }
            async with self._lock:
                async with aiofiles.open(cache_path, 'w') as f:
                    await f.write(json.dumps(data))
        except (OSError, TypeError) as e:
            logger.error(f"Cache write error for {key}: {str(e)}")
    
    async def _remove_file(self, path: Path) -> None:
        """Remove a file asynchronously."""
        try:
            async with self._lock:
                os.remove(path)
        except OSError as e:
            logger.error(f"Failed to remove file {path}: {str(e)}")
    
    async def clear(self) -> None:
        """Clear all cached files."""
        async with self._lock:
            for cache_file in self.cache_dir.glob("*.json"):
                await self._remove_file(cache_file)

class NetworkCache(DiskCache):
    """Specialized cache for network requests."""
    
    def __init__(self, cache_dir: str = ".cache/network", ttl: int = 3600):
        super().__init__(cache_dir, ttl)
    
    async def cache_response(self, url: str, content: str, headers: Dict[str, str]) -> None:
        """Cache a network response with its headers."""
        await self.set(url, {
            'content': content,
            'headers': headers,
            'cached_at': datetime.now().isoformat()
        })
    
    async def get_response(self, url: str) -> Optional[Dict[str, Any]]:
        """Get cached response if available."""
        return await self.get(url)

class AnalysisCache(DiskCache):
    """Specialized cache for analysis results."""
    
    def __init__(self, cache_dir: str = ".cache/analysis", ttl: int = 86400):
        super().__init__(cache_dir, ttl)
    
    async def cache_analysis(self, url: str, analyzer: str, results: Dict[str, Any]) -> None:
        """Cache analysis results for a specific URL and analyzer."""
        cache_key = f"{url}:{analyzer}"
        await self.set(cache_key, {
            'results': results,
            'analyzer': analyzer,
            'analyzed_at': datetime.now().isoformat()
        })
    
    async def get_analysis(self, url: str, analyzer: str) -> Optional[Dict[str, Any]]:
        """Get cached analysis results if available."""
        cache_key = f"{url}:{analyzer}"
        return await self.get(cache_key) 