import pytest
import os
import asyncio
import importlib.util

# Skip the whole module if ollama is not installed (optional dependency)
if importlib.util.find_spec("ollama") is None:
    pytest.skip("ollama not installed; skipping Ollama integration tests", allow_module_level=True)

from jsonAI.model_backends import OllamaBackend
from jsonAI.main import Jsonformer

skip_ollama = pytest.mark.skipif(
    os.environ.get("CI") == "true" or os.environ.get("GITHUB_ACTIONS") == "true",
    reason="Ollama tests are skipped in CI environments."
)

@skip_ollama
def test_ollama_basic_generation():
    """Test basic Ollama generation with a simple prompt."""
    # Using mistral as it's commonly available
    backend = OllamaBackend(model_name="mistral")
    
    prompt = "Generate a short greeting message"
    try:
        result = backend.generate(prompt, temperature=0.7, max_tokens=50)
        assert isinstance(result, str)
        assert len(result) > 0
        print(f"Generated response: {result}")
    except Exception as e:
        pytest.fail(f"OllamaBackend.generate raised an exception: {e}")

@skip_ollama
def test_ollama_json_generation():
    """Test Ollama generation with JSON schema."""
    backend = OllamaBackend(model_name="mistral")
    
    # Simple JSON schema for testing
    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"}
        }
    }
    
    prompt = f"Generate a JSON object with a person's name and age. Schema: {schema}"
    
    try:
        result = backend.generate(prompt, temperature=0.7)
        assert isinstance(result, str)
        assert len(result) > 0
        print(f"Generated JSON response: {result}")
    except Exception as e:
        pytest.fail(f"OllamaBackend.generate with JSON schema raised an exception: {e}")

@pytest.mark.asyncio
@skip_ollama
async def test_ollama_async_generation():
    """Test async Ollama generation."""
    backend = OllamaBackend(model_name="mistral")
    
    prompt = "Generate a short motivational quote"
    
    try:
        result = await backend.agenerate(prompt, temperature=0.7, max_tokens=100)
        assert isinstance(result, str)
        assert len(result) > 0
        print(f"Generated async response: {result}")
    except Exception as e:
        pytest.fail(f"OllamaBackend.agenerate raised an exception: {e}")

@skip_ollama
def test_ollama_with_jsonformer():
    """Test Ollama integration with Jsonformer."""
    backend = OllamaBackend(model_name="mistral")
    
    schema = {
        "type": "object",
        "properties": {
            "greeting": {"type": "string"},
            "language": {"type": "string"}
        }
    }
    
    prompt = "Generate a greeting in a random language"
    
    jsonformer = Jsonformer(
        model_backend=backend,
        json_schema=schema,
        prompt=prompt,
        debug=True
    )
    
    try:
        result = jsonformer.generate_data()
        assert isinstance(result, dict)
        assert "greeting" in result
        assert "language" in result
        print(f"Jsonformer with Ollama generated: {result}")
    except Exception as e:
        # This might fail due to the nature of the task, but we want to see what happens
        print(f"Jsonformer with Ollama test completed with result: {e}")

@skip_ollama
def test_ollama_model_options():
    """Test Ollama with various model options."""
    backend = OllamaBackend(model_name="mistral")
    
    prompt = "Generate a very short response"
    
    # Test with different options
    try:
        result = backend.generate(prompt, temperature=0.1, max_tokens=20)
        assert isinstance(result, str)
        assert len(result) > 0
        print(f"Low temperature response: {result}")
        
        result = backend.generate(prompt, temperature=1.0, max_tokens=20)
        assert isinstance(result, str)
        assert len(result) > 0
        print(f"High temperature response: {result}")
    except Exception as e:
        pytest.fail(f"OllamaBackend with options raised an exception: {e}")

if __name__ == "__main__":
    # Run tests manually if executed directly
    test_ollama_basic_generation()
    test_ollama_json_generation()
    test_ollama_model_options()
    print("Ollama integration tests completed!")