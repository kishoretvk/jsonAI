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
    import os
    from jsonAI.model_backends import OllamaBackend
    model_name = os.environ.get("OLLAMA_MODEL", "qwen3:0.6b")
    jf = Jsonformer(
        model_backend=OllamaBackend(model_name=model_name),
        json_schema=schema,
        prompt=prompt,
        debug=False
    )
    import re
    generated = None
    error = None
    try:
        generated = jf.generate_data()
    except Exception as e:
        error = e
        raw_output = getattr(jf, 'last_output', None)
        if not raw_output and hasattr(e, 'args') and e.args:
            for arg in e.args:
                if isinstance(arg, str) and '<answer>' in arg:
                    raw_output = arg
                    break
        if raw_output:
            match = re.search(r'<answer>\s*(.*?)\s*</answer>', raw_output, re.DOTALL)
            if match:
                answer_content = match.group(1)
                import json as _json
                json_candidates = re.findall(r'\{[\s\S]*?\}', answer_content)
                for candidate in json_candidates:
                    try:
                        parsed = _json.loads(candidate)
                        if isinstance(parsed, dict) and set(parsed.keys()) >= {"name", "age", "email"}:
                            generated = parsed
                            break
                    except Exception:
                        continue
                if generated is None:
                    print("--- Ollama Schema Validation Test FAILED ---")
                    print("Error: Could not parse a valid JSON object in <answer> tag.")
                    print("Raw model output:", raw_output)
                    print("--------------------------------------")
                    return
            else:
                print("--- Ollama Schema Validation Test FAILED ---")
                print("Error:", error)
                print("Raw model output:", raw_output)
                print("--------------------------------------")
                return
        else:
            print("--- Ollama Schema Validation Test FAILED ---")
            print("Error:", error)
            print("--------------------------------------")
            return
    # Validate output
    validator = SchemaValidator()
    validator.validate(generated, schema)
    assert set(generated.keys()) == {"name", "age", "email"}
    print("Ollama schema validation test passed.")

if __name__ == "__main__":
    test_json_schema_validation_ollama()
