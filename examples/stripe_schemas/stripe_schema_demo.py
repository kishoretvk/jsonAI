import json
import asyncio
from pathlib import Path
from jsonAI.output_formatter import OutputFormatter
from jsonAI.model_backends import OllamaBackend
from jsonAI.main import Jsonformer, AsyncJsonformer
from jsonAI.tool_registry import ToolRegistry

# Example tool functions
def uppercase_value(value):
    return {"value": value.upper()}

def append_suffix(value, suffix="_demo"):
    return {"value": value + suffix}

# Register tools
tool_registry = ToolRegistry()
tool_registry.register(uppercase_value)
tool_registry.register(append_suffix)

# Supported schemas and environments
schemas = [
    "transfer_reversals_metadata",
    "tax_rates_metadata",
    "transfer_reversals"
]
environments = ["dev", "qa", "cte", "perf", "prod"]

base_dir = Path(__file__).parent

async def generate_for_config(schema_choice, env):
    config_path = base_dir / f"{schema_choice}.{env}.json"
    with open(config_path) as f:
        config = json.load(f)
        schema_path = base_dir / config["schema"]
    with open(schema_path) as f:
        schema = json.load(f)
    # Add tool chaining to schema (for demonstration)
    schema["x-jsonai-tool-chain"] = [
        {
            "name": "uppercase_value",
            "arguments": {"value": "value"}
        },
        {
            "name": "append_suffix",
            "arguments": {"value": "value", "suffix": "_demo"}
        }
    ]
    backend = OllamaBackend("mistral:latest")
    prompt = f"Generate a {schema_choice} object with sample values for {env}."
    jsonformer = Jsonformer(
        model_backend=backend,
        json_schema=schema,
        prompt=prompt,
        tool_registry=tool_registry
    )
    async_jsonformer = AsyncJsonformer(jsonformer)
    try:
        # Print raw generated data before tool chaining
        raw_data = jsonformer.generate_data()
        print(f"[DEBUG] Raw generated data for {schema_choice} ({env}):", raw_data)
        result = await async_jsonformer()
        print(f"[DEBUG] Final result after tool chaining for {schema_choice} ({env}):", result)
    except Exception as e:
        print(f"[ERROR] Exception for {schema_choice} ({env}): {e}")
        result = None
    return {
        "schema": schema_choice,
        "environment": env,
        "result": result
    }

async def main():
    tasks = []
    for schema_choice in schemas:
        for env in environments:
            tasks.append(generate_for_config(schema_choice, env))
    results = await asyncio.gather(*tasks)
    for entry in results:
        print(f"Schema: {entry['schema']}, Environment: {entry['environment']}")
        print("Output:", json.dumps(entry["result"], indent=2))
        print("-" * 60)

if __name__ == "__main__":
    asyncio.run(main())
