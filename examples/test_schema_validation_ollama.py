import pytest
import json
from jsonAI.main import Jsonformer
from jsonAI.tool_registry import ToolRegistry
from jsonAI.schema_validator import SchemaValidator

def test_json_schema_validation_ollama():
    # Simple schema for a person
    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"},
            "email": {"type": "string"}
        },
        "required": ["name", "age", "email"]
    }
    prompt = "Generate a person profile as JSON."
    # Use OllamaBackend for integration test
    from jsonAI.model_backends import OllamaBackend
    jf = Jsonformer(
        model_backend=OllamaBackend(model_name="qwen3:0.6b"),
        json_schema=schema,
        prompt=prompt,
        debug=False
    )
    generated = jf.generate_data()
    # Validate output
    validator = SchemaValidator()
    validator.validate(generated, schema)
    assert set(generated.keys()) == {"name", "age", "email"}
    print("Ollama schema validation test passed.")

if __name__ == "__main__":
    test_json_schema_validation_ollama()
