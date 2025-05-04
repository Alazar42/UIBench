"""
Async utility functions for parallel processing and concurrent operations.
"""
import asyncio
from typing import List, Any, Callable, TypeVar, Coroutine
from concurrent.futures import ThreadPoolExecutor
import logging
from functools import partial

T = TypeVar('T')
R = TypeVar('R')

logger = logging.getLogger(__name__)

class AsyncPool:
    """Manages a pool of async tasks with concurrency limits."""
    
    def __init__(self, max_concurrency: int = 10):
        self.semaphore = asyncio.Semaphore(max_concurrency)
        self.tasks: List[asyncio.Task] = []
    
    async def add_task(self, coro: Coroutine) -> None:
        """Add a task to the pool with semaphore control."""
        async with self.semaphore:
            task = asyncio.create_task(coro)
            self.tasks.append(task)
            try:
                await task
            except Exception as e:
                logger.error(f"Task failed with error: {str(e)}")
            finally:
                self.tasks.remove(task)

    async def join(self) -> None:
        """Wait for all tasks in the pool to complete."""
        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)

async def batch_process(items: List[T], 
                       processor: Callable[[T], Coroutine[Any, Any, R]], 
                       batch_size: int = 10) -> List[R]:
    """Process items in batches using async operations.
    
    Args:
        items: List of items to process
        processor: Async function to process each item
        batch_size: Number of items to process concurrently
        
    Returns:
        List of processed results
    """
    pool = AsyncPool(max_concurrency=batch_size)
    results = []
    
    async def process_item(item: T) -> None:
        try:
            result = await processor(item)
            results.append(result)
        except Exception as e:
            logger.error(f"Failed to process item: {str(e)}")
    
    tasks = [pool.add_task(process_item(item)) for item in items]
    await asyncio.gather(*tasks, return_exceptions=True)
    await pool.join()
    
    return results

def run_in_executor(func: Callable[..., T], *args, **kwargs) -> Coroutine[Any, Any, T]:
    """Run a blocking function in a thread pool executor.
    
    Args:
        func: The blocking function to run
        *args: Positional arguments for the function
        **kwargs: Keyword arguments for the function
        
    Returns:
        Coroutine that will yield the function result
    """
    loop = asyncio.get_event_loop()
    return loop.run_in_executor(
        ThreadPoolExecutor(),
        partial(func, *args, **kwargs)
    )

async def gather_with_concurrency(n: int, *tasks) -> List[Any]:
    """Run coroutines with a concurrency limit.
    
    Args:
        n: Maximum number of concurrent tasks
        *tasks: Coroutines to run
        
    Returns:
        List of results from the tasks
    """
    semaphore = asyncio.Semaphore(n)
    
    async def run_with_semaphore(task):
        async with semaphore:
            return await task
    
    return await asyncio.gather(
        *(run_with_semaphore(task) for task in tasks),
        return_exceptions=True
    )

async def retry_async(func: Callable[..., Coroutine],
                     retries: int = 3,
                     delay: float = 1.0,
                     backoff: float = 2.0,
                     exceptions: tuple = (Exception,),
                     *args, **kwargs) -> Any:
    """Retry an async function with exponential backoff.
    
    Args:
        func: Async function to retry
        retries: Maximum number of retries
        delay: Initial delay between retries in seconds
        backoff: Multiplier for delay after each retry
        exceptions: Tuple of exceptions to catch
        *args: Positional arguments for the function
        **kwargs: Keyword arguments for the function
        
    Returns:
        Result from the function
        
    Raises:
        The last exception if all retries fail
    """
    last_exception = None
    current_delay = delay
    
    for attempt in range(retries):
        try:
            return await func(*args, **kwargs)
        except exceptions as e:
            last_exception = e
            if attempt < retries - 1:
                logger.warning(f"Retry attempt {attempt + 1} failed: {str(e)}")
                await asyncio.sleep(current_delay)
                current_delay *= backoff
            else:
                logger.error(f"All retry attempts failed: {str(e)}")
                raise last_exception 