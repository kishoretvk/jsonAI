import click
import json
import yaml
import asyncio
from pathlib import Path
from jsonAI.main import Jsonformer, AsyncJsonformer
from jsonAI.model_backends import TransformersBackend, OllamaBackend, DummyBackend
from jsonAI.schema_generator import SchemaGenerator
from transformers import AutoModelForCausalLM, AutoTokenizer

# Import enhanced features
try:
    from .enhanced_workflow_engine import WorkflowCLI
    from .api_collection_tester import APITestingCLI
    ENHANCED_FEATURES = True
except ImportError:
    ENHANCED_FEATURES = False
    click.echo("Enhanced features not available. Some commands may be disabled.")

@click.group()
@click.version_option()
def cli():
    """JsonAI - Advanced JSON generation and workflow automation tool"""
    pass

def initialize_backend(use_ollama, model, ollama_model):
    """Initialize the backend based on user options."""
    if use_ollama:
        try:
            return OllamaBackend(model_name=ollama_model)
        except Exception as e:
            print(f"Warning: Could not initialize Ollama backend: {e}")
            print("Falling back to DummyBackend for testing")
            return DummyBackend()
    else:
        try:
            tokenizer = AutoTokenizer.from_pretrained(model)
            model = AutoModelForCausalLM.from_pretrained(model)
            return TransformersBackend(model, tokenizer)
        except Exception as e:
            print(f"Warning: Could not initialize Transformers backend: {e}")
            print("Falling back to DummyBackend for testing")
            return DummyBackend()

@cli.command()
@click.option("--schema", type=click.File('r'), required=True, help="JSON schema file")
@click.option("--prompt", required=True, help="Generation prompt")
@click.option("--model", default="gpt2", help="Model name (for transformers)")
@click.option("--use-ollama", is_flag=True, help="Use Ollama backend")
@click.option("--ollama-model", default="qwen3:0.6b", help="Ollama model name")
@click.option("--output-format", default="json", help="Output format (json, yaml, xml, csv)")
@click.option("--async", "use_async", is_flag=True, help="Use async generation")
@click.option("--count", default=1, help="Number of items to generate")
@click.option("--output", type=click.Path(), help="Output file path")
def generate(schema, prompt, model, use_ollama, ollama_model, output_format, use_async, count, output):
    """Generate structured data from a schema and prompt"""
    try:
        json_schema = json.load(schema)
    except json.JSONDecodeError:
        click.echo("Invalid JSON schema file")
        return

    backend = initialize_backend(use_ollama, model, ollama_model)

    results = []
    for i in range(count):
        current_prompt = prompt if count == 1 else f"{prompt} (item {i+1})"
        
        jsonformer = Jsonformer(
            model_backend=backend,
            json_schema=json_schema,
            prompt=current_prompt,
            output_format=output_format
        )

        if use_async:
            async_jsonformer = AsyncJsonformer(jsonformer)
            result = asyncio.run(async_jsonformer())
        else:
            result = jsonformer()
        
        results.append(result)

    # Prepare final output
    final_result = results[0] if count == 1 else results
    
    # Format output
    if output_format.lower() == 'json':
        formatted_output = json.dumps(final_result, indent=2, ensure_ascii=False)
    elif output_format.lower() == 'yaml':
        formatted_output = yaml.dump(final_result, default_flow_style=False)
    else:
        formatted_output = str(final_result)
    
    # Output to file or console
    if output:
        with open(output, 'w') as f:
            f.write(formatted_output)
        click.echo(f"Output written to {output}")
    else:
        click.echo(formatted_output)

    # Optional: Validate output and print warning if invalid
    try:
        from jsonAI.schema_validator import SchemaValidator
        validator = SchemaValidator()
        for result in results:
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

# Workflow Management Commands (Enhanced Features)
if ENHANCED_FEATURES:
    @cli.group()
    def workflow():
        """Workflow management commands"""
        pass

    @workflow.command()
    @click.argument('config_file', type=click.Path(exists=True))
    def create(config_file):
        """Create a workflow from configuration file"""
        workflow_cli = WorkflowCLI()
        workflow_name = workflow_cli.create_workflow_command(config_file)
        click.echo(f"Workflow '{workflow_name}' created successfully")

    @workflow.command()
    @click.argument('workflow_name')
    @click.option('--variables', '-v', help='Runtime variables as JSON string')
    @click.option('--variables-file', type=click.Path(exists=True), help='Variables from file')
    def run(workflow_name, variables, variables_file):
        """Run a workflow"""
        workflow_cli = WorkflowCLI()
        
        # Parse variables
        runtime_vars = {}
        if variables:
            runtime_vars.update(json.loads(variables))
        if variables_file:
            with open(variables_file) as f:
                if variables_file.endswith(('.yml', '.yaml')):
                    runtime_vars.update(yaml.safe_load(f))
                else:
                    runtime_vars.update(json.load(f))
        
        async def run_workflow():
            execution_id = await workflow_cli.run_workflow_command(workflow_name, runtime_vars)
            click.echo(f"Workflow execution started with ID: {execution_id}")
            return execution_id
        
        asyncio.run(run_workflow())

    @workflow.command()
    def list():
        """List all available workflows"""
        workflow_cli = WorkflowCLI()
        workflows = workflow_cli.list_workflows_command()
        if workflows:
            click.echo("Available workflows:")
            for workflow in workflows:
                click.echo(f"  - {workflow}")
        else:
            click.echo("No workflows found")

    @workflow.command()
    @click.argument('execution_id')
    def status(execution_id):
        """Get workflow execution status"""
        workflow_cli = WorkflowCLI()
        execution = workflow_cli.status_command(execution_id)
        if execution:
            click.echo(f"Execution ID: {execution.id}")
            click.echo(f"Workflow: {execution.workflow_name}")
            click.echo(f"Status: {execution.status.value}")
            click.echo(f"Start Time: {execution.start_time}")
            if execution.end_time:
                click.echo(f"End Time: {execution.end_time}")
            if execution.error_message:
                click.echo(f"Error: {execution.error_message}")
        else:
            click.echo(f"Execution '{execution_id}' not found")

    # API Testing Commands (Enhanced Features)
    @cli.group()
    def test():
        """API testing commands"""
        pass

    @test.command('import-collection')
    @click.option('--source', type=click.Choice(['postman', 'openapi']), required=True, help='Collection source')
    @click.argument('file', type=click.Path(exists=True))
    def import_collection(source, file):
        """Import API collection for testing"""
        api_cli = APITestingCLI()
        collection_id = api_cli.import_collection_command(source, file)
        click.echo(f"Collection imported with ID: {collection_id}")

    @test.command('run-collection')
    @click.argument('collection_id')
    @click.option('--environment', default='default', help='Environment to use')
    def run_collection(collection_id, environment):
        """Run API collection tests"""
        api_cli = APITestingCLI()
        
        async def run_tests():
            results = await api_cli.run_tests_command(collection_id, environment)
            
            total_tests = len(results)
            passed_tests = sum(1 for r in results if r.success)
            failed_tests = total_tests - passed_tests
            
            click.echo(f"API Test Results:")
            click.echo(f"  Total: {total_tests}")
            click.echo(f"  Passed: {passed_tests}")
            click.echo(f"  Failed: {failed_tests}")
            
            if failed_tests > 0:
                click.echo("\nFailed tests:")
                for result in results:
                    if not result.success:
                        click.echo(f"  - {result.name}: {result.error_message}")
        
        asyncio.run(run_tests())

    @test.command('report')
    @click.option('--format', 'report_format', type=click.Choice(['html', 'json', 'junit']), default='html', help='Report format')
    @click.option('--output', type=click.Path(), help='Output file')
    def report(report_format, output):
        """Generate test report"""
        api_cli = APITestingCLI()
        report_content = api_cli.generate_report_command(report_format, output)
        
        if output:
            click.echo(f"Report generated: {output}")
        else:
            click.echo(report_content[:1000] + "..." if len(report_content) > 1000 else report_content)

# Entry point

if __name__ == "__main__":
    cli()
