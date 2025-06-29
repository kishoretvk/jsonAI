from jsonAI.main import Jsonformer
from jsonAI.model_backends import OllamaBackend, TransformersBackend
from transformers import AutoModelForCausalLM, AutoTokenizer

def test_ollama_integration():
    # This test requires a running Ollama instance with a model like 'llama2'
    try:
        ollama_backend = OllamaBackend(model_name="llama2")
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

    prompt = "Generate a person's information based on the following schema:"
    jsonformer = Jsonformer(
        model_backend=ollama_backend,
        json_schema=json_schema,
        prompt=prompt
    )
    generated_data = jsonformer()

    print("--- Ollama Integration Test ---")
    print(generated_data)
    print("-----------------------------")

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
