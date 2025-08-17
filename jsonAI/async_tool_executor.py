import asyncio
from typing import Callable, Any, Dict, Awaitable, List
from functools import partial

class ToolExecutionError(Exception):
    pass

class AsyncToolExecutor:
    def __init__(self, max_retries: int = 3, backoff_factor: float = 0.5):
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        # Track pending asyncio tasks; explicit type for mypy
        self.pending_tasks: List[asyncio.Task[Any]] = []
        # Track failed results from run_all for postmortem (optional)
        self.failed_tasks: List[Exception] = []
        
    async def execute(self, tool_func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
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

    def add_task(self, tool_func: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
        """Add a tool execution task to the queue"""
        # Wrap coroutine in an actual Task to ensure scheduling and typing clarity
        task = asyncio.create_task(self.execute(tool_func, *args, **kwargs))
        self.pending_tasks.append(task)
        
    async def run_all(self) -> list[Any]:
        """Execute all pending tasks concurrently and retain failed tasks for analysis."""
        results: list[Any] = await asyncio.gather(*self.pending_tasks, return_exceptions=True)
        self.failed_tasks = [exc for exc in results if isinstance(exc, Exception)]
        self.pending_tasks = []
        return results

    async def __aenter__(self) -> "AsyncToolExecutor":
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: object | None
    ) -> None:
        if self.pending_tasks:
            await self.run_all()
