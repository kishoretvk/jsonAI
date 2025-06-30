import pytest
from jsonAI.main import Jsonformer
from jsonAI.tool_registry import ToolRegistry

# Dummy tools for chaining
def add(x, y):
    return {"sum": x + y}

def multiply(sum, factor):
    return {"product": sum * factor}

def test_tool_chaining():
    # Register dummy tools
    registry = ToolRegistry()
    registry.register(add)
    registry.register(multiply)

    # Define schema with tool chain
    schema = {
        "type": "object",
        "properties": {
            "x": {"type": "integer"},
            "y": {"type": "integer"},
            "factor": {"type": "integer"}
        },
        "x-jsonai-tool-chain": [
            {
                "name": "add",
                "arguments": {"x": "x", "y": "y"}
            },
            {
                "name": "multiply",
                "arguments": {"sum": "sum", "factor": "factor"}
            }
        ]
    }

    # Provide input data
    prompt = "Calculate (x + y) * factor."
    from jsonAI.model_backends import DummyBackend
    jf = Jsonformer(
        model_backend=DummyBackend(),  # Use DummyBackend for tests
        json_schema=schema,
        prompt=prompt,
        tool_registry=registry,
        debug=False
    )
    # Patch value to simulate generated data
    jf.value = {"x": 2, "y": 3, "factor": 4}
    generated = jf.generate_data()
    result = jf._execute_tool_call(generated)
    assert result["tool_chain_results"][0]["tool_result"] == {"sum": 5}
    assert result["tool_chain_results"][1]["tool_result"] == {"product": 20}
    assert result["final_data"]["product"] == 20
    print("Tool chaining test passed.")

if __name__ == "__main__":
    test_tool_chaining()
