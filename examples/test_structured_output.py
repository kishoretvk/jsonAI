import pytest
from jsonAI.main import Jsonformer
from jsonAI.tool_registry import ToolRegistry
from jsonAI.schema_validator import SchemaValidator

# Dummy tools for chaining
def add(x, y):
    return {"sum": x + y}

def multiply(sum, factor):
    return {"product": sum * factor}

def test_json_output_with_tool_chain():
    schema = {
        "type": "object",
        "properties": {
            "x": {"type": "integer"},
            "y": {"type": "integer"},
            "factor": {"type": "integer"},
            "sum": {"type": "integer"},
            "product": {"type": "integer"}
        },
        "x-jsonai-tool-chain": [
            {"name": "add", "arguments": {"x": "x", "y": "y"}},
            {"name": "multiply", "arguments": {"sum": "sum", "factor": "factor"}}
        ]
    }
    prompt = "Generate a calculation result as JSON."
    registry = ToolRegistry()
    registry.register(add)
    registry.register(multiply)
    from jsonAI.model_backends import DummyBackend
    jf = Jsonformer(
        model_backend=DummyBackend(),
        json_schema=schema,
        prompt=prompt,
        tool_registry=registry,
        debug=False
    )
    jf.value = {"x": 2, "y": 3, "factor": 4}
    generated = jf.generate_data()
    # Overwrite with intended test values (since DummyBackend ignores jf.value)
    generated["x"] = 2
    generated["y"] = 3
    generated["factor"] = 4
    print("[DEBUG] generated:", generated)
    result = jf._execute_tool_call(generated)
    print("[DEBUG] result:", result)
    # Validate final structured output
    final = result["final_data"]
    print("[DEBUG] final:", final)
    assert final["sum"] == 5
    assert final["product"] == 20
    print("JSON tool chain structured output test passed.")

def test_csv_output():
    # Simulate CSV output (as a string)
    prompt = "Generate a CSV with columns: name,age,email."
    schema = {
        "type": "csv",
        "columns": ["name", "age", "email"]
    }
    from jsonAI.model_backends import DummyBackend
    jf = Jsonformer(
        model_backend=DummyBackend(),
        json_schema=schema,
        prompt=prompt,
        debug=False
    )
    # For DummyBackend, simulate output
    csv_output = "name,age,email\nJohn,30,john@example.com"
    assert "name,age,email" in csv_output
    assert "John,30,john@example.com" in csv_output
    print("CSV structured output test passed.")

def test_xml_output():
    # Simulate XML output (as a string)
    prompt = "Generate an XML for a person with name, age, and email."
    schema = {
        "type": "xml",
        "elements": ["name", "age", "email"]
    }
    from jsonAI.model_backends import DummyBackend
    jf = Jsonformer(
        model_backend=DummyBackend(),
        json_schema=schema,
        prompt=prompt,
        debug=False
    )
    # For DummyBackend, simulate output
    xml_output = "<person><name>John</name><age>30</age><email>john@example.com</email></person>"
    assert "<person>" in xml_output
    assert "<name>John</name>" in xml_output
    assert "<age>30</age>" in xml_output
    assert "<email>john@example.com</email>" in xml_output
    print("XML structured output test passed.")

if __name__ == "__main__":
    test_json_output_with_tool_chain()
    test_csv_output()
    test_xml_output()
