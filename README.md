# jsonAI

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

## License

This project is licensed under the MIT License.
