import asyncio
from typing import Callable, Any, Dict
from functools import partial

class ToolExecutionError(Exception):
    pass

class AsyncToolExecutor:
    def __init__(self, max_retries: int = 3, backoff_factor: float = 0.5):
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.pending_tasks = []
        
    async def execute(self, tool_func: Callable, *args, **kwargs) -> Any:
        """Execute a tool function with retry logic and detailed error reporting."""
        for attempt in range(self.max_retries):
            try:
                if asyncio.iscoroutinefunction(tool_func):
                    result = await tool_func(*args, **kwargs)
                else:
                    loop = asyncio.get_running_loop()
                    result = await loop.run_in_executor(None, partial(tool_func, *args, **kwargs))
                return result
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise ToolExecutionError(f"Tool '{tool_func.__name__}' failed after {self.max_retries} attempts: {e}")
                await asyncio.sleep(self.backoff_factor * (2 ** attempt))

    def add_task(self, tool_func: Callable, *args, **kwargs):
        """Add a tool execution task to the queue"""
        task = self.execute(tool_func, *args, **kwargs)
        self.pending_tasks.append(task)
        
    async def run_all(self) -> list:
        """Execute all pending tasks concurrently and retain failed tasks for analysis."""
        results = await asyncio.gather(*self.pending_tasks, return_exceptions=True)
        self.failed_tasks = [task for task in results if isinstance(task, Exception)]
        self.pending_tasks = []
        return results

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self.pending_tasks:
            await self.run_all()
