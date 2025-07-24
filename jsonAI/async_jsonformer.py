import asyncio
from jsonAI.async_generation import AsyncGenerator
from jsonAI.model_backends import ModelBackend
from jsonAI.type_generator import TypeGenerator
from typing import Dict, Any, Optional
import json

class FullAsyncJsonformer:
    def __init__(
        self,
        model_backend: ModelBackend,
        json_schema: Dict[str, Any],
        prompt: str,
        *,
        output_format: str = "json",
        validate_output: bool = False,
        debug: bool = False,
        max_array_length: int = 10,
        max_number_tokens: int = 6,
        temperature: float = 1.0,
        max_string_token_length: int = 175,
        tool_registry: Optional[Any] = None,
        mcp_callback: Optional[Any] = None,
    ):
        self.async_generator = AsyncGenerator(model_backend)
        self.json_schema = json_schema
        self.prompt = prompt
        self.output_format = output_format
        self.validate_output = validate_output
        self.tool_registry = tool_registry
        self.mcp_callback = mcp_callback
        self.debug_on = debug
        self.max_array_length = max_array_length
        self.generation_marker = "|GENERATION|"
        
        self.type_generator = TypeGenerator(
            model_backend=model_backend,
            debug=self.debug_on,
            max_number_tokens=max_number_tokens,
            max_string_token_length=max_string_token_length,
            temperature=temperature,
        )

    async def agenerate_object(
        self, properties: Dict[str, Any], obj: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate an object asynchronously."""
        tasks = [self.agenerate_value(schema, obj, key) for key, schema in properties.items()]
        results = await asyncio.gather(*tasks)
        return dict(zip(properties.keys(), results))

    async def agenerate_value(
        self,
        schema: Dict[str, Any],
        obj: Dict[str, Any],
        key: str
    ) -> Any:
        schema_type = schema["type"]
        prompt = self.get_prompt()
        
        if schema_type == "string":
            return await self.async_generator.generate(prompt)
        elif schema_type == "number":
            return await asyncio.to_thread(
                self.type_generator.generate_number, prompt
            )
        elif schema_type == "integer":
            return await asyncio.to_thread(
                self.type_generator.generate_integer, prompt
            )
        elif schema_type == "boolean":
            return await asyncio.to_thread(
                self.type_generator.generate_boolean, prompt
            )
        # Add other types as needed
        else:
            raise ValueError(f"Unsupported schema type: {schema_type}")

    def get_prompt(self) -> str:
        # Simplified prompt generation
        return f"{self.prompt}\nOutput JSON:"

    async def __call__(self) -> Dict[str, Any]:
        result = {}
        await self.agenerate_object(self.json_schema["properties"], result)
        return result
