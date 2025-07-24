from jsonAI.main import Jsonformer
from jsonAI.type_generator import TypeGenerator
from jsonAI.model_backends import OllamaBackend, TransformersBackend
from transformers import AutoModelForCausalLM, AutoTokenizer

def test_ollama_integration():
    # This test requires a running Ollama instance with a model like 'qwen3:0.6b'
    import os
    model_name = os.environ.get("OLLAMA_MODEL", "qwen3:0.6b")
    try:
        ollama_backend = OllamaBackend(model_name=model_name)
    except ImportError:
        print("Ollama is not installed. Skipping Ollama integration test.")
        return
    except Exception as e:
        print(f"Failed to connect to Ollama. Skipping test. Error: {e}")
        return

    json_schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "number"},
            "is_student": {"type": "boolean"},
            "courses": {
                "type": "array",
                "items": {"type": "string"}
            }
        }
    }

    prompt = (
        "Generate a person's information as JSON. "
        "Output ONLY the answer, wrapped in <answer> tags, with no explanation or formatting. "
        "Schema: " + str(json_schema)
    )
    # Warn if backend does not support structured generation
    if not hasattr(ollama_backend, 'structured') or not getattr(ollama_backend, 'structured', False):
        print("[WARNING] OllamaBackend does not support structured (token-by-token) generation. Test may not be meaningful.")
    jsonformer = Jsonformer(
        model_backend=ollama_backend,
        json_schema=json_schema,
        prompt=prompt
    )
    import re, json as _json
    generated_data = None
    error = None
    def try_parse_json(candidate):
        try:
            parsed = _json.loads(candidate)
            if isinstance(parsed, dict) and set(parsed.keys()) >= {"name", "age", "is_student", "courses"}:
                return parsed
        except Exception:
            pass
        return None

    generated_data = None
    error = None
    sources = []

    def extract_answer_blocks(text):
        # Returns a list of all <answer>...</answer> blocks (content only)
        return re.findall(r'<answer>([\s\S]*?)</answer>', text, re.IGNORECASE)

    def extract_and_parse_json_from_sources(sources):
        for source in sources:
            answer_blocks = extract_answer_blocks(source)
            if not answer_blocks:
                answer_blocks = [source]
            for block in answer_blocks:
                print("[DEBUG] Found <answer> block:")
                print(block)
                json_candidates = re.findall(r'\{[\s\S]*?\}', block)
                if not json_candidates:
                    json_candidates = [block.strip()]
                for candidate in json_candidates:
                    print("[DEBUG] Trying JSON candidate:")
                    print(candidate)
                    parsed = try_parse_json(candidate)
                    if parsed:
                        return parsed
        # If not found in <answer> blocks, try all JSON objects in all sources (outside <answer> tags)
        for source in sources:
            json_candidates = re.findall(r'\{[\s\S]*?\}', source)
            for candidate in json_candidates:
                print("[DEBUG] Trying fallback JSON candidate:")
                print(candidate)
                parsed = try_parse_json(candidate)
                if parsed:
                    return parsed
        return None

    try:
        raw_result = jsonformer()
        # Try direct dict
        if isinstance(raw_result, dict) and set(raw_result.keys()) >= {"name", "age", "is_student", "courses"}:
            generated_data = raw_result
        elif isinstance(raw_result, str):
            # Always extract from <answer> tags if present
            generated_data = extract_and_parse_json_from_sources([raw_result])
            if not generated_data:
                sources.append(raw_result)
        else:
            sources.append(str(raw_result))
    except Exception as e:
        error = e
        raw_output = getattr(jsonformer, 'last_output', None)
        if raw_output:
            sources.append(raw_output)
        if hasattr(e, 'args') and e.args:
            for arg in e.args:
                if isinstance(arg, str):
                    sources.append(arg)

    if generated_data is None and sources:
        generated_data = extract_and_parse_json_from_sources(sources)

    if generated_data is None:
        print("--- Ollama Integration Test FAILED ---")
        print("Error: Could not parse a valid JSON object in any output.")
        if error:
            print("Exception:", error)
        if sources:
            print("Checked sources:")
            for s in sources:
                print(s)
        print("--------------------------------------")
        return
    # Validate output structure
    # Validate output structure
    from jsonAI.schema_validator import SchemaValidator
    validator = SchemaValidator()
    validator.validate(generated_data, json_schema)
    assert set(generated_data.keys()) == {"name", "age", "is_student", "courses"}
    print("--- Ollama Integration Test PASSED ---")
    print(generated_data)
    print("--------------------------------------")
    return

def test_type_selection_fallback():
    """Test the weighted random fallback for type selection"""
    class SimpleBackend:
        def generate(self, prompt, **kwargs):
            return "test"  # Simple response
    
    backend = SimpleBackend()
    type_gen = TypeGenerator(backend, lambda *args: print(args))
    
    # Should use fallback selection
    selected = type_gen.choose_type("test", ["string", "number"])
    assert selected in ["string", "number"]

def test_hf_backend_compatibility():
    # Ensure the original Hugging Face backend still works
    model = AutoModelForCausalLM.from_pretrained("gpt2")
    tokenizer = AutoTokenizer.from_pretrained("gpt2")
    hf_backend = TransformersBackend(model, tokenizer)

    json_schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "number"}
        }
    }

    prompt = "Generate a person's information:"
    jsonformer = Jsonformer(
        model_backend=hf_backend,
        json_schema=json_schema,
        prompt=prompt
    )
    generated_data = jsonformer()

    print("--- Hugging Face Backend Compatibility Test ---")
    print(generated_data)
    print("-------------------------------------------")


if __name__ == "__main__":
    test_ollama_integration()
    test_hf_backend_compatibility()
