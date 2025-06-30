import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from jsonAI.main import Jsonformer
from jsonAI.tool_registry import ToolRegistry
from jsonAI.model_backends import TransformersBackend
import json

def mock_get_tool(tool_name):
    print(f"Mock get_tool called with tool_name: {tool_name}")
    return lambda **kwargs: {"mock_result": "success"}

def mock_mcp_callback(tool_name, server_name, kwargs):
    print(f"Mock mcp_callback called with tool_name: {tool_name}, server_name: {server_name}, kwargs: {kwargs}")
    return {"mock_result": "success"}

# MCP callback function
def mcp_callback(tool_name: str, server_name: str, arguments: dict) -> str:
    """Simulates MCP tool execution"""
    if tool_name == "get_stock_price":
        return f"Stock price for {arguments['symbol']} is $150.75"
    elif tool_name == "get_news":
        return f"Latest news about {arguments['topic']}: Major breakthrough announced!"
    return f"MCP tool {tool_name} on server {server_name} executed with args: {arguments}"

# Dummy backend for mock tests
class DummyBackend:
    def generate(self, prompt, **kwargs):
        return "mocked string"

# Add debugging logs to trace the flow of data and marker handling
def test_mcp_calling():
    # Initialize model backend
    model_name = "gpt2"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(model_name)
    model_backend = TransformersBackend(model, tokenizer)

    # Create and populate the ToolRegistry with MCP tools
    registry = ToolRegistry()
    registry.register({
        "name": "get_stock_price",
        "server_name": "financial-server",
        "config": {"description": "Gets current stock price"}
    })
    registry.register({
        "name": "get_news",
        "server_name": "news-server",
        "config": {"description": "Gets latest news"}
    })

    # Define the schema with MCP tool call
    stock_schema = {
        "type": "object",
        "properties": {
            "symbol": {"type": "string"},
            "timeframe": {"type": "string", "enum": ["daily", "weekly"]}
        },
        "required": ["symbol"],
        "x-jsonai-tool-call": {
            "name": "get_stock_price",
            "arguments": {
                "symbol": "symbol",
                "timeframe": "timeframe"
            }
        }
    }

    # Test case 1: Stock price lookup
    prompt = "Get the current stock price for AAPL"
    jsonformer = Jsonformer(
        model_backend=model_backend,
        json_schema=stock_schema,
        prompt=prompt,
        tool_registry=registry,
        mcp_callback=mcp_callback,
        debug=True  # Enable debugging
    )

    # Add logs to trace the state of tool_registry.get_tool and mcp_callback
    print("Initial state of tool_registry.get_tool:", registry.get_tool)
    print("Initial state of mcp_callback:", mcp_callback)

    # Before running Jsonformer
    print("Before Jsonformer execution - tool_registry.get_tool callable:", callable(registry.get_tool))
    print("Before Jsonformer execution - mcp_callback callable:", callable(mcp_callback))

    try:
        result = jsonformer()
        print("Test Case 1 - Stock Price Lookup:")
        print(result)
    except Exception as e:
        print("Error in Test Case 1:", str(e))

    # After running Jsonformer
    print("After Jsonformer execution - tool_registry.get_tool callable:", callable(registry.get_tool))
    print("After Jsonformer execution - mcp_callback callable:", callable(mcp_callback))

    # Test case 2: News lookup
    news_schema = {
        "type": "object",
        "properties": {
            "topic": {"type": "string"},
            "category": {"type": "string", "enum": ["tech", "politics"]}
        },
        "required": ["topic"],
        "x-jsonai-tool-call": {
            "name": "get_news",
            "arguments": {
                "topic": "topic",
                "category": "category"
            }
        }
    }

    prompt = "Get news about artificial intelligence"
    jsonformer = Jsonformer(
        model_backend=model_backend,
        json_schema=news_schema,
        prompt=prompt,
        tool_registry=registry,
        mcp_callback=mcp_callback,
        debug=True  # Enable debugging
    )

    # Add logs to trace the state of tool_registry.get_tool and mcp_callback
    print("Initial state of tool_registry.get_tool:", registry.get_tool)
    print("Initial state of mcp_callback:", mcp_callback)

    # Before running Jsonformer
    print("Before Jsonformer execution - tool_registry.get_tool callable:", callable(registry.get_tool))
    print("Before Jsonformer execution - mcp_callback callable:", callable(mcp_callback))

    try:
        result = jsonformer()
        print("\nTest Case 2 - News Lookup:")
        print(result)
    except Exception as e:
        print("Error in Test Case 2:", str(e))

    # After running Jsonformer
    print("After Jsonformer execution - tool_registry.get_tool callable:", callable(registry.get_tool))
    print("After Jsonformer execution - mcp_callback callable:", callable(mcp_callback))

    # Mock ToolRegistry and MCP callback
    mock_tool_registry = ToolRegistry()
    mock_tool_registry.get_tool = mock_get_tool

    # Example JSON schema with tool call
    json_schema = {
        "properties": {
            "symbol": {"type": "string"},
            "topic": {"type": "string"}
        },
        "x-jsonai-tool-call": {
            "name": "mock_tool",
            "arguments": {
                "arg1": "symbol",
                "arg2": "topic"
            }
        }
    }

    # Initialize Jsonformer with mock components
    jsonformer = Jsonformer(
        model_backend=DummyBackend(),  # Use dummy backend for mock
        json_schema=json_schema,
        prompt="Generate data",
        tool_registry=mock_tool_registry,
        mcp_callback=mock_mcp_callback,
        debug=True
    )

    # Add logs to trace the state of mock_tool_registry.get_tool and mock_mcp_callback
    print("Initial state of mock_tool_registry.get_tool:", mock_tool_registry.get_tool)
    print("Initial state of mock_mcp_callback:", mock_mcp_callback)

    # Before mock Jsonformer execution
    print("Before mock Jsonformer execution - mock_tool_registry.get_tool callable:", callable(mock_tool_registry.get_tool))
    print("Before mock Jsonformer execution - mock_mcp_callback callable:", callable(mock_mcp_callback))

    # Run Jsonformer and print output
    try:
        output = jsonformer()
        print("Output:", output)
    except Exception as e:
        print("Error:", e)

    # After mock Jsonformer execution
    print("After mock Jsonformer execution - mock_tool_registry.get_tool callable:", callable(mock_tool_registry.get_tool))
    print("After mock Jsonformer execution - mock_mcp_callback callable:", callable(mock_mcp_callback))

if __name__ == "__main__":
    test_mcp_calling()
