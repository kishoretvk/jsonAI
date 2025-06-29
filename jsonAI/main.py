from typing import List, Union, Dict, Any, Callable, Optional
import asyncio
from termcolor import cprint
from transformers import PreTrainedModel, PreTrainedTokenizer
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

    def generate_array(
        self, item_schema: Dict[str, Any], obj: List[Any]
    ) -> list:
        for _ in range(self.max_array_length):
            element = self.generate_value(item_schema, obj)
            obj[-1] = element

            obj.append(self.generation_marker)
            input_prompt = self.get_prompt()
            obj.pop()
            # This part is tricky with the new backend.
            # We need a way to get logits from the backend, which might not be possible with Ollama.
            # For now, we will assume the backend can provide logits.
            # This will need to be revisited.
            if hasattr(self.model_backend, "tokenizer") and hasattr(self.model_backend, "model"):
                input_tensor = self.model_backend.tokenizer.encode(
                    input_prompt, return_tensors="pt"
                )
                output = self.model_backend.model.forward(
                    input_tensor.to(self.model_backend.model.device)
                )
                logits = output.logits[0, -1]

                top_indices = logits.topk(30).indices
            else:
                # If the backend doesn't support getting logits, we can't determine if we should continue the array.
                # We will just break.
                break
            if hasattr(self.model_backend, "tokenizer"):
                sorted_indices = logits[top_indices].argsort(
                    descending=True
                )
                sorted_token_ids = top_indices[sorted_indices]

                found_comma = False
                found_close_bracket = False

                for token_id in sorted_token_ids:
                    decoded_token = self.model_backend.tokenizer.decode(
                        token_id, skip_special_tokens=True
                    )
                    if "," in decoded_token:
                        found_comma = True
                        break
                    if "]" in decoded_token:
                        found_close_bracket = True
                        break

                if found_close_bracket or not found_comma:
                    break
            else:
                break

        return obj

    def choose_type_to_generate(self, possible_types: List[str]) -> str:
        possible_types = list(set(possible_types))  # remove duplicates
        self.debug("[choose_type_to_generate]", str(possible_types))
        if len(possible_types) < 1:
            raise ValueError("Union type must not be empty")
        elif len(possible_types) == 1:
            return possible_types[0]

        prompt = self.get_prompt()
        if hasattr(self.model_backend, "tokenizer") and hasattr(self.model_backend, "model"):
            input_tensor = self.model_backend.tokenizer.encode(
                prompt, return_tensors="pt"
            )
            output = self.model_backend.model.forward(
                input_tensor.to(self.model_backend.model.device)
            )
            logits = output.logits[0, -1]
        else:
            # If we can't get logits, we can't choose a type. We'll just pick the first one.
            return possible_types[0]

        max_type = None
        max_logit = -float("inf")
        for possible_type in possible_types:
            try:
                prefix_tokens = self.type_generator.type_prefix_tokens[
                    possible_type
                ]
            except KeyError:
                raise ValueError(f"Unsupported schema type: {possible_type}")
            max_type_logit = logits[prefix_tokens].max()
            if max_type_logit > max_logit:
                max_type = possible_type
                max_logit = max_type_logit

        if max_type is None:
            raise Exception(
                "Unable to find best type to generate for union type"
            )
        self.debug("[choose_type_to_generate]", max_type)
        return max_type

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

        if schema_type == "number":
            if key:
                obj[key] = self.generation_marker
            else:
                obj.append(self.generation_marker)
            return self.type_generator.generate_number(prompt)
        elif schema_type == "integer":
            if key:
                obj[key] = self.generation_marker
            else:
                obj.append(self.generation_marker)
            return self.type_generator.generate_integer(prompt)
        elif schema_type == "boolean":
            if key:
                obj[key] = self.generation_marker
            else:
                obj.append(self.generation_marker)
            return self.type_generator.generate_boolean(prompt)
        elif schema_type == "string":
            if key:
                obj[key] = self.generation_marker
            else:
                obj.append(self.generation_marker)
            return self.type_generator.generate_string(
                prompt, schema.get("maxLength")
            )
        elif schema_type == "datetime":
            if key:
                obj[key] = self.generation_marker
            else:
                obj.append(self.generation_marker)
            return self.type_generator.generate_datetime(prompt)
        elif schema_type == "date":
            if key:
                obj[key] = self.generation_marker
            else:
                obj.append(self.generation_marker)
            return self.type_generator.generate_date(prompt)
        elif schema_type == "time":
            if key:
                obj[key] = self.generation_marker
            else:
                obj.append(self.generation_marker)
            return self.type_generator.generate_time(prompt)
        elif schema_type == "uuid":
            if key:
                obj[key] = self.generation_marker
            else:
                obj.append(self.generation_marker)
            return self.type_generator.generate_uuid(prompt)
        elif schema_type == "binary":
            if key:
                obj[key] = self.generation_marker
            else:
                obj.append(self.generation_marker)
            return self.type_generator.generate_binary(prompt)
        elif schema_type == "p_enum":
            if key:
                obj[key] = self.generation_marker
            else:
                obj.append(self.generation_marker)
            return self.type_generator.generate_p_enum(
                prompt, schema["values"], round=schema.get("round", 3)
            )
        elif schema_type == "p_integer":
            if key:
                obj[key] = self.generation_marker
            else:
                obj.append(self.generation_marker)
            return self.type_generator.generate_p_integer(
                prompt,
                schema["minimum"],
                schema["maximum"],
                round=schema.get("round", 3),
            )
        elif schema_type == "enum":
            if key:
                obj[key] = self.generation_marker
            else:
                obj.append(self.generation_marker)
            return self.type_generator.generate_enum(
                prompt, set(schema["values"])
            )
        elif schema_type == "array":
            new_array = []
            obj[key] = new_array
            return self.generate_array(schema["items"], new_array)
        elif schema_type == "object":
            new_obj = {}
            if key:
                obj[key] = new_obj
            else:
                obj.append(new_obj)
            return self.generate_object(schema["properties"], new_obj)
        elif schema_type == "null":
            return None
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
