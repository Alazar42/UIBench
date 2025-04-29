"""
Specialized caching implementation for analysis results.
"""
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from pathlib import Path
import logging
from dataclasses import dataclass, asdict
import hashlib
from .cache import DiskCache

logger = logging.getLogger(__name__)

@dataclass
class AnalysisResult:
    """Container for analysis results with metadata."""
    analyzer_id: str
    url: str
    timestamp: datetime
    results: Dict[str, Any]
    metadata: Dict[str, Any]
    version: str
    dependencies: List[str] = None

class AnalysisCache(DiskCache):
    """Specialized cache for storing and retrieving analysis results."""
    
    def __init__(self, cache_dir: str = ".cache/analysis",
                 ttl: int = 86400,
                 version: str = "1.0.0"):
        super().__init__(cache_dir, ttl)
        self.version = version
        
    def _compute_cache_key(self, url: str, analyzer_id: str) -> str:
        """Compute a unique cache key for the URL and analyzer."""
        key = f"{url}:{analyzer_id}:{self.version}"
        return hashlib.sha256(key.encode()).hexdigest()
    
    def store_result(self, result: AnalysisResult) -> None:
        """Store an analysis result in the cache."""
        key = self._compute_cache_key(result.url, result.analyzer_id)
        
        try:
            data = asdict(result)
            # Convert datetime to ISO format for JSON serialization
            data['timestamp'] = data['timestamp'].isoformat()
            self.set(key, data)
            logger.debug(f"Stored analysis result for {result.url} ({result.analyzer_id})")
        except Exception as e:
            logger.error(f"Failed to store analysis result: {str(e)}")
    
    def get_result(self, url: str, analyzer_id: str) -> Optional[AnalysisResult]:
        """Retrieve an analysis result from the cache if available and valid."""
        key = self._compute_cache_key(url, analyzer_id)
        data = self.get(key)
        
        if data:
            try:
                # Convert ISO format string back to datetime
                data['timestamp'] = datetime.fromisoformat(data['timestamp'])
                return AnalysisResult(**data)
            except Exception as e:
                logger.error(f"Failed to load analysis result: {str(e)}")
                return None
        return None
    
    def is_valid(self, result: AnalysisResult) -> bool:
        """Check if a cached result is still valid."""
        if not result:
            return False
            
        # Check version compatibility
        if result.version != self.version:
            return False
            
        # Check TTL
        age = datetime.now() - result.timestamp
        if age > timedelta(seconds=self.ttl):
            return False
            
        # Check dependencies if specified
        if result.dependencies:
            for dep in result.dependencies:
                dep_path = Path(dep)
                if not dep_path.exists():
                    return False
                    
        return True
    
    def invalidate(self, url: str = None, analyzer_id: str = None) -> None:
        """Invalidate cache entries matching the given criteria."""
        if url and analyzer_id:
            key = self._compute_cache_key(url, analyzer_id)
            self._remove_cache_file(key)
        else:
            pattern = ""
            if url:
                pattern = hashlib.sha256(f"{url}:".encode()).hexdigest()[:10]
            elif analyzer_id:
                pattern = hashlib.sha256(f":{analyzer_id}:".encode()).hexdigest()[:10]
                
            for cache_file in self.cache_dir.glob(f"*{pattern}*.json"):
                try:
                    cache_file.unlink()
                except OSError as e:
                    logger.error(f"Failed to remove cache file {cache_file}: {str(e)}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_size = 0
        num_entries = 0
        analyzers = set()
        oldest_entry = None
        newest_entry = None
        
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                data = json.loads(cache_file.read_text())
                total_size += cache_file.stat().st_size
                num_entries += 1
                analyzers.add(data.get('analyzer_id'))
                
                timestamp = datetime.fromisoformat(data.get('timestamp'))
                if not oldest_entry or timestamp < oldest_entry:
                    oldest_entry = timestamp
                if not newest_entry or timestamp > newest_entry:
                    newest_entry = timestamp
                    
            except Exception as e:
                logger.error(f"Failed to read cache file {cache_file}: {str(e)}")
        
        return {
            'total_size_bytes': total_size,
            'num_entries': num_entries,
            'num_analyzers': len(analyzers),
            'analyzers': list(analyzers),
            'oldest_entry': oldest_entry.isoformat() if oldest_entry else None,
            'newest_entry': newest_entry.isoformat() if newest_entry else None
        }
    
    def optimize(self, max_size_bytes: int = None) -> None:
        """Optimize the cache by removing old entries if needed."""
        if not max_size_bytes:
            return
            
        stats = self.get_stats()
        if stats['total_size_bytes'] <= max_size_bytes:
            return
            
        # Get all cache files sorted by modification time
        cache_files = []
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                mtime = cache_file.stat().st_mtime
                size = cache_file.stat().st_size
                cache_files.append((mtime, size, cache_file))
            except OSError as e:
                logger.error(f"Failed to stat cache file {cache_file}: {str(e)}")
                
        cache_files.sort()  # Sort by modification time
        
        # Remove oldest files until we're under the size limit
        current_size = stats['total_size_bytes']
        for mtime, size, cache_file in cache_files:
            if current_size <= max_size_bytes:
                break
                
            try:
                cache_file.unlink()
                current_size -= size
                logger.debug(f"Removed old cache file: {cache_file}")
            except OSError as e:
                logger.error(f"Failed to remove cache file {cache_file}: {str(e)}")
                
class AnalysisCacheManager:
    """Manager for handling multiple analysis caches."""
    
    def __init__(self, base_cache_dir: str = ".cache"):
        self.base_cache_dir = Path(base_cache_dir)
        self.caches: Dict[str, AnalysisCache] = {}
    
    def get_cache(self, name: str, ttl: int = 86400, version: str = "1.0.0") -> AnalysisCache:
        """Get or create an analysis cache instance."""
        if name not in self.caches:
            cache_dir = self.base_cache_dir / name
            self.caches[name] = AnalysisCache(str(cache_dir), ttl, version)
        return self.caches[name]
    
    def clear_all(self) -> None:
        """Clear all managed caches."""
        for cache in self.caches.values():
            cache.clear()
            
    def get_total_stats(self) -> Dict[str, Any]:
        """Get combined statistics for all managed caches."""
        total_stats = {
            'total_size_bytes': 0,
            'num_entries': 0,
            'num_caches': len(self.caches),
            'cache_names': list(self.caches.keys()),
            'per_cache_stats': {}
        }
        
        for name, cache in self.caches.items():
            stats = cache.get_stats()
            total_stats['total_size_bytes'] += stats['total_size_bytes']
            total_stats['num_entries'] += stats['num_entries']
            total_stats['per_cache_stats'][name] = stats
            
        return total_stats 