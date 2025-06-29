from typing import List, Union, Dict, Any, Callable, Optional
import asyncio
from termcolor import cprint
import json

from jsonAI.model_backends import ModelBackend
from jsonAI.type_generator import TypeGenerator
from jsonAI.output_formatter import OutputFormatter
from jsonAI.schema_validator import SchemaValidator
from jsonAI.tool_registry import ToolRegistry
from jsonAI.async_tool_executor import AsyncToolExecutor, ToolExecutionError


GENERATION_MARKER = "|GENERATION|"


class Jsonformer:
    value: Dict[str, Any] = {}

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
        tool_registry: Optional[ToolRegistry] = None,
        mcp_callback: Optional[Callable] = None,
    ):
        self.model_backend = model_backend
        self.json_schema = json_schema
        self.prompt = prompt
        self.output_format = output_format
        self.validate_output = validate_output
        self.tool_registry = tool_registry
        self.mcp_callback = mcp_callback
        self.debug_on = debug

        self.type_generator = TypeGenerator(
            model_backend=self.model_backend,
            debug=self.debug_on,
            max_number_tokens=max_number_tokens,
            max_string_token_length=max_string_token_length,
            temperature=temperature,
        )
        self.output_formatter = OutputFormatter()
        self.schema_validator = SchemaValidator() if validate_output else None

        self.generation_marker = "|GENERATION|"
        self.max_array_length = max_array_length

    def debug(self, caller: str, value: str, is_prompt: bool = False):
        if self.debug_on:
            if is_prompt:
                cprint(caller, "green", end=" ")
                cprint(value, "yellow")
            else:
                cprint(caller, "green", end=" ")
                cprint(value, "blue")

    def generate_object(
        self, properties: Dict[str, Any], obj: Dict[str, Any]
    ) -> Dict[str, Any]:
        for key, schema in properties.items():
            self.debug("[generate_object] generating value for", key)
            obj[key] = self.generate_value(schema, obj, key)
        return obj

    async def generate_array(self, item_schema: Dict[str, Any], obj: List[Any]) -> list:
        """Generate an array following the item schema.
        
        Uses TypeGenerator's helper methods when possible for consistent behavior.
        """
        tasks = [self.generate_value(item_schema, obj) for _ in range(self.max_array_length)]
        results = await asyncio.gather(*tasks)
        return results

    def choose_type_to_generate(self, possible_types: List[str]) -> str:
        """Select which type to generate from possible options.
        
        Delegates to TypeGenerator's choose_type() method.
        """
        return self.type_generator.choose_type(
            prompt=self.get_prompt(),
            possible_types=possible_types
        )

    # Refactor generate_value to modularize schema type handling
    def generate_value(
        self,
        schema: Dict[str, Any],
        obj: Union[Dict[str, Any], List[Any]],
        key: Union[str, None] = None,
    ) -> Any:
        schema_type = schema["type"]
        if isinstance(schema_type, list):
            if key:
                obj[key] = self.generation_marker
            else:
                obj.append(self.generation_marker)
            schema_type = self.choose_type_to_generate(schema_type)

        prompt = self.get_prompt()

        type_handlers = {
            "number": self.type_generator.generate_number,
            "integer": self.type_generator.generate_integer,
            "boolean": self.type_generator.generate_boolean,
            "string": lambda p: self.type_generator.generate_string(p, schema.get("maxLength")),
            "datetime": self.type_generator.generate_datetime,
            "date": self.type_generator.generate_date,
            "time": self.type_generator.generate_time,
            "uuid": self.type_generator.generate_uuid,
            "binary": self.type_generator.generate_binary,
            "p_enum": lambda p: self.type_generator.generate_p_enum(p, schema["values"], round=schema.get("round", 3)),
            "p_integer": lambda p: self.type_generator.generate_p_integer(p, schema["minimum"], schema["maximum"], round=schema.get("round", 3)),
            "enum": lambda p: self.type_generator.generate_enum(p, set(schema["values"])),
            "array": lambda _: self.generate_array(schema["items"], obj[key]),
            "object": lambda _: self.generate_object(schema["properties"], obj[key]),
            "null": lambda _: None,
        }

        if schema_type in type_handlers:
            if key:
                obj[key] = self.generation_marker
            else:
                obj.append(self.generation_marker)
            return type_handlers[schema_type](prompt)
        else:
            raise ValueError(f"Unsupported schema type: {schema_type}")

    def get_prompt(self):
        template = """{prompt}
Output result in the following JSON schema format:
```json{schema}```
Result: ```json
{progress}"""
        value = self.value

        progress = json.dumps(value)
        gen_marker_index = progress.find(f'"{self.generation_marker}"')
        if gen_marker_index != -1:
            progress = progress[:gen_marker_index]
        else:
            raise ValueError("Failed to find generation marker")

        prompt = template.format(
            prompt=self.prompt,
            schema=json.dumps(self.json_schema),
            progress=progress,
        )

        return prompt

    def _execute_tool_call(self, generated_data: Dict[str, Any]) -> Dict[str, Any]:
        """Checks for and executes a tool call if defined in the schema."""
        tool_call_config = self.json_schema.get("x-jsonai-tool-call")
        
        if not self.tool_registry or not tool_call_config:
            return {"generated_data": generated_data}

        tool_name = tool_call_config.get("name")
        tool = self.tool_registry.get_tool(tool_name)

        if not tool:
            raise ValueError(f"Tool '{tool_name}' not found in the registry.")

        # Map generated data to tool arguments
        arg_map = tool_call_config.get("arguments", {})
        kwargs = {
            tool_arg: generated_data.get(json_key)
            for tool_arg, json_key in arg_map.items()
        }

        # Execute the tool
        if callable(tool): # It's a Python function
            tool_result = tool(**kwargs)
        else: # It's an MCP tool
            if not self.mcp_callback:
                raise ValueError("mcp_callback must be provided to execute MCP tools.")
            # Invoke the callback provided by the environment
            tool_result = self.mcp_callback(tool_name, tool['server_name'], kwargs)
            
        return {
            "generated_data": generated_data,
            "tool_name": tool_name,
            "tool_arguments": kwargs,
            "tool_result": tool_result
        }

    def generate_data(self) -> Dict[str, Any]:
        """Generate structured data without tool execution"""
        self.value = {}
        generated_data = self.generate_object(
            self.json_schema["properties"], self.value
        )
        
        # Validate if enabled
        if self.validate_output and self.schema_validator:
            self.schema_validator.validate(generated_data, self.json_schema)
            
        return generated_data

    def __call__(self) -> Union[Dict[str, Any], str]:
        generated_data = self.generate_data()
        
        # Check for tool call and execute if needed
        result = self._execute_tool_call(generated_data)

        # Format the output
        formatted_output = self.output_formatter.format(
            result, self.output_format
        )
        return formatted_output


class AsyncJsonformer:
    def __init__(self, jsonformer: Jsonformer):
        self.jsonformer = jsonformer
        self.tool_executor = AsyncToolExecutor()

    async def __call__(self) -> Union[Dict[str, Any], str]:
        # Run synchronous generation in thread
        loop = asyncio.get_running_loop()
        generated_data = await loop.run_in_executor(
            None, self.jsonformer.generate_data
        )
        
        # Check for tool call
        tool_call_config = self.jsonformer.json_schema.get("x-jsonai-tool-call")
        if not self.jsonformer.tool_registry or not tool_call_config:
            return generated_data

        # Execute tool asynchronously
        tool_name = tool_call_config.get("name")
        tool = self.jsonformer.tool_registry.get_tool(tool_name)
        if not tool:
            raise ValueError(f"Tool '{tool_name}' not found in registry")

        # Prepare tool arguments
        arg_map = tool_call_config.get("arguments", {})
        kwargs = {
            tool_arg: generated_data.get(json_key)
            for tool_arg, json_key in arg_map.items()
        }

        # Execute tool
        if callable(tool):
            tool_result = await self.tool_executor.execute(tool, **kwargs)
        else:  # MCP tool
            if not self.jsonformer.mcp_callback:
                raise ValueError("mcp_callback required for MCP tools")
            tool_result = await self.tool_executor.execute(
                self.jsonformer.mcp_callback, 
                tool_name, 
                tool['server_name'], 
                kwargs
            )
            
        return {
            "generated_data": generated_data,
            "tool_name": tool_name,
            "tool_arguments": kwargs,
            "tool_result": tool_result
        }
