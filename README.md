# jsonAI

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Architecture Overview](#architecture-overview)
- [Testing](#testing)
- [Examples](#examples)
  - [Basic JSON Generation](#basic-json-generation)
  - [XML Output](#xml-output)
  - [YAML Output](#yaml-output)
  - [CSV Output](#csv-output)
  - [CLI Example](#cli-example)
  - [Tool Calling Example](#tool-calling-example)
  - [MCP Integration Example](#mcp-integration-example)
  - [Complex Schema Example](#complex-schema-example)
- [Output Format × Type Coverage](#output-format--type-coverage)
- [Integrations & Capabilities](#integrations--capabilities)
- [License](#license)

jsonAI is a Python library for generating structured data based on JSON schemas using pre-trained language models. It supports a wide range of data types and output formats, making it ideal for applications requiring dynamic data generation.

## Features

-   **Dynamic JSON Generation**: Generate JSON objects based on schemas with support for complex types.
-   **Output Formats**: Supports JSON, XML, YAML, and CSV.
-   **Validation**: Validate generated data against schemas.
-   **Tool Integration**: Execute tools based on generated data.
-   **Async Support**: Asynchronous generation and tool execution.

## Installation

```bash
pip install jsonAI
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

```bash
jsonai generate --schema schema.json --prompt "Generate a product" --output-format json
```

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
