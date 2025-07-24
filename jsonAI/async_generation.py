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
        type_handlers = {
            "string": self.generate,
            "number": self.generate,
            "boolean": self.generate,
            # Add more types as needed
        }

        if value_type in type_handlers:
            return await type_handlers[value_type](prompt, **kwargs)
        else:
            raise ValueError(f"Unsupported value type: {value_type}")
