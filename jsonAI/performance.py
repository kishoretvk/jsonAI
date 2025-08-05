"""
Performance optimization utilities for JsonAI.

This module provides caching, batch processing, and performance monitoring
capabilities to enhance the efficiency of JSON generation operations.
"""

import asyncio
import json
import time
from typing import Any, Dict, List, Optional, Union
from collections import defaultdict
from cachetools import TTLCache, LRUCache
import hashlib
from contextlib import asynccontextmanager

from .main import Jsonformer
# Use the async wrapper defined in main.py to detect async capability
from .main import AsyncJsonformer


class PerformanceMonitor:
    """Monitor and track performance metrics for JSON generation."""
    
    def __init__(self):
        self.metrics = defaultdict(list)
        self.start_times = {}
        
    def start_operation(self, operation_id: str) -> None:
        """Start timing an operation."""
        self.start_times[operation_id] = time.time()
        
    def end_operation(
        self,
        operation_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> float:
        """End timing an operation and record metrics."""
        if operation_id not in self.start_times:
            raise ValueError(f"Operation {operation_id} was not started")
            
        duration = time.time() - self.start_times[operation_id]
        
        metric = {
            'duration': duration,
            'timestamp': time.time(),
            'metadata': metadata or {}
        }
        
        self.metrics[operation_id].append(metric)
        del self.start_times[operation_id]
        
        return duration
        
    @asynccontextmanager
    async def async_timer(self, operation_id: str, 
                          metadata: Optional[Dict[str, Any]] = None):
        """Async context manager for timing operations."""
        self.start_operation(operation_id)
        try:
            yield
        finally:
            self.end_operation(operation_id, metadata)
            
    def get_stats(self, operation_id: str) -> Dict[str, Any]:
        """Get statistics for an operation."""
        if operation_id not in self.metrics:
            return {}
            
        durations = [m['duration'] for m in self.metrics[operation_id]]
        
        return {
            'count': len(durations),
            'avg_duration': sum(durations) / len(durations),
            'min_duration': min(durations),
            'max_duration': max(durations),
            'total_duration': sum(durations)
        }
        
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all operations."""
        return {op_id: self.get_stats(op_id) for op_id in self.metrics.keys()}


class CachedJsonformer(Jsonformer):
    """Jsonformer with intelligent caching capabilities."""
    
    def __init__(self, model, tokenizer, schema: Dict[str, Any], 
                 cache_size: int = 1000, cache_ttl: int = 3600):
        super().__init__(model, tokenizer, schema)
        
        # LRU cache for schema-based results
        self.schema_cache = LRUCache(maxsize=cache_size // 2)
        
        # TTL cache for prompt-based results  
        self.prompt_cache = TTLCache(maxsize=cache_size // 2, ttl=cache_ttl)
        
        self.monitor = PerformanceMonitor()
        
    def _get_cache_key(
        self,
        prompt: str,
        schema: Dict[str, Any],
        **kwargs,
    ) -> str:
        """Generate a cache key for the given parameters."""
        # Create a deterministic hash from prompt, schema, and parameters
        content = {
            'prompt': prompt,
            'schema': schema,
            'kwargs': sorted(kwargs.items())
        }
        
        content_str = json.dumps(content, sort_keys=True)
        return hashlib.sha256(content_str.encode()).hexdigest()
        
    def generate(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate JSON with caching support."""
        cache_key = self._get_cache_key(prompt, self.schema, **kwargs)
        
        # Check caches
        if cache_key in self.prompt_cache:
            return self.prompt_cache[cache_key]
            
        if cache_key in self.schema_cache:
            return self.schema_cache[cache_key]
            
        # Generate and cache result
        # Use synchronous timing instead of async context manager inside sync method
        self.monitor.start_operation('generation')
        try:
            result = super().generate(prompt, **kwargs)
        finally:
            self.monitor.end_operation('generation')
            
        # Store in appropriate cache based on complexity
        schema_complexity = self._calculate_schema_complexity()
        if schema_complexity > 10:  # Complex schemas use TTL cache
            self.prompt_cache[cache_key] = result
        else:  # Simple schemas use LRU cache
            self.schema_cache[cache_key] = result
            
        return result
        
    def _calculate_schema_complexity(self) -> int:
        """Calculate a complexity score for the current schema."""
        def count_properties(obj, depth=0):
            if depth > 10:  # Prevent infinite recursion
                return 0
                
            count = 0
            if isinstance(obj, dict):
                if 'properties' in obj:
                    count += len(obj['properties'])
                    for prop in obj['properties'].values():
                        count += count_properties(prop, depth + 1)
                elif 'items' in obj:
                    count += count_properties(obj['items'], depth + 1)
                    
            return count
            
        return count_properties(self.schema)
        
    def clear_cache(self):
        """Clear all caches."""
        self.schema_cache.clear()
        self.prompt_cache.clear()
        
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics."""
        return {
            'schema_cache': {
                'size': len(self.schema_cache),
                'maxsize': self.schema_cache.maxsize,
                'hits': getattr(self.schema_cache, 'hits', 0),
                'misses': getattr(self.schema_cache, 'misses', 0)
            },
            'prompt_cache': {
                'size': len(self.prompt_cache),
                'maxsize': self.prompt_cache.maxsize,
                'ttl': self.prompt_cache.ttl,
                'hits': getattr(self.prompt_cache, 'hits', 0),
                'misses': getattr(self.prompt_cache, 'misses', 0)
            },
            'performance': self.monitor.get_all_stats()
        }


class BatchProcessor:
    """Process multiple JSON generation requests efficiently."""
    
    def __init__(
        self,
        jsonformer: Union[Jsonformer, CachedJsonformer],
        max_concurrent: int = 5,
    ):
        self.jsonformer = jsonformer
        self.max_concurrent = max_concurrent
        self.monitor = PerformanceMonitor()
        
    async def process_batch(self, requests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process a batch of generation requests."""
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def process_single(request: Dict[str, Any]) -> Dict[str, Any]:
            async with semaphore:
                request_id = request.get('id', f"req_{id(request)}")
                
                async with self.monitor.async_timer(f'batch_item_{request_id}'):
                    # If we have an async jsonformer, use it directly
                    if isinstance(self.jsonformer, AsyncJsonformer):
                        result = await self.jsonformer.generate_async(
                            request['prompt'], **request.get('kwargs', {})
                        )
                    else:
                        # Run sync jsonformer in thread pool
                        loop = asyncio.get_event_loop()
                        result = await loop.run_in_executor(
                            None, 
                            lambda: self.jsonformer.generate(
                                request['prompt'], **request.get('kwargs', {})
                            )
                        )
                        
                return {
                    'id': request_id,
                    'result': result,
                    'status': 'success'
                }
                
        async def safe_process(request: Dict[str, Any]) -> Dict[str, Any]:
            try:
                return await process_single(request)
            except Exception as e:
                request_id = request.get('id', f"req_{id(request)}")
                return {
                    'id': request_id,
                    'error': str(e),
                    'status': 'error'
                }
                
        # Use async context manager correctly with 'async with'
        async with self.monitor.async_timer('batch_total'):
            tasks = [safe_process(req) for req in requests]
            results = await asyncio.gather(*tasks)
            
        return results
        
    def process_batch_sync(self, requests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Synchronous version of batch processing."""
        return asyncio.run(self.process_batch(requests))
        
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get batch processing performance statistics."""
        return self.monitor.get_all_stats()


class OptimizedJsonformer(CachedJsonformer):
    """Highly optimized Jsonformer with all performance features enabled."""
    
    def __init__(self, model, tokenizer, schema: Dict[str, Any],
                 cache_size: int = 2000, cache_ttl: int = 7200,
                 enable_batch_processing: bool = True,
                 max_concurrent: int = 10):
        super().__init__(model, tokenizer, schema, cache_size, cache_ttl)
        
        self.enable_batch_processing = enable_batch_processing
        if enable_batch_processing:
            self.batch_processor = BatchProcessor(self, max_concurrent)
            
        # Additional optimizations
        self._warmup_cache()
        
    def _warmup_cache(self):
        """Pre-warm caches with common patterns."""
        common_prompts = [
            "Generate a simple example",
            "Create a test case", 
            "Provide sample data"
        ]
        
        for prompt in common_prompts:
            try:
                # Generate without storing to warm up internal caches
                self.generate(prompt)
            except Exception:
                # Ignore errors during warmup
                pass
                
    async def generate_batch_async(
        self,
        requests: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Generate multiple JSON responses efficiently."""
        if not self.enable_batch_processing:
            raise ValueError("Batch processing is disabled")
        return await self.batch_processor.process_batch(requests)
        
    def generate_batch(self, requests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Synchronous batch generation."""
        if not self.enable_batch_processing:
            raise ValueError("Batch processing is disabled")
            
        return self.batch_processor.process_batch_sync(requests)
        
    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance and cache statistics."""
        stats = {
            'cache': self.get_cache_stats(),
            'performance': self.monitor.get_all_stats()
        }
        
        if self.enable_batch_processing:
            stats['batch_processing'] = self.batch_processor.get_performance_stats()
            
        return stats
        
    def optimize_for_schema(self, sample_prompts: List[str] = None):
        """Optimize the instance for the current schema."""
        if sample_prompts:
            # Pre-generate with sample prompts to populate caches
            for prompt in sample_prompts:
                try:
                    self.generate(prompt)
                except Exception:
                    continue
                    
        # Calculate optimal cache sizes based on schema complexity
        complexity = self._calculate_schema_complexity()
        
        if complexity > 50:  # Very complex schemas
            self.prompt_cache = TTLCache(maxsize=500, ttl=1800)  # Shorter TTL
            self.schema_cache = LRUCache(maxsize=100)  # Smaller cache
        elif complexity > 20:  # Moderately complex
            self.prompt_cache = TTLCache(maxsize=1000, ttl=3600)
            self.schema_cache = LRUCache(maxsize=500)
        # Keep defaults for simple schemas
