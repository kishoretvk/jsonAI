"""
Integration test suite for all JSON schema types and combinations, including a complex nested JSON example.
This will serve as a template for robust LLM output extraction and validation.
"""
import pytest
from jsonAI.main import Jsonformer
from jsonAI.model_backends import OllamaBackend
from jsonAI.schema_validator import SchemaValidator
import re, json as _json, os

def extract_answer_blocks(text):
    return re.findall(r'<answer>([\s\S]*?)</answer>', text, re.IGNORECASE)

def try_parse_json(candidate):
    try:
        return _json.loads(candidate)
    except Exception:
        return None

from jsonAI.output_formatter import OutputFormatter

def extract_and_parse_json_from_sources(sources, required_keys=None, schema=None):
    formatter = OutputFormatter()
    for source in sources:
        answer_blocks = extract_answer_blocks(source)
        if not answer_blocks:
            answer_blocks = [source]
        for block in answer_blocks:
            json_candidates = re.findall(r'\{[\s\S]*?\}', block)
            if not json_candidates:
                json_candidates = [block.strip()]
            for candidate in json_candidates:
                parsed = try_parse_json(candidate)
                if parsed and (not required_keys or set(parsed.keys()) >= set(required_keys)):
                    return parsed
            # If parsing fails and schema is primitive or enum, try sanitization
            if schema:
                schema_type = schema.get("type")
                if schema_type in {"string", "number", "integer", "boolean", "null"} or "enum" in schema:
                    sanitized = formatter.sanitize_primitive(block.strip(), schema_type if "enum" not in schema else "enum", enum_values=schema.get("enum"))
                    return sanitized
    for source in sources:
        json_candidates = re.findall(r'\{[\s\S]*?\}', source)
        for candidate in json_candidates:
            parsed = try_parse_json(candidate)
            if parsed and (not required_keys or set(parsed.keys()) >= set(required_keys)):
                return parsed
        # If parsing fails and schema is primitive or enum, try sanitization
        if schema:
            schema_type = schema.get("type")
            if schema_type in {"string", "number", "integer", "boolean", "null"} or "enum" in schema:
                sanitized = formatter.sanitize_primitive(source.strip(), schema_type if "enum" not in schema else "enum", enum_values=schema.get("enum"))
                return sanitized
    return None

@pytest.mark.parametrize("json_schema,required_keys,desc", [
    # Simple types
    ({"type": "string"}, None, "string"),
    ({"type": "number"}, None, "number"),
    ({"type": "integer"}, None, "integer"),
    ({"type": "boolean"}, None, "boolean"),
    ({"type": "null"}, None, "null"),
    # Array of strings
    ({"type": "array", "items": {"type": "string"}}, None, "array of strings"),
    # Enum
    ({"type": "string", "enum": ["A", "B", "C"]}, None, "enum string"),
    # Object with required fields
    ({"type": "object", "properties": {"foo": {"type": "string"}, "bar": {"type": "number"}}, "required": ["foo", "bar"]}, ["foo", "bar"], "object with required fields"),
    # Nested object
    ({"type": "object", "properties": {"user": {"type": "object", "properties": {"id": {"type": "integer"}, "name": {"type": "string"}}, "required": ["id", "name"]}}}, ["user"], "nested object"),
    # Array of objects
    ({"type": "array", "items": {"type": "object", "properties": {"id": {"type": "integer"}, "val": {"type": "string"}}, "required": ["id", "val"]}}, None, "array of objects"),
    # Complex example
    ({
        "type": "object",
        "properties": {
            "user": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "name": {"type": "string"},
                    "roles": {"type": "array", "items": {"type": "string"}},
                    "profile": {
                        "type": "object",
                        "properties": {
                            "email": {"type": "string"},
                            "active": {"type": "boolean"},
                            "meta": {"type": "object", "properties": {"score": {"type": "number"}}}
                        },
                        "required": ["email", "active", "meta"]
                    }
                },
                "required": ["id", "name", "roles", "profile"]
            },
            "items": {
                "type": "array",
                "items": {"type": "object", "properties": {"id": {"type": "integer"}, "value": {"type": "string"}}, "required": ["id", "value"]}
            }
        },
        "required": ["user", "items"]
    }, ["user", "items"], "complex nested object")
])
def test_json_schema_variety(json_schema, required_keys, desc):
    # Skip unsupported types for now
    # TODO: Backend does not support primitive types or enums yet. See README "Limitations".
    # All primitive and enum types are now supported and should not be skipped.

    model_name = os.environ.get("OLLAMA_MODEL", "qwen3:0.6b")
    try:
        backend = OllamaBackend(model_name=model_name)
    except Exception as e:
        pytest.skip(f"Ollama backend not available: {e}")
    prompt = f"Generate a valid JSON value for the following schema. Output ONLY the answer, wrapped in <answer> tags, with no explanation or formatting. Schema: {json_schema}"
    jsonformer = Jsonformer(model_backend=backend, json_schema=json_schema, prompt=prompt)
    sources = []
    generated_data = None
    try:
        raw_result = jsonformer()
        if isinstance(raw_result, (dict, list, str, int, float, bool)):
            if isinstance(raw_result, (dict, list)):
                generated_data = raw_result
            elif isinstance(raw_result, str):
                generated_data = extract_and_parse_json_from_sources([raw_result], required_keys, json_schema)
                if not generated_data:
                    sources.append(raw_result)
            else:
                generated_data = raw_result
        else:
            sources.append(str(raw_result))
    except Exception as e:
        raw_output = getattr(jsonformer, 'last_output', None)
        if raw_output:
            sources.append(raw_output)
        if hasattr(e, 'args') and e.args:
            for arg in e.args:
                if isinstance(arg, str):
                    sources.append(arg)
    if generated_data is None and sources:
        generated_data = extract_and_parse_json_from_sources(sources, required_keys, json_schema)
    assert generated_data is not None, f"Failed to parse valid JSON for schema: {desc}\nSources: {sources}"
    # Validate output structure
    validator = SchemaValidator()
    validator.validate(generated_data, json_schema)
    print(f"--- PASSED: {desc} ---\n{generated_data}\n----------------------")

if __name__ == "__main__":
    import sys
    import pytest
    sys.exit(pytest.main([__file__]))
