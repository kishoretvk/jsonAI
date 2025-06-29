import asyncio
from jsonAI.model_backends import ModelBackend
from typing import Any, Dict

class AsyncGenerator:
    def __init__(self, backend: ModelBackend):
        self.backend = backend
        
    async def generate(self, prompt: str, **kwargs) -> str:
        """Unified async generation interface"""
        if hasattr(self.backend, 'agenerate'):
            return await self.backend.agenerate(prompt, **kwargs)
        return await asyncio.to_thread(self.backend.generate, prompt, **kwargs)

    async def generate_value(self, value_type: str, prompt: str, **kwargs) -> Any:
        """Generate typed value asynchronously"""
        if value_type == "string":
            return await self.generate(prompt, **kwargs)
        # Add other types as needed
        raise ValueError(f"Unsupported value type: {value_type}")
