# JsonAI — Production-Ready Structured JSON Generation with LLMs

## Environment Configuration

This project uses separate environment files for dev, qa, perf, cte, and prod, each located at the project root as `.env.dev`, `.env.qa`, `.env.perf`, `.env.cte`, and `.env.prod`. These files contain environment-specific variables for OIDC, metrics, tracing, and service endpoints. All files use the same variable structure for consistency and ease of deployment. See the `examples/stripe_schemas/` directory for environment-specific schema configs.

JsonAI is a comprehensive Python library for generating structured JSON data using Large Language Models (LLMs). It provides enterprise-grade features including robust JSON schema validation, multiple model backends, REST API, React frontend, CLI interface, and production deployment configurations.

Current version: 0.15.1

## 🔔 What’s New in 0.15.1

- Stabilized FastAPI REST API with endpoints for sync/async generation, batch processing, stats, cache management, and schema validation
- Performance suite:
  - PerformanceMonitor async timing fixes
  - CachedJsonformer with LRU/TTL caching
  - BatchProcessor for efficient concurrent execution
  - OptimizedJsonformer combines caching + batch processing with warmup
- Async generation improvements:
  - FullAsyncJsonformer (aliased as AsyncJsonformer in the API)
  - AsyncJsonformer wrapper in main.py for async tool execution
- Logging hygiene: lazy logging interpolation to reduce overhead
- Packaging: PyPI publish flow cleaned; version bumped to 0.15.1

## 🚀 Features

### Quantitative Output Quality Metrics

JsonAI's output quality is validated with statistical metrics. The following table summarizes KL divergence (lower is better) and timing (seconds) for core types, measured using uniform schema sampling and the built-in metrics suite:

| Type    | KL Divergence | Time (s) |
|---------|---------------|----------|
| number  | 0.016813      | 4.5798   |
| integer | 0.000864      | 4.5564   |
| boolean | 0.000018      | 4.4584   |
| enum    | 0.000108      | 4.4765   |

All values are well below the recommended threshold (KL < 0.5), demonstrating high-fidelity, schema-faithful sampling. See `tests/test_metrics_sampling.py` for methodology.

### Core Capabilities
- Multiple LLM Backends: Ollama, OpenAI, and HuggingFace Transformers
- Full JSON Schema Coverage: primitives, arrays, objects, enums, nested structures, oneOf
- Performance Optimization: caching (LRU/TTL), batch processing, async operations
- Production Ready: Docker, FastAPI, monitoring, scaling considerations

### Interfaces & APIs
- REST API: FastAPI-based service with OpenAPI docs
- React Frontend: Modern web interface for JSON generation
- CLI Interface: Command-line tools for automation and batch processing
- Python Library: Programmatic access with sync and async support

### Enterprise Features
- Caching System: Intelligent multi-level caching (LRU/TTL)
- Batch Processing: Concurrent batch execution
- Performance Monitoring: Built-in metrics via PerformanceMonitor
- Schema Validation: Comprehensive validation with jsonschema
- Multiple Output Formats: JSON, YAML, XML, and CSV

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

- **Jsonformer** (jsonAI.main): Orchestrates generation, formatting, and validation
- **TypeGenerator**: Generates values for each JSON Schema type
- **OutputFormatter**: Converts data into JSON, YAML, XML, CSV
- **SchemaValidator**: Validates data with jsonschema
- **ToolRegistry**: Registers and resolves Python/MCP tools
- **Async Paths**:
  - **FullAsyncJsonformer** (jsonAI.async_jsonformer): asynchronous generator taking model_backend, json_schema, prompt (aliased as AsyncJsonformer in API)
  - **AsyncJsonformer wrapper** (jsonAI.main): wraps a Jsonformer instance for async tool execution

## Testing

The project includes comprehensive tests for each component and integration:

-   **Unit Tests**: Test individual components.
-   **Integration Tests**: Validate the interaction between components.

To run tests:

```bash
pytest tests/
```

## Quick API Start (FastAPI)

Run the API with uvicorn:

```bash
uvicorn jsonAI.api:app --host 0.0.0.0 --port 8000
```

Then open http://localhost:8000/docs for interactive Swagger UI.

### REST Endpoints

- POST /generate — synchronous generation
- POST /generate/async — asynchronous generation
- POST /generate/batch — concurrent batch generation
- GET /stats — performance and cache statistics
- DELETE /cache — clear all caches
- POST /validate — validate a JSON schema

Minimal cURL examples:

```bash
# Sync generate
curl -X POST http://localhost:8000/generate -H "Content-Type: application/json" -d '{
  "prompt": "Generate a simple user object",
  "schema": {"type":"object","properties":{"name":{"type":"string"},"age":{"type":"integer"}}},
  "model_name": "ollama",
  "model_path": "mistral:latest"
}'

# Async generate
curl -X POST http://localhost:8000/generate/async -H "Content-Type: application/json" -d '{
  "prompt": "Generate a simple user object",
  "schema": {"type":"object","properties":{"name":{"type":"string"},"age":{"type":"integer"}}},
  "model_name": "ollama",
  "model_path": "mistral:latest"
}'

# Batch generate
curl -X POST http://localhost:8000/generate/batch -H "Content-Type: application/json" -d '{
  "requests": [
    {"prompt":"User 1","schema":{"type":"object","properties":{"name":{"type":"string"}}},"model_name":"ollama","model_path":"mistral:latest"},
    {"prompt":"User 2","schema":{"type":"object","properties":{"name":{"type":"string"}}},"model_name":"ollama","model_path":"mistral:latest"}
  ],
  "max_concurrent": 5
}'
```

## Examples

### Stripe Schema Demo

A full demonstration of environment-based configuration and schema-driven generation is provided in both:

- [`examples/stripe_schemas/stripe_schema_demo.py`](examples/stripe_schemas/stripe_schema_demo.py) (Python script)
- [`examples/stripe_schemas/stripe_schema_demo.ipynb`](examples/stripe_schemas/stripe_schema_demo.ipynb) (Jupyter notebook)

**Features demonstrated:**
- Loading Stripe-like schemas and environment-specific config files
- Switching between multiple schemas (`transfer_reversals_metadata`, `tax_rates_metadata`, `transfer_reversals`) and environments (`dev`, `qa`, `cte`, `perf`, `prod`)
- Using config file naming conventions: `<schema>.<env>.json` (e.g., `transfer_reversals_metadata.dev.json`)
- Tool chaining and environment-driven config patterns
- Integration with Ollama and JsonAI's tool registry

**Usage pattern:**
```python
env = "dev"  # or "qa", "cte", "perf", "prod"
schema_choice = "transfer_reversals_metadata"  # or "tax_rates_metadata", "transfer_reversals"
config_path = base_dir / f"{schema_choice}.{env}.json"
```

All required schema and config files are provided in [`examples/stripe_schemas/`](examples/stripe_schemas/).  
You can run the Python script or the notebook to see how to generate and validate data for any supported schema/environment combination.

See the `examples/stripe_schemas/` directory for all related files and configuration patterns.

### Basic JSON Generation

```python
from jsonAI.main import Jsonformer
from jsonAI.model_backends import DummyBackend
backend = DummyBackend()  # replace with OllamaBackend/OpenAIBackend/etc.

# Primitive type: string
schema = {"type": "string"}
prompt = "Generate a random color name."
jsonformer = Jsonformer(model_backend=backend, json_schema=schema, prompt=prompt)
print(jsonformer())  # e.g., "blue"

# Primitive type: number
schema = {"type": "number"}
prompt = "Generate a random floating point number."
jsonformer = Jsonformer(model_backend=backend, json_schema=schema, prompt=prompt)
print(jsonformer())  # e.g., 3.1415

# Enum type
schema = {"type": "string", "enum": ["A", "B", "C"]}
prompt = "Pick a letter from the set A, B, or C."
jsonformer = Jsonformer(model_backend=backend, json_schema=schema, prompt=prompt)
print(jsonformer())  # e.g., "B"

# Object type
schema = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "age": {"type": "integer"},
        "isStudent": {"type": "boolean"}
    }
}
prompt = "Generate a person's profile."
jsonformer = Jsonformer(model_backend=backend, json_schema=schema, prompt=prompt)
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
jsonformer = Jsonformer(model_backend=backend, json_schema=schema, prompt=prompt, output_format="yaml")
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
jsonformer = Jsonformer(model_backend=backend, json_schema=schema, prompt=prompt, output_format="csv")
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
python -m jsonAI.cli generate --schema complex_schema.json \
  --prompt "Generate a comprehensive person profile as JSON." \
  --use-ollama --ollama-model mistral:latest
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
jsonformer = Jsonformer(model_backend=backend, json_schema=schema, prompt=prompt, tool_registry=tool_registry)
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
jsonformer = Jsonformer(model_backend=backend, json_schema=schema, prompt=prompt, mcp_callback=mcp_callback)
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
jsonformer = Jsonformer(model_backend=backend, json_schema=schema, prompt=prompt, output_format="xml")
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

## Performance and Caching

JsonAI includes a performance suite to optimize throughput and latency.

## Quantitative Output Quality Metrics

JsonAI's output quality is validated with statistical metrics. The following table summarizes KL divergence (lower is better) and timing (seconds) for core types, measured using uniform schema sampling and the built-in metrics suite:

| Type    | KL Divergence | Time (s) |
|---------|---------------|----------|
| number  | 0.016813      | 4.5798   |
| integer | 0.000864      | 4.5564   |
| boolean | 0.000018      | 4.4584   |
| enum    | 0.000108      | 4.4765   |

All values are well below the recommended threshold (KL < 0.5), demonstrating high-fidelity, schema-faithful sampling. See `tests/test_metrics_sampling.py` for methodology.

- **PerformanceMonitor**: measures durations for operations (async-safe)
- **CachedJsonformer**: two-level caching
  - LRU cache for simple schema-based results
  - TTL cache for prompt-based entries for complex schemas
- **OptimizedJsonformer**: all performance features plus cache warmup and batch helpers
- **BatchProcessor**: asynchronous concurrent processing (configurable semaphore)

Example:

```python
from jsonAI.performance import OptimizedJsonformer
from jsonAI.model_backends import DummyBackend

backend = DummyBackend()
schema = {"type":"object","properties":{"name":{"type":"string"}}}

jsonformer = OptimizedJsonformer(
    model=backend,          # accepts a ModelBackend
    tokenizer=backend.tokenizer,
    schema=schema,
    cache_size=1000,
    cache_ttl=3600
)

# Single generation (cached)
print(jsonformer.generate("Generate a name"))

# Batch generation
requests = [
  {"prompt":"User A","kwargs":{}},
  {"prompt":"User B","kwargs":{}}
]
print(jsonformer.generate_batch(requests))
```

To inspect performance and cache stats at runtime, use the REST API `GET /stats` or:
```python
jsonformer.get_comprehensive_stats()
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

- LLMs: HuggingFace Transformers, OpenAI, Ollama (vLLM patterns apply)
- FastAPI: See `jsonAI/api.py` and `examples/fastapi_example.py`
- Tool Registry: Register and call Python or MCP tools from schemas; supports tool chaining via `x-jsonai-tool-chain`
- Async Support:
  - `FullAsyncJsonformer` for async generation with `model_backend/json_schema/prompt`
  - `AsyncJsonformer` wrapper (jsonAI.main) for async tool execution

See the [examples/](examples/) directory for more advanced usage and integration patterns.

## License

This project is licensed under the MIT License.

## Native Library Usage

JsonAI leverages high-performance native libraries for data processing and extensibility:

- **PyYAML** for YAML serialization
- **lxml** for XML output
- **cachetools** for caching
- **requests** and **aiohttp** for HTTP
- **jsonschema** for validation

For any tabular or batch data processing, it is recommended to use **pandas** for reliability and performance. If you extend JsonAI or build custom output logic, prefer native libraries like pandas, numpy, or others for best results.

## Multi-Environment Support

JsonAI supports multiple environments: dev, qa, perf, cte, and prod. Each environment has its own `.env` file at the project root.

- **Local Development:**  
  Copy or rename the desired `.env.*` file to `.env` before running locally.
  ```bash
  cp .env.dev .env
  uvicorn jsonAI.api:app --host 0.0.0.0 --port 8000
  ```

- **Docker Compose:**  
  Edit `docker-compose.yml` to set the `env_file` for the desired environment (e.g., `.env.prod`).  
  Or override at runtime:
  ```bash
  docker-compose --env-file .env.qa up -d
  ```

- **Docker:**  
  Pass the environment file at runtime:
  ```bash
  docker run --env-file .env.prod -p 8000:8000 jsonai:latest
  ```

- **CI/CD:**  
  The GitHub Actions workflow tests all environments by copying the correct `.env.*` file to `.env` for each matrix job.

- **APP_ENV Variable:**  
  The Dockerfile sets `APP_ENV` (default: dev) for extensibility. You can override this at runtime.

See `docs/deployment.md` for more details.

## Deployment

- API:
  - `uvicorn jsonAI.api:app --host 0.0.0.0 --port 8000`
  - CORS is enabled by default for development; harden for production
- Docker:
  - `docker build -t jsonai:latest .`
  - `docker run -p 8000:8000 jsonai:latest`
- Docker Compose:
  - `docker-compose up -d`
- See `docs/deployment.md` for more

## Versioning and Release

PyPI forbids reusing the same filename for the same version. Always bump the version:

```bash
poetry version patch  # or minor/major
poetry build
poetry publish -u __token__ -p $PYPI_TOKEN
```

Automate in CI by bumping on tags and using repository secrets for tokens.

## Streaming Support

JsonAI supports streaming data generation (experimental API in examples). Example pattern:

```python
jsonformer = Jsonformer(model_backend, json_schema, prompt)
for data_chunk in jsonformer.stream_generate_data():
    print(data_chunk)
```

For async streaming, adapt the pattern with the async wrapper as needed.

## Limitations

- All native JSON schema types are now fully supported and tested, including primitives (`string`, `number`, `integer`, `boolean`, `null`), enums, arrays, objects, oneOf, and nested/complex schemas.
- See [examples/test_json_schema_variety.py](examples/test_json_schema_variety.py) for comprehensive test coverage and usage patterns.
