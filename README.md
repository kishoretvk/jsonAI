# jsonAI 

jsonAI is a Python library for generating JSON objects based on a given schema using a pre-trained language model. It supports a wide range of data types, including numbers, integers, booleans, strings, datetime, date, time, UUID, and binary data.

The idea to create json structures with strong typed schemas is now possible, with any number of variable combinations.

## Installation

```bash
pip install jsonAI
```

## Architecture Overview

The `jsonAI` library is structured into several key components to provide robust and flexible structured data generation:

-   **`Jsonformer` (in `jsonAI/main.py`)**: The main facade class that orchestrates the generation process. It takes the model, tokenizer, schema, and prompt, and coordinates the use of other components to produce the final output. It also handles output formatting and validation.
-   **`TypeGenerator` (in `jsonAI/type_generator.py`)**: Responsible for generating values for individual data types based on the schema and the current generation context (prompt).
-   **`OutputFormatter` (in `jsonAI/output_formatter.py`)**: Handles the conversion of the generated data structure (internal dictionary representation) into the desired output format (JSON, XML, YAML).
-   **`SchemaValidator` (in `jsonAI/schema_validator.py`)**: Provides functionality to validate the generated data structure against the provided JSON schema using the `jsonschema` library.

This modular architecture improves separation of concerns and makes the library more maintainable and extensible.

This currently supports a subset of JSON Schema. Below is a list of the supported schema types:

- number
- integer
- boolean
- string  (descriptions also enabled to satisfy summary)
- datetime
- date
- time
- UUID
- binary data
### combinations
- arrays
- enums
- complex object

## Supported Output Formats

In addition to JSON, `jsonAI` supports generating output in XML, YAML, and CSV formats. You can specify the desired format using the `output_format` parameter in the `Jsonformer` constructor.

**XML Output Example:**

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
from jsonAI.main import Jsonformer

model = AutoModelForCausalLM.from_pretrained("gpt2")
tokenizer = AutoTokenizer.from_pretrained("gpt2")

json_schema = {
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

prompt = "Generate information about a book."

jsonformer = Jsonformer(
    model=model,
    tokenizer=tokenizer,
    json_schema=json_schema,
    prompt=prompt,
    output_format="xml"
)

    generated_data = jsonformer()
    print(generated_data)
```

**CSV Output Example:**

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
from jsonAI.main import Jsonformer

model = AutoModelForCausalLM.from_pretrained("gpt2")
tokenizer = AutoTokenizer.from_pretrained("gpt2")

json_schema = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"},
            "score": {"type": "number"}
        }
    }
}

prompt = "Generate data for three students with names, ages, and test scores."

jsonformer = Jsonformer(
    model=model,
    tokenizer=tokenizer,
    json_schema=json_schema,
    prompt=prompt,
    output_format="csv"
)

generated_data = jsonformer()
print(generated_data)
```

**YAML Output Example:**

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
from jsonAI.main import Jsonformer

model = AutoModelForCausalLM.from_pretrained("gpt2")
tokenizer = AutoTokenizer.from_pretrained("gpt2")

json_schema = {
    "type": "object",
    "properties": {
        "person": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"},
                "isStudent": {"type": "boolean"}
            }
        }
    }
}

prompt = "Generate information about a person."

jsonformer = Jsonformer(
    model=model,
    tokenizer=tokenizer,
    json_schema=json_schema,
    prompt=prompt,
    output_format="yaml"
)

generated_data = jsonformer()
print(generated_data)
```

## Output Validation

You can enable schema validation for the generated output by setting the `validate_output` parameter to `True`. This requires the `jsonschema` library to be installed (`pip install jsonschema`).

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
from jsonAI.main import Jsonformer

model = AutoModelForCausalLM.from_pretrained("gpt2")
tokenizer = AutoTokenizer.from_pretrained("gpt2")

json_schema = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "age": {"type": "integer", "minimum": 0}
    },
    "required": ["name", "age"]
}

prompt = "Generate a person's information."

# This will raise a jsonschema.exceptions.ValidationError if the output doesn't match the schema
jsonformer = Jsonformer(
    model=model,
    tokenizer=tokenizer,
    json_schema=json_schema,
    prompt=prompt,
    validate_output=True
)

generated_data = jsonformer()
print(generated_data)
```

## Examples

We have included examples to demonstrate how to integrate `jsonAI` with other libraries and frameworks. You can find them in the `examples/` directory.

### FastAPI Integration Example

This example shows how to use `jsonAI` within a FastAPI web application to create an API endpoint that generates structured data based on user input.

To run the FastAPI example:

1.  Install necessary dependencies:
    ```bash
    pip install fastapi uvicorn transformers torch jsonschema PyYAML
    ```
2.  Navigate to the `examples/` directory.
3.  Run the server:
    ```bash
    uvicorn fastapi_example:app --reload
    ```
4.  Send a POST request to `http://127.0.0.1:8000/generate/` with a JSON body containing `prompt` and optionally `json_schema`, `output_format`, and `validate_output`. See the comments in `examples/fastapi_example.py` for more details.

## Basic Usage

### TypeGenerator Examples
```python
from jsonAI.type_generator import TypeGenerator
from jsonAI.model_backends import TransformersBackend
from transformers import AutoModelForCausalLM, AutoTokenizer

# With tokenizer backend
model = AutoModelForCausalLM.from_pretrained("gpt2")
tokenizer = AutoTokenizer.from_pretrained("gpt2")
backend = TransformersBackend(model, tokenizer)

# Initialize TypeGenerator
type_gen = TypeGenerator(
    backend,
    debug=print,  # Simple debug function
    max_number_tokens=6,
    max_string_token_length=50
)

# Generate values
number = type_gen.generate_number("Generate a number:")
string = type_gen.generate_string("Generate a name:")
boolean = type_gen.generate_boolean("Is this true?")

# With simple backend (no tokenizer)
class SimpleBackend:
    def generate(self, prompt, **kwargs):
        return "42"  # Simple response

simple_type_gen = TypeGenerator(SimpleBackend(), debug=print)
number = simple_type_gen.generate_number("Generate a number:")  # Will use simple backend
```

## Examples

``` python 
# Define the JSON schema
json_schema = {
    "type": "object",
    "properties": {
        "transaction_id": {"type": "uuid"},
        "store": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "location": {"type": "string"},
                "datetime": {"type": "datetime"}
            }
        },
        "customer": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "uuid"},
                "name": {"type": "string"},
                "membership": {"type": "boolean"}
            }
        },
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "item_id": {"type": "uuid"},
                    "name": {"type": "string"},
                    "category": {"type": "string"},
                    "price": {"type": "number"},
                    "quantity": {"type": "integer"}
                }
            }
        },
        "total_amount": {"type": "number"},
        "payment_method": {"type": "string"},
        "transaction_date": {"type": "date"},
        "transaction_time": {"type": "time"},
        "receipt_binary": {"type": "binary"}
    }
}

# Define the prompt
prompt = "Generate a JSON object representing a transaction at a Starbucks coffee shop. The transaction includes details such as transaction ID, store information, customer information, items purchased, total amount, payment method, transaction date and time, and a binary receipt."

# Initialize Jsonformer
jsonformer = Jsonformer(
    model=model,
    tokenizer=tokenizer,
    json_schema=json_schema,
    prompt=prompt,
    debug=True,
    output_format="json", # Specify output format (e.g., "json", "xml", "yaml")
    validate_output=False # Enable/disable validation (requires jsonschema)
)

# Generate the data
generated_data = jsonformer()
print(generated_data)
# The highlight_values utility might be useful for debugging JSON output
# from jsonAI.format import highlight_values
# highlight_values(generated_data)

```

## Example with various types

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
from jsonAI.main import Jsonformer

model = AutoModelForCausalLM.from_pretrained("gpt2")
tokenizer = AutoTokenizer.from_pretrained("gpt2")
json_schema = {
    "type": "object",
    "properties": {
        "number": {"type": "number"},
        "integer": {"type": "integer"},
        "boolean": {"type": "boolean"},
        "string": {"type": "string"},
        "datetime": {"type": "datetime"},
        "date": {"type": "date"},
        "time": {"type": "time"},
        "uuid": {"type": "uuid"},
        "binary": {"type": "binary"},
    }
}
prompt = "Generate a JSON object with various data types"

jsonformer = Jsonformer(
    model=model,
    tokenizer=tokenizer,
    json_schema=json_schema,
    prompt=prompt,
    debug=True,
    output_format="json", # Specify output format
    validate_output=False # Enable/disable validation
)

generated_data = jsonformer()
print(generated_data)

```

## Probabilistic Generation

`jsonAI` includes advanced features for probabilistic structured generation, allowing you to extract probability distributions or weighted means for certain types.

### Supported Probabilistic Types:

-   `p_enum`: Returns a list of possible values and their probabilities for an enumeration
-   `p_integer`: Returns the probabilistic weighted mean for an integer range

### Example:

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
from jsonAI.main import Jsonformer

model_name = "databricks/dolly-v2-3b" # Note: Probabilistic features may work better with larger models
model = AutoModelForCausalLM.from_pretrained(model_name)
tokenizer = AutoTokenizer.from_pretrained(model_name)

json_schema = {
    "type": "object",
    "properties": {
        # Get probability distribution for age within a range
        "age_probs": {"type": "p_enum", "values": [str(s) for s in range(10, 20)]},
        # Get probabilistic weighted mean for age within a range
        "age_wmean": {"type": "p_integer", "minimum": 10, "maximum": 20},
        # Get probability distribution for a boolean choice
        "is_student_probs": {"type": "p_enum", "values": ["true", "false"]},
        # Standard boolean generation
        "is_student": {"type": "boolean"},
        # Standard types also supported alongside probabilistic ones
        "name": {"type": "string", "maxLength": 4},
        "age": {"type": "integer"},
        "unit_time": {"type": "number"},
        "courses": {"type": "array", "items": {"type": "string"}},
        "trim": {"type": ["string", "null"]},
        "color": {
            "type": "enum",
            "values": ["red", "green", "blue", "brown", "white", "black"],
        },
    },
}

prompt = "Generate a young person's information based on the following schema:"
jsonformer = Jsonformer(model, tokenizer, json_schema, prompt, temperature=0)
generated_data = jsonformer()

print(generated_data)
```

## Tool and Function Calling

`jsonAI` can now act as an intelligent agent by calling external tools and functions based on the generated data. This is achieved through a `ToolRegistry` and a special `x-jsonai-tool-call` directive in your JSON schema.

### Example:

```python
from jsonAI.main import Jsonformer
from jsonAI.tool_registry import ToolRegistry
from transformers import AutoModelForCausalLM, AutoTokenizer

# 1. Define a Python function to act as a tool
def get_current_weather(city: str, temp_unit: str = "celsius"):
    """A dummy function to get weather."""
    if city.lower() == "tokyo":
        return f"The weather in {city} is 25° {temp_unit} and sunny."
    else:
        return f"Weather for {city} is not available."

# 2. Create and populate the ToolRegistry
registry = ToolRegistry()
registry.register(get_current_weather)

# 3. Define the schema with the tool call directive
weather_schema = {
  "type": "object",
  "properties": {
    "location": { "type": "string", "description": "The city name." },
    "unit": { "type": "string", "enum": ["celsius", "fahrenheit"] }
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

# 4. Instantiate Jsonformer with the registry
model = AutoModelForCausalLM.from_pretrained("gpt2")
tokenizer = AutoTokenizer.from_pretrained("gpt2")
prompt = "What is the weather like in Tokyo?"
jsonformer = Jsonformer(
    model=model,
    tokenizer=tokenizer,
    json_schema=weather_schema,
    prompt=prompt,
    tool_registry=registry
)

# 5. Execute and get the result
result = jsonformer()
print(result)
```

## MCP Integration

`jsonAI` supports calling MCP tools by providing a callback function.

### Example:

```python
from jsonAI.main import Jsonformer
from jsonAI.tool_registry import ToolRegistry
from transformers import AutoModelForCausalLM, AutoTokenizer

# MCP callback function
def mcp_callback(tool_name: str, server_name: str, arguments: dict) -> str:
    """Simulates MCP tool execution"""
    return f"MCP tool {tool_name} on server {server_name} executed with args: {arguments}"

# Register the MCP tool
registry = ToolRegistry()
registry.register({
    "name": "get_stock_price",
    "server_name": "financial-server",
    "config": {"description": "Gets current stock price"}
})

# Define the schema
stock_schema = {
    "type": "object",
    "properties": {
        "symbol": {"type": "string"},
    },
    "required": ["symbol"],
    "x-jsonai-tool-call": {
        "name": "get_stock_price",
        "arguments": {
            "symbol": "symbol"
        }
    }
}

# Instantiate and run Jsonformer
model = AutoModelForCausalLM.from_pretrained("gpt2")
tokenizer = AutoTokenizer.from_pretrained("gpt2")
prompt = "Get the stock price for GOOG"
jsonformer = Jsonformer(
    model=model,
    tokenizer=tokenizer,
    json_schema=stock_schema,
    prompt=prompt,
    tool_registry=registry,
    mcp_callback=mcp_callback
)
result = jsonformer()
print(result)
```

## Ollama Integration

You can use models from Ollama as a backend for generation.

### Example:

```python
from jsonAI.main import Jsonformer
from jsonAI.model_backends import OllamaBackend

# This requires a running Ollama instance
ollama_backend = OllamaBackend(model_name="llama2")

json_schema = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "age": {"type": "number"}
    }
}

prompt = "Generate a person's information:"
jsonformer = Jsonformer(
    model_backend=ollama_backend,
    json_schema=json_schema,
    prompt=prompt
)
generated_data = jsonformer()
print(generated_data)
```

## License

This project is licensed under the MIT License - see the [LICENSE](license.txt) file for details.
