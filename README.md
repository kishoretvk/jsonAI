# JsonAI - Production-Ready Structured JSON Generation with LLMs

JsonAI is a comprehensive Python library for generating structured JSON data using Large Language Models (LLMs). It provides enterprise-grade features including robust JSON schema validation, multiple model backends, REST API, React frontend, CLI interface, and production deployment configurations.

## 🚀 Features

### Core Capabilities
- **Multiple LLM Backends**: Support for Ollama, OpenAI, and HuggingFace models
- **Complete JSON Schema Support**: All JSON schema types including primitives, arrays, objects, enums, and complex nested structures
- **Performance Optimization**: Advanced caching, batch processing, and async operations
- **Production Ready**: Docker deployment, Kubernetes configs, monitoring, and scaling

### Interfaces & APIs
- **REST API**: FastAPI-based service with OpenAPI documentation
- **React Frontend**: Modern web interface for JSON generation
- **CLI Interface**: Powerful command-line tools for automation and batch processing
- **Python Library**: Direct programmatic access with async support

### Enterprise Features
- **Caching System**: Intelligent multi-level caching with TTL and LRU strategies
- **Batch Processing**: Concurrent processing of multiple requests
- **Performance Monitoring**: Built-in metrics and performance tracking
- **Schema Validation**: Comprehensive validation with custom rules support
- **Multiple Output Formats**: JSON, YAML, XML, and CSV support

## 📦 Installation

### Option 1: pip (Recommended)
```bash
pip install jsonai
```

### Option 2: From Source
```bash
git clone https://github.com/yourusername/JsonAI.git
cd JsonAI
poetry install
```

### Option 3: Docker
```bash
# Quick start with Docker
docker run -p 8000:8000 jsonai:latest

# Full stack with Docker Compose
docker-compose up -d
```

## Architecture Overview

The `jsonAI` library is modular and consists of the following components:

-   **`Jsonformer`**: Orchestrates the generation process, handles output formatting, and validates data.
-   **`TypeGenerator`**: Generates values for individual data types.
-   **`OutputFormatter`**: Converts generated data into the desired format.
-   **`SchemaValidator`**: Validates data against JSON schemas.
-   **`ToolRegistry`**: Manages tools for execution.
-   **`AsyncJsonformer`**: Provides asynchronous support for generation and tool execution.

## Testing

The project includes comprehensive tests for each component and integration:

-   **Unit Tests**: Test individual components.
-   **Integration Tests**: Validate the interaction between components.

To run tests:

```bash
pytest tests/
```

## Examples

### Basic JSON Generation

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
from jsonAI.main import Jsonformer

model = AutoModelForCausalLM.from_pretrained("gpt2")
tokenizer = AutoTokenizer.from_pretrained("gpt2")

schema = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "age": {"type": "integer"},
        "isStudent": {"type": "boolean"}
    }
}

prompt = "Generate a person's profile."
jsonformer = Jsonformer(model, tokenizer, schema, prompt)
output = jsonformer()
print(output)
```


### XML Output
### YAML Output

```python
schema = {
    "type": "object",
    "properties": {
        "city": {"type": "string"},
        "population": {"type": "integer"}
    }
}
prompt = "Generate a city profile."
jsonformer = Jsonformer(model, tokenizer, schema, prompt, output_format="yaml")
output = jsonformer()
print(output)
```

### CSV Output

```python
schema = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "score": {"type": "number"}
        }
    }
}
prompt = "Generate a list of students and their scores."
jsonformer = Jsonformer(model, tokenizer, schema, prompt, output_format="csv")
output = jsonformer()
print(output)
```


### CLI Example

#### Basic CLI Usage

```bash
python -m jsonAI.cli generate --schema schema.json --prompt "Generate a product" --output-format json
```

#### Using Ollama Backend (Recommended for LLMs)

```bash
python -m jsonAI.cli generate --schema complex_schema.json --prompt "Generate a comprehensive person profile as JSON." --use-ollama --ollama-model qwen3:1.7b
```

#### Features
- Robustly extracts the first valid JSON object from any LLM output (even if wrapped in <answer> tags or surrounded by extra text)
- Supports all JSON schema types: primitives, enums, arrays, objects, null, oneOf, nested/complex
- Validates output against the schema and warns if invalid
- Pretty-prints objects/arrays, prints primitives/null as-is
- Production-ready for any schema and LLM output style

#### Example Output

```json
{
  "id": "profile with all supported JSON schema types.",
  "name": "re",
  "age": 30,
  "is_active": true,
  "email": "example@example.com",
  "roles": ["admin", "user"],
  "address": {"street": "123 Main St", "city": "Anytown", "zip": "12345", "country": "USA"},
  "preferences": {"newsletter": true, "theme": "dark", "language": "en"},
  "tags": ["tech", "developer"],
  "score": 95,
  "metadata": {"key1": "value1", "key2": "value2"},
  "status": "active",
  "history": [{"date": "2023-01-01", "event": "joined", "details": "Account created"}],
  "profile_picture": "https://example.com/avatar.jpg",
  "settings": {"notifications": true, "privacy": "private"},
  "null_field": null
}
```

See `complex_schema.json` for a comprehensive schema example.

### Tool Calling Example

```python
def send_email(email):
    print(f"Sending email to {email}")
    return "Email sent"

tool_registry = ToolRegistry()
tool_registry.register_tool("send_email", send_email)

schema = {
    "type": "object",
    "properties": {
        "email": {"type": "string", "format": "email"}
    },
    "x-jsonai-tool-call": {
        "name": "send_email",
        "arguments": {"email": "email"}
    }
}
prompt = "Generate a user email."
jsonformer = Jsonformer(model, tokenizer, schema, prompt, tool_registry=tool_registry)
output = jsonformer()
print(output)
```

### MCP Integration Example

```python
def mcp_callback(tool_name, server_name, kwargs):
    # Simulate MCP call
    return f"Called {tool_name} on {server_name} with {kwargs}"

schema = {
    "type": "object",
    "properties": {
        "query": {"type": "string"}
    },
    "x-jsonai-tool-call": {
        "name": "search_tool",
        "arguments": {"query": "query"}
    }
}
jsonformer = Jsonformer(model, tokenizer, schema, prompt, mcp_callback=mcp_callback)
output = jsonformer()
print(output)
```

### Complex Schema Example

```python
schema = {
    "type": "object",
    "properties": {
        "user": {
            "type": "object",
            "properties": {
                "id": {"type": "uuid"},
                "name": {"type": "string"},
                "email": {"type": "string", "format": "email"}
            }
        },
        "roles": {
            "type": "array",
            "items": {"type": "string", "enum": ["admin", "user", "guest"]}
        },
        "profile": {
            "oneOf": [
                {"type": "object", "properties": {"age": {"type": "integer"}}},
                {"type": "object", "properties": {"birthdate": {"type": "date"}}}
            ]
        }
    },
    "x-jsonai-tool-call": {
        "name": "send_welcome_email",
        "arguments": {"email": "user.email"}
    }
}
# ...setup model, tokenizer, tool_registry, etc...
jsonformer = Jsonformer(model, tokenizer, schema, prompt, tool_registry=tool_registry)
output = jsonformer()
print(output)
```

```python
schema = {
    "type": "object",
    "properties": {
        "book": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "author": {"type": "string"},
                "year": {"type": "integer"}
            }
        }
    }
}

prompt = "Generate details for a book."
jsonformer = Jsonformer(model, tokenizer, schema, prompt, output_format="xml")
output = jsonformer()
print(output)
```

### Tool Chaining Example

You can chain multiple tools together using the `x-jsonai-tool-chain` schema key. Each tool in the chain receives arguments from the generated data and/or previous tool outputs.

```python
from jsonAI.main import Jsonformer
from jsonAI.tool_registry import ToolRegistry

def add(x, y):
    return {"sum": x + y}

def multiply(sum, factor):
    return {"product": sum * factor}

registry = ToolRegistry()
registry.register_tool("add", add)
registry.register_tool("multiply", multiply)

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

prompt = "Calculate (x + y) * factor."
jsonformer = Jsonformer(
    model_backend=None,  # Not used in this example
    json_schema=schema,
    prompt=prompt,
    tool_registry=registry
)
# Provide input data (simulate generated data)
jsonformer.value = {"x": 2, "y": 3, "factor": 4}
generated = jsonformer.generate_data()
result = jsonformer._execute_tool_call(generated)
print(result)
# Output will include all intermediate and final tool results.
```

## Output Format × Type Coverage


| Type      | Example         | JSON | XML  | YAML | CSV* |
|-----------|----------------|------|------|------|------|
| number    | 3.14           | ✅   | ✅   | ✅   | ✅   |
| integer   | 42             | ✅   | ✅   | ✅   | ✅   |
| boolean   | true           | ✅   | ✅   | ✅   | ✅   |
| string    | "hello"        | ✅   | ✅   | ✅   | ✅   |
| datetime  | "2023-06-29T12:00:00Z" | ✅   | ✅   | ✅   | ✅   |
| date      | "2023-06-29"   | ✅   | ✅   | ✅   | ✅   |
| time      | "12:00:00"     | ✅   | ✅   | ✅   | ✅   |
| uuid      | "123e4567-e89b-12d3-a456-426614174000" | ✅   | ✅   | ✅   | ✅   |
| binary    | "SGVsbG8="     | ✅   | ✅   | ✅   | ✅   |
| null      | null           | ✅   | (⚠️) | ✅   | (⚠️) |
| array     | [1,2,3]        | ✅   | ✅   | ✅   | (⚠️) |
| object    | {"a":1}        | ✅   | ✅   | ✅   | (⚠️) |
| enum      | "red"          | ✅   | ✅   | ✅   | ✅   |
| p_enum    | "blue"         | ✅   | ✅   | ✅   | ✅   |
| p_integer | 7              | ✅   | ✅   | ✅   | ✅   |

✅ = Supported
⚠️ = Supported with caveats (e.g., nulls in XML/CSV, arrays/objects in CSV)
*CSV: Only arrays of objects (tabular) are practical


## Integrations & Capabilities

- **LLM Integration**: Use with HuggingFace Transformers, OpenAI, vLLM, Ollama, etc.
- **FastAPI**: Serve generation endpoints via FastAPI (see `examples/fastapi_example.py`).
- **Tool Registry**: Register and call Python or MCP tools from schemas.
- **Async Support**: Use `AsyncJsonformer` for async workflows.

See the [examples/](examples/) directory for more advanced usage and integration patterns.

## License

This project is licensed under the MIT License.

## Streaming Support

jsonAI now supports streaming data generation for real-time applications. Use the `stream_generate_data` method in `Jsonformer` or `AsyncJsonformer` to generate data incrementally.

### Example

```python
# Streaming with Jsonformer
jsonformer = Jsonformer(model_backend, json_schema, prompt)
for data_chunk in jsonformer.stream_generate_data():
    print(data_chunk)

# Streaming with AsyncJsonformer
async def async_stream():
    async_jsonformer = AsyncJsonformer(jsonformer)
    async for data_chunk in async_jsonformer.stream_generate_data():
        print(data_chunk)

asyncio.run(async_stream())
```
