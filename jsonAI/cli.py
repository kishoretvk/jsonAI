import click
import json
from jsonAI.main import Jsonformer, AsyncJsonformer
from jsonAI.model_backends import TransformersBackend, OllamaBackend
from jsonAI.schema_generator import SchemaGenerator
from transformers import AutoModelForCausalLM, AutoTokenizer
import asyncio

@click.group()
def cli():
    pass

def initialize_backend(use_ollama, model, ollama_model):
    """Initialize the backend based on user options."""
    if use_ollama:
        return OllamaBackend(model_name=ollama_model)
    else:
        tokenizer = AutoTokenizer.from_pretrained(model)
        model = AutoModelForCausalLM.from_pretrained(model)
        return TransformersBackend(model, tokenizer)

@cli.command()
@click.option("--schema", type=click.File('r'), required=True, help="JSON schema file")
@click.option("--prompt", required=True, help="Generation prompt")
@click.option("--model", default="gpt2", help="Model name (for transformers)")
@click.option("--use-ollama", is_flag=True, help="Use Ollama backend")
@click.option("--ollama-model", default="qwen3:0.6b", help="Ollama model name")
@click.option("--output-format", default="json", help="Output format (json, yaml, xml, csv)")
@click.option("--async", "use_async", is_flag=True, help="Use async generation")
def generate(schema, prompt, model, use_ollama, ollama_model, output_format, use_async):
    """Generate structured data from a schema and prompt"""
    try:
        json_schema = json.load(schema)
    except json.JSONDecodeError:
        click.echo("Invalid JSON schema file")
        return

    backend = initialize_backend(use_ollama, model, ollama_model)

    jsonformer = Jsonformer(
        model_backend=backend,
        json_schema=json_schema,
        prompt=prompt,
        output_format=output_format
    )

    if use_async:
        async_jsonformer = AsyncJsonformer(jsonformer)
        result = asyncio.run(async_jsonformer())
    else:
        result = jsonformer()

    # Pretty-print dict/list, print primitives/null as-is
    import sys
    from jsonAI.schema_validator import SchemaValidator
    if isinstance(result, (dict, list)):
        click.echo(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        click.echo(result)

    # Optional: Validate output and print warning if invalid
    try:
        validator = SchemaValidator()
        validator.validate(result, json_schema)
    except Exception as e:
        click.echo(f"[WARNING] Output does not validate against schema: {e}", err=True)

@cli.command()
@click.option("--description", required=True, help="Natural language schema description")
@click.option("--model", default="gpt2", help="Model name (for transformers)")
@click.option("--use-ollama", is_flag=True, help="Use Ollama backend")
@click.option("--ollama-model", default="qwen3:0.6b", help="Ollama model name")
def generate_schema(description, model, use_ollama, ollama_model):
    """Generate JSON schema from natural language description"""
    if use_ollama:
        backend = OllamaBackend(model_name=ollama_model)
    else:
        tokenizer = AutoTokenizer.from_pretrained(model)
        model = AutoModelForCausalLM.from_pretrained(model)
        backend = TransformersBackend(model, tokenizer)
    
    generator = SchemaGenerator(backend)
    schema = generator.generate_schema(description)
    # Pretty-print schema
    click.echo(json.dumps(schema, indent=2))

# (ensure two blank lines above entry point for lint)

# Entry point

if __name__ == "__main__":
    cli()
