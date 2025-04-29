"""
Performance optimization utilities for analysis operations.
"""
import time
import asyncio
from typing import Any, Callable, Dict, List, TypeVar, Optional
from functools import wraps
import logging
import cProfile
import pstats
from io import StringIO
from contextlib import contextmanager
import tracemalloc
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

T = TypeVar('T')

@dataclass
class PerformanceMetrics:
    """Container for performance metrics."""
    execution_time: float
    memory_peak: int
    start_time: datetime
    end_time: datetime
    additional_data: Dict[str, Any] = None

def async_timed():
    """Decorator to measure async function execution time."""
    def wrapper(func):
        @wraps(func)
        async def wrapped(*args, **kwargs):
            start = time.perf_counter()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                end = time.perf_counter()
                total = end - start
                logger.debug(f"{func.__name__} took {total:.2f} seconds")
        return wrapped
    return wrapper

@contextmanager
def profile_code(name: str = None):
    """Context manager for profiling code blocks."""
    profiler = cProfile.Profile()
    profiler.enable()
    try:
        yield
    finally:
        profiler.disable()
        s = StringIO()
        ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
        ps.print_stats()
        if name:
            logger.debug(f"Profile for {name}:\n{s.getvalue()}")
        else:
            logger.debug(f"Profile results:\n{s.getvalue()}")

@contextmanager
def memory_tracker(name: str = None):
    """Context manager for tracking memory usage."""
    tracemalloc.start()
    try:
        yield
    finally:
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        if name:
            logger.debug(f"Memory usage for {name} - Current: {current / 10**6:.1f}MB, Peak: {peak / 10**6:.1f}MB")
        else:
            logger.debug(f"Memory usage - Current: {current / 10**6:.1f}MB, Peak: {peak / 10**6:.1f}MB")

class PerformanceMonitor:
    """Monitor and track performance metrics for operations."""
    
    def __init__(self):
        self.metrics: Dict[str, List[PerformanceMetrics]] = {}
    
    @contextmanager
    def monitor(self, operation_name: str):
        """Context manager to monitor an operation's performance."""
        start_time = datetime.now()
        tracemalloc.start()
        start = time.perf_counter()
        
        try:
            yield
        finally:
            end = time.perf_counter()
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            
            metrics = PerformanceMetrics(
                execution_time=end - start,
                memory_peak=peak,
                start_time=start_time,
                end_time=datetime.now()
            )
            
            if operation_name not in self.metrics:
                self.metrics[operation_name] = []
            self.metrics[operation_name].append(metrics)
    
    def get_metrics(self, operation_name: str) -> List[PerformanceMetrics]:
        """Get metrics for a specific operation."""
        return self.metrics.get(operation_name, [])
    
    def get_average_execution_time(self, operation_name: str) -> Optional[float]:
        """Get average execution time for an operation."""
        metrics = self.get_metrics(operation_name)
        if not metrics:
            return None
        return sum(m.execution_time for m in metrics) / len(metrics)
    
    def get_peak_memory_usage(self, operation_name: str) -> Optional[int]:
        """Get peak memory usage for an operation."""
        metrics = self.get_metrics(operation_name)
        if not metrics:
            return None
        return max(m.memory_peak for m in metrics)
    
    def clear_metrics(self, operation_name: Optional[str] = None):
        """Clear metrics for an operation or all operations."""
        if operation_name:
            self.metrics.pop(operation_name, None)
        else:
            self.metrics.clear()

class RateLimiter:
    """Rate limiter for controlling request frequency."""
    
    def __init__(self, max_requests: int, time_window: float):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests: List[float] = []
        self._lock = asyncio.Lock()
    
    async def acquire(self):
        """Acquire a rate limit slot."""
        async with self._lock:
            now = time.time()
            
            # Remove old requests
            while self.requests and now - self.requests[0] > self.time_window:
                self.requests.pop(0)
            
            # Wait if we're at the limit
            if len(self.requests) >= self.max_requests:
                wait_time = self.requests[0] + self.time_window - now
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
                    # Recheck after waiting
                    return await self.acquire()
            
            self.requests.append(now)
    
    async def __aenter__(self):
        await self.acquire()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

def memoize(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator to memoize function results."""
    cache: Dict[str, T] = {}
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        key = str((args, sorted(kwargs.items())))
        if key not in cache:
            cache[key] = func(*args, **kwargs)
        return cache[key]
    
    # Add cache clear method
    wrapper.clear_cache = lambda: cache.clear()
    return wrapper

async def batch_process(items: List[T],
                       process_func: Callable[[T], Any],
                       batch_size: int = 10,
                       delay: float = 0.1) -> List[Any]:
    """Process items in batches with delay between batches."""
    results = []
    
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        batch_results = await asyncio.gather(
            *(process_func(item) for item in batch)
        )
        results.extend(batch_results)
        
        if i + batch_size < len(items):
            await asyncio.sleep(delay)
    
    return results 