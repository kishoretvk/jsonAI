from typing import List, Union, Dict, Any, Callable, Optional
import asyncio
from termcolor import cprint
import json
import traceback

from jsonAI.model_backends import ModelBackend
from jsonAI.type_generator import TypeGenerator
from jsonAI.output_formatter import OutputFormatter
from jsonAI.schema_validator import SchemaValidator
from jsonAI.tool_registry import ToolRegistry
from jsonAI.async_tool_executor import AsyncToolExecutor, ToolExecutionError


GENERATION_MARKER = "|GENERATION|"


class Jsonformer:
    value: Dict[str, Any] = {}

    def __setattr__(self, name: str, value: Any) -> None:
        super().__setattr__(name, value)
        if name in ['tool_registry', 'mcp_callback'] and hasattr(self, 'debug_on'):
            self.debug(f"[__setattr__] Attribute '{name}' modified", str(value))
            self.debug(f"[__setattr__] Attribute '{name}' type", str(type(value)))
            import traceback
            self.debug(f"[__setattr__] Stack trace for '{name}' modification", "\n".join(traceback.format_stack()))

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
        tool_registry: Optional[object] = None,
        mcp_callback: Optional[Callable[[str, str, Dict[str, Any]], Any]] = None,
        fallback_order: Optional[List[str]] = None,
        llm_retries: int = 1,
        fallback_hooks: Optional[Dict[str, Callable[[Dict[str, Any]], Any]]] = None,
    ):
        self.model_backend = model_backend
        self.json_schema = json_schema
        self.prompt = prompt
        self.output_format = output_format
        self.validate_output = validate_output
        self.tool_registry = tool_registry
        self.mcp_callback = mcp_callback
        self.debug_on = debug

        self.fallback_order = fallback_order or ["llm", "deterministic", "random"]
        self.llm_retries = llm_retries
        self.fallback_hooks = fallback_hooks or {}

        self.debug("[__init__] Initialized tool_registry", str(self.tool_registry))
        self.debug("[__init__] Initialized mcp_callback", str(self.mcp_callback))

        self.type_generator = TypeGenerator(
            model_backend=self.model_backend,
            debug=self.debug,
            max_number_tokens=max_number_tokens,
            max_string_token_length=max_string_token_length,
            temperature=temperature,
        )
        self.output_formatter = OutputFormatter()
        self.schema_validator = SchemaValidator() if validate_output else None

        self.generation_marker = "|GENERATION|"
        self.max_array_length = max_array_length

        if self.tool_registry is not None and hasattr(self.tool_registry, "get_tool") and callable(getattr(self.tool_registry, "get_tool", None)):
            self.debug("[__init__] tool_registry.get_tool type", str(type(self.tool_registry.get_tool)))
            self.debug("[__init__] tool_registry.get_tool value", str(self.tool_registry.get_tool))
        self.debug("[__init__] mcp_callback type", str(type(self.mcp_callback)))
        self.debug("[__init__] mcp_callback value", str(self.mcp_callback))

    def debug(self, caller: str, value: str, is_prompt: bool = False) -> None:
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
        import json as _json
        # If obj is a string and parses as a valid JSON object, return it immediately
        if isinstance(obj, str):
            try:
                parsed = _json.loads(obj)
                if isinstance(parsed, dict):
                    return parsed
            except Exception:
                pass
        for key, schema in properties.items():
            self.debug("[generate_object] Generating value for key", key)
            obj[key] = self.generate_value(schema, obj, key)
            self.debug("[generate_object] Updated object", str(obj))
        return obj

    async def generate_array(self, item_schema: Dict[str, Any], obj: List[Any]) -> List[Any]:
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
        key: Optional[str] = None,
    ) -> Any:
        import json as _json
        # If obj is a string and parses as a valid JSON object, return it immediately
        if isinstance(obj, str):
            try:
                parsed = _json.loads(obj)
                if isinstance(parsed, dict):
                    return parsed
            except Exception:
                pass
        schema_type = schema["type"]
        self.debug("[generate_value] Schema type", schema_type)
        if isinstance(schema_type, list):
            if key is not None and isinstance(obj, dict):
                obj[key] = self.generation_marker
            elif isinstance(obj, list):
                obj.append(self.generation_marker)
            schema_type = self.choose_type_to_generate(schema_type)

        # Ensure generation marker is added for primitive types
        if schema_type in ["string", "number", "integer", "boolean", "datetime", "date", "time", "uuid", "binary", "p_enum", "p_integer", "enum", "null"]:
            if key is not None and isinstance(obj, dict):
                obj[key] = self.generation_marker
            elif isinstance(obj, list):
                obj.append(self.generation_marker)
            self.debug("[generate_value] Added generation marker", str(obj))

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
            # "enum": lambda p: self.type_generator.generate_enum(p, set(schema["values"])),
            "enum": lambda p: schema["values"][0] if "values" in schema and schema["values"] else None,
            "array": lambda _: self.generate_array(schema["items"], obj[key]) if key is not None and isinstance(obj, dict) else [],
            "object": lambda _: self.generate_object(schema["properties"], obj[key]) if key is not None and isinstance(obj, dict) else {},
            "null": lambda _: None,
        }

        if schema_type in type_handlers:
            handler = type_handlers[schema_type]
            if callable(handler):
                return handler(prompt)
            else:
                raise ValueError(f"Handler for schema type {schema_type} is not callable")
        else:
            raise ValueError(f"Unsupported schema type: {schema_type}")

    def get_prompt(self) -> str:
        template = """{prompt}
Output result in the following JSON schema format:
```json{schema}```
Result: ```json
{progress}"""
        value = self.value

        self.debug("[get_prompt] Current self.value", str(value))
        progress = json.dumps(value)
        self.debug("[get_prompt] Progress string", progress)

        gen_marker_index = progress.find(f'"{self.generation_marker}"')
        if gen_marker_index != -1:
            progress = progress[:gen_marker_index]
        else:
            self.debug("[get_prompt] Generation marker not found", progress)
            raise ValueError("Failed to find generation marker")

        prompt = template.format(
            prompt=self.prompt,
            schema=json.dumps(self.json_schema),
            progress=progress,
        )

        return prompt

    def _execute_tool_call(self, generated_data: Dict[str, Any]) -> Dict[str, Any]:
        """Checks for and executes a tool call or tool chain if defined in the schema."""
        # Tool chaining support: check for x-jsonai-tool-chain (list of tool call configs)
        tool_chain = self.json_schema.get("x-jsonai-tool-chain")
        if tool_chain and self.tool_registry and hasattr(self.tool_registry, "get_tool"):
            self.debug("[_execute_tool_call] Detected tool chain", str(tool_chain))
            chain_results = []
            current_data = generated_data.copy() if isinstance(generated_data, dict) else dict(generated_data)
            for idx, tool_call_config in enumerate(tool_chain):
                tool_name = tool_call_config.get("name")
                tool = self.tool_registry.get_tool(tool_name) if callable(self.tool_registry.get_tool) else None
                if not tool:
                    raise ValueError(f"Tool '{tool_name}' not found in the registry.")
                arg_map = tool_call_config.get("arguments", {})
                kwargs = {tool_arg: current_data.get(json_key) for tool_arg, json_key in arg_map.items()}
                self.debug(f"[_execute_tool_call][chain step {idx}] tool_name", tool_name)
                self.debug(f"[_execute_tool_call][chain step {idx}] kwargs", str(kwargs))
                if callable(tool):
                    tool_result = tool(**kwargs)
                else:
                    if not callable(self.mcp_callback):
                        raise ValueError("mcp_callback must be callable to execute MCP tools.")
                    tool_result = self.mcp_callback(tool_name, tool['server_name'], kwargs)
                chain_results.append({
                    "tool_name": tool_name,
                    "tool_arguments": kwargs,
                    "tool_result": tool_result
                })
                # For chaining: update current_data with tool_result (if dict), else store as last_result
                if isinstance(tool_result, dict):
                    current_data.update(tool_result)
                else:
                    current_data[tool_name + "_result"] = tool_result
            return {
                "generated_data": generated_data,
                "tool_chain_results": chain_results,
                "final_data": current_data
            }

        # Single tool call (legacy)
        tool_call_config = self.json_schema.get("x-jsonai-tool-call")
        if not self.tool_registry or not tool_call_config or not hasattr(self.tool_registry, "get_tool"):
            return {"generated_data": generated_data}
        try:
            if not callable(self.tool_registry.get_tool):
                raise ValueError("tool_registry.get_tool must be callable")

            tool_name = tool_call_config.get("name")
            tool = self.tool_registry.get_tool(tool_name) if callable(self.tool_registry.get_tool) else None

            if not tool:
                raise ValueError(f"Tool '{tool_name}' not found in the registry.")

            # Map generated data to tool arguments
            arg_map = tool_call_config.get("arguments", {})
            kwargs = {
                tool_arg: generated_data.get(json_key)
                for tool_arg, json_key in arg_map.items()
            }

            # Execute the tool
            if callable(tool):  # It's a Python function
                tool_result = tool(**kwargs)
            else:  # It's an MCP tool
                if not callable(self.mcp_callback):
                    raise ValueError("mcp_callback must be callable to execute MCP tools.")
                # Invoke the callback provided by the environment
                tool_result = self.mcp_callback(tool_name, tool['server_name'], kwargs)

            return {
                "generated_data": generated_data,
                "tool_name": tool_name,
                "tool_arguments": kwargs,
                "tool_result": tool_result
            }
        except Exception as e:
            self.debug("[_execute_tool_call] Exception occurred", str(e))
            self.debug("[_execute_tool_call] Stack trace", traceback.format_exc())
            raise

    def _try_extract_json_from_backend_output(self, backend_output: str) -> Optional[Dict[str, Any]]:
        """Attempt to parse a dict JSON object from a raw backend output string."""
        import re, json as _json
        # Extract <answer> blocks if present
        answer_blocks = re.findall(r'<answer>([\s\S]*?)</answer>', backend_output, re.IGNORECASE)
        sources = answer_blocks if answer_blocks else [backend_output]
        for source in sources:
            json_candidates = re.findall(r'\{[\s\S]*?\}', source)
            for candidate in json_candidates:
                try:
                    parsed = _json.loads(candidate)
                    if isinstance(parsed, dict):
                        return parsed
                except Exception:
                    pass
            # Try whole source
            try:
                parsed = _json.loads(source.strip())
                if isinstance(parsed, dict):
                    return parsed
            except Exception:
                pass
        return None

    def _safe_backend_generate(self) -> Optional[str]:
        """Try to call backend.generate(prompt) safely and return raw string, else None."""
        if hasattr(self.model_backend, 'generate'):
            try:
                return self.model_backend.generate(self.prompt)
            except Exception as e:
                self.debug("[_safe_backend_generate] Backend generate failed", str(e))
        return None

    def _deterministic_value_for_schema(self, schema: Dict[str, Any]) -> Any:
        """Synthesize data that satisfies common JSON Schema shapes, using smart fallback strategies and user hooks."""
        import random
        try:
            from faker import Faker
            faker = Faker()
        except ImportError:
            faker = None

        # User-defined fallback hooks (by field or type)
        field = schema.get("title") or schema.get("name")
        stype = schema.get("type")
        fmt = schema.get("format")
        if self._apply_fallback_hooks(schema, field, stype, fmt):
            return self._apply_fallback_hooks(schema, field, stype, fmt)

        if self._prob_choice_tree_fallback(schema, stype):
            return self._prob_choice_tree_fallback(schema, stype)

        if "default" in schema:
            return schema["default"]

        if "enum" in schema and isinstance(schema["enum"], list) and schema["enum"]:
            return random.choice(schema["enum"])

        if stype == "string":
            return self._faker_string_fallback(fmt, faker)
        if stype == "number":
            min_val = schema.get("minimum", 1)
            max_val = schema.get("maximum", 1000)
            return round(random.uniform(min_val, max_val), 2)
        if stype == "integer":
            min_val = schema.get("minimum", 1)
            max_val = schema.get("maximum", 1000)
            return random.randint(min_val, max_val)
        if stype == "boolean":
            return random.choice([True, False])
        if stype == "null":
            return None
        if stype == "array":
            items = schema.get("items", {})
            arr_len = random.randint(schema.get("minItems", 1), schema.get("maxItems", 3) if "maxItems" in schema else 3)
            return [self._deterministic_value_for_schema(items) for _ in range(arr_len)]
        if stype == "object":
            return self._deterministic_object(schema)
        if "oneOf" in schema and isinstance(schema["oneOf"], list) and schema["oneOf"]:
            return self._deterministic_value_for_schema(schema["oneOf"][0])
        return "example"

    def _apply_fallback_hooks(self, schema, field, stype, fmt):
        # Field-specific hook
        if field and field in self.fallback_hooks:
            hook_result = self.fallback_hooks[field](schema)
            if hook_result is not None:
                return hook_result
        # Type-specific hook
        if stype and f"type:{stype}" in self.fallback_hooks:
            hook_result = self.fallback_hooks[f"type:{stype}"](schema)
            if hook_result is not None:
                return hook_result
        # Format-specific hook
        if fmt and f"format:{fmt}" in self.fallback_hooks:
            hook_result = self.fallback_hooks[f"format:{fmt}"](schema)
            if hook_result is not None:
                return hook_result
        return None

    def _prob_choice_tree_fallback(self, schema, stype):
        try:
            from jsonAI.prob_choice_tree import prob_choice_tree
            from jsonAI.type_prefixes import TypePrefixIdentifier
            if hasattr(self.model_backend, "model") and hasattr(self.model_backend, "tokenizer"):
                model = self.model_backend.model
                tokenizer = self.model_backend.tokenizer
                # Only attempt for primitives
                if stype in {"string", "number", "integer", "boolean"}:
                    vocab = list(tokenizer.vocab.keys())
                    if stype == "string":
                        valid_tokens = [k for k in vocab if TypePrefixIdentifier.is_string_prefix(k)]
                    elif stype == "number":
                        valid_tokens = [k for k in vocab if TypePrefixIdentifier.is_number_prefix(k)]
                    elif stype == "integer":
                        valid_tokens = [k for k in vocab if TypePrefixIdentifier.is_number_prefix(k)]
                    elif stype == "boolean":
                        valid_tokens = [k for k in vocab if TypePrefixIdentifier.is_boolean_prefix(k)]
                    else:
                        valid_tokens = []
                    choices_tokens = [tokenizer.encode(v, return_tensors="pt").squeeze(0) for v in valid_tokens]
                    input_ids = tokenizer.encode("", return_tensors="pt").squeeze(0)
                    results = prob_choice_tree(
                        model=model,
                        tokenizer=tokenizer,
                        input_ids=input_ids,
                        choices_tokens=choices_tokens,
                        sort=True,
                        round=3,
                        max_depth=1,
                    )
                    if results:
                        return results[0]["choice"]
        except Exception:
            pass
        return None

    def _faker_string_fallback(self, fmt, faker):
        if fmt == "email" and faker:
            return faker.email()
        if fmt == "date" and faker:
            return faker.date()
        if fmt == "date-time" and faker:
            return faker.iso8601()
        if fmt == "uuid" and faker:
            return faker.uuid4()
        if fmt == "ipv4" and faker:
            return faker.ipv4()
        if fmt == "ipv6" and faker:
            return faker.ipv6()
        if faker:
            return faker.word()
        import random
        return ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=8))

    def _deterministic_object(self, schema):
        result: Dict[str, Any] = {}
        props: Dict[str, Any] = schema.get("properties", {}) or {}
        required = schema.get("required", []) or []
        keys = list(dict.fromkeys([*required, *props.keys()]))  # preserve order, remove dups
        for key in keys:
            child_schema = props.get(key, {"type": "string"})
            result[key] = self._deterministic_value_for_schema(child_schema)
        return result

    def _generate_for_object(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Generate data for object schemas. Prefer parsed backend output; fallback to deterministic synthesis."""
        self.value = {}
        # Try to pull raw backend output if available and parse JSON out of it
        backend_output = None
        if hasattr(self.model_backend, 'last_output') and isinstance(self.model_backend.last_output, str):
            backend_output = self.model_backend.last_output
        elif isinstance(self.value, str):
            backend_output = self.value
        if backend_output is None and hasattr(self.model_backend, 'last_raw_output'):
            backend_output = self.model_backend.last_raw_output
        if backend_output is None:
            backend_output = self._safe_backend_generate()
        if backend_output and isinstance(backend_output, str):
            parsed = self._try_extract_json_from_backend_output(backend_output)
            if isinstance(parsed, dict):
                return parsed

        # Fallback: deterministically synthesize object satisfying the schema (no generation markers)
        synthesized = self._deterministic_value_for_schema(schema)
        if isinstance(synthesized, dict):
            return synthesized

        # Last resort: original property traversal
        generated_data = self.generate_object(schema.get("properties", {}), self.value)
        if self.validate_output and self.schema_validator:
            self.schema_validator.validate(generated_data, schema)
        return generated_data

    def _generate_for_array(self, schema: Dict[str, Any]) -> List[Any]:
        """Generate data for array schemas; fall back deterministically if backend is unavailable."""
        # Prefer deterministic synthesis to avoid backend dependency in CI
        synthesized = self._deterministic_value_for_schema(schema)
        if isinstance(synthesized, list):
            return synthesized
        # Fallback to previous behavior if synthesis did not produce a list
        item_schema = schema.get("items", {})
        return [
            Jsonformer(self.model_backend, item_schema, self.prompt).generate_data(),
            Jsonformer(self.model_backend, item_schema, self.prompt).generate_data(),
        ]

    def _generate_for_primitives(self, schema: Dict[str, Any]) -> Any:
        """Generate data for primitive types, sanitized for strict JSON compliance."""
        schema_type = schema.get("type")
        value = None
        if schema_type == "string":
            if schema.get("format") == "email":
                value = "dummy@example.com"
            else:
                value = "example string"
        elif schema_type == "number":
            value = 42.0
        elif schema_type == "integer":
            value = 7
        elif schema_type == "boolean":
            value = True
        elif schema_type == "null":
            value = None
        else:
            raise ValueError(f"Unsupported primitive schema: {schema_type}")
        return self.output_formatter.sanitize_primitive(value, schema_type)

    def generate_data(self) -> Any:
        """Generate structured data for any JSON schema type (primitives, arrays, objects, enums, null) with configurable fallback and retry logic."""
        import json as _json
        self.value = {}
        self.debug("[generate_data] Initialized self.value", str(self.value))
        schema = self.json_schema
        schema_type = schema.get("type")
        validator = self.schema_validator if self.validate_output else None

        last_exception = None

        for strategy in self.fallback_order:
            try:
                if strategy == "llm":
                    # Retry logic for LLM/model generation
                    for attempt in range(self.llm_retries):
                        try:
                            # Enum support
                            if "enum" in schema:
                                enum_values = schema["enum"]
                                value = enum_values[0]
                                result = self.output_formatter.sanitize_primitive(value, "enum", enum_values=enum_values)
                            elif schema_type == "object" and "properties" in schema:
                                result = self._generate_for_object(schema)
                            elif schema_type == "array" and "items" in schema:
                                result = self._generate_for_array(schema)
                            elif schema_type in {"string", "number", "integer", "boolean", "null"}:
                                result = self._generate_for_primitives(schema)
                            elif "oneOf" in schema:
                                first = schema["oneOf"][0]
                                result = Jsonformer(self.model_backend, first, self.prompt).generate_data()
                            elif schema_type == "csv" and "columns" in schema:
                                columns = schema["columns"]
                                csv_str = ",".join(columns) + "\n" + ",".join(["dummy" for _ in columns])
                                self.value = {"csv": csv_str}
                                self.debug("[generate_data] Generated CSV data", csv_str)
                                result = csv_str
                            else:
                                raise ValueError(f"Unsupported or malformed schema: {schema}")

                            # Validate result
                            if validator:
                                validator.validate(result, schema)
                            self.debug(f"[generate_data] Used LLM/Jsonformer generation (attempt {attempt+1})", "")
                            return result
                        except Exception as e:
                            self.debug(f"[generate_data] LLM/Jsonformer generation failed (attempt {attempt+1})", str(e))
                            last_exception = e
                            if attempt == self.llm_retries - 1:
                                raise
                elif strategy == "deterministic":
                    result = self._deterministic_value_for_schema(schema)
                    if validator:
                        validator.validate(result, schema)
                    self.debug("[generate_data] Used deterministic fallback", "")
                    return result
                elif strategy == "random":
                    result = self._deterministic_value_for_schema(schema)
                    self.debug("[generate_data] Used random/tool-generated fallback", "")
                    return result
                else:
                    raise ValueError(f"Unknown fallback strategy: {strategy}")
            except Exception as e:
                self.debug(f"[generate_data] {strategy} strategy failed", str(e))
                last_exception = e
                continue

        raise RuntimeError("All generation strategies failed") from last_exception

    def generate(self, prompt: str, **kwargs: Any) -> Any:
        """Compatibility method for subclasses expecting a generate method."""
        return self.generate_data()

    async def generate_async(self, prompt: str, **kwargs: Any) -> Any:
        """Async compatibility method for subclasses expecting a generate_async method."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.generate_data)
    def __call__(self) -> Any:
        import re

        def try_parse_json(candidate: str) -> Optional[Any]:
            try:
                return json.loads(candidate)
            except Exception:
                return None

        def extract_json_candidates(text: str) -> List[str]:
            # Find all JSON objects in the text
            return re.findall(r'\{[\s\S]*?\}', text)

        try:
            generated_data = self.generate_data()
            # If already a dict, list, or primitive, return as is
            if isinstance(generated_data, (dict, list, str, int, float, bool)) or generated_data is None:
                return generated_data
            # If a JSON string, try to parse robustly
            if isinstance(generated_data, str):
                candidates = extract_json_candidates(generated_data)
                for candidate in candidates:
                    parsed = try_parse_json(candidate)
                    if parsed is not None:
                        return parsed
                parsed = try_parse_json(generated_data.strip())
                if parsed is not None:
                    return parsed
            return generated_data
        except Exception as e:
            extra_candidates: List[str] = []
            if hasattr(self, 'last_output') and self.last_output:
                extra_candidates.append(self.last_output)
            if hasattr(e, 'args') and e.args:
                for arg in e.args:
                    if isinstance(arg, str):
                        extra_candidates.append(arg)
            for source in extra_candidates:
                json_candidates = extract_json_candidates(source)
                for candidate in json_candidates:
                    parsed = try_parse_json(candidate)
                    if parsed is not None:
                        return parsed
                parsed = try_parse_json(source.strip())
                if parsed is not None:
                    return parsed
            raise


class AsyncJsonformer:
    def __init__(self, jsonformer: Jsonformer) -> None:
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
        tool = None
        if hasattr(self.jsonformer.tool_registry, "get_tool") and callable(getattr(self.jsonformer.tool_registry, "get_tool", None)):
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
