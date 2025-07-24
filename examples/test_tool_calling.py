import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from jsonAI.main import Jsonformer
from jsonAI.tool_registry import ToolRegistry

# Define a simple function to act as a tool
def get_current_weather(city: str, temp_unit: str = "celsius"):
    """A dummy function to get weather."""
    if city.lower() == "tokyo":
        return f"The weather in {city} is 25° {temp_unit} and sunny."
    else:
        return f"Weather for {city} is not available."

def test_tool_calling():
    # Initialize model and tokenizer
    model_name = "gpt2"
    model = AutoModelForCausalLM.from_pretrained(model_name)
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    
    # Create and populate the ToolRegistry
    registry = ToolRegistry()
    registry.register(get_current_weather)

    # Define the schema with the tool call directive
    weather_schema = {
        "type": "object",
        "properties": {
            "location": {"type": "string", "description": "The city name."},
            "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]}
        },
        "required": ["location", "unit"],
        "x-jsonai-tool-call": {
            "name": "get_current_weather",
            "arguments": {
                "city": "location",
                "temp_unit": "unit"
            }
        }
    }

    # Test case 1: Valid city
    prompt = "What is the weather like in Tokyo?"
    from jsonAI.model_backends import TransformersBackend
    backend = TransformersBackend(model, tokenizer)
    jsonformer = Jsonformer(
        model_backend=backend,
        json_schema=weather_schema,
        prompt=prompt,
        tool_registry=registry
    )
    
    result = jsonformer()
    print("Test Case 1 - Valid City:")
    print(result)
    
    # Test case 2: Invalid city
    prompt = "What is the weather like in Mars?"
    jsonformer = Jsonformer(
        model_backend=backend,
        json_schema=weather_schema,
        prompt=prompt,
        tool_registry=registry
    )
    
    result = jsonformer()
    print("\nTest Case 2 - Invalid City:")
    print(result)
    
    # Test case 3: No tool registry (should return just generated data)
    prompt = "What is the weather like in Tokyo?"
    jsonformer = Jsonformer(
        model_backend=backend,
        json_schema=weather_schema,
        prompt=prompt
    )
    
    result = jsonformer()
    print("\nTest Case 3 - No Tool Registry:")
    print(result)

if __name__ == "__main__":
    test_tool_calling()
