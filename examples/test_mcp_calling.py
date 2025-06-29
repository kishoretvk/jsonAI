import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from jsonAI.main import Jsonformer
from jsonAI.tool_registry import ToolRegistry

# MCP callback function
def mcp_callback(tool_name: str, server_name: str, arguments: dict) -> str:
    """Simulates MCP tool execution"""
    if tool_name == "get_stock_price":
        return f"Stock price for {arguments['symbol']} is $150.75"
    elif tool_name == "get_news":
        return f"Latest news about {arguments['topic']}: Major breakthrough announced!"
    return f"MCP tool {tool_name} on server {server_name} executed with args: {arguments}"

def test_mcp_calling():
    # Initialize model and tokenizer
    model_name = "gpt2"
    model = AutoModelForCausalLM.from_pretrained(model_name)
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    
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
        model=model,
        tokenizer=tokenizer,
        json_schema=stock_schema,
        prompt=prompt,
        tool_registry=registry,
        mcp_callback=mcp_callback
    )
    
    result = jsonformer()
    print("Test Case 1 - Stock Price Lookup:")
    print(result)
    
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
        model=model,
        tokenizer=tokenizer,
        json_schema=news_schema,
        prompt=prompt,
        tool_registry=registry,
        mcp_callback=mcp_callback
    )
    
    result = jsonformer()
    print("\nTest Case 2 - News Lookup:")
    print(result)

if __name__ == "__main__":
    test_mcp_calling()
