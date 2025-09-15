"""
Enhanced CLI for JsonAI with workflow automation and API testing capabilities
"""

import asyncio
import json
import click
import yaml
from pathlib import Path
from typing import Dict, Any, Optional

from .enhanced_workflow_engine import WorkflowCLI
from .api_collection_tester import APITestingCLI


@click.group()
@click.version_option()
def cli():
    """JsonAI - Automated workflow and API testing tool"""
    pass


# Workflow Management Commands
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


@workflow.command()
@click.argument('workflow_name')
@click.option('--type', 'schedule_type', default='daily', help='Schedule type (daily, interval, cron)')
@click.option('--time', help='Time for daily schedule (HH:MM)')
@click.option('--interval', type=int, help='Interval in seconds for interval schedule')
@click.option('--cron', help='Cron expression for cron schedule')
def schedule(workflow_name, schedule_type, time, interval, cron):
    """Schedule a workflow for execution"""
    workflow_cli = WorkflowCLI()
    
    schedule_config = {'type': schedule_type}
    if schedule_type == 'daily' and time:
        schedule_config['time'] = time
    elif schedule_type == 'interval' and interval:
        schedule_config['interval_seconds'] = interval
    elif schedule_type == 'cron' and cron:
        schedule_config['cron'] = cron
    
    schedule_id = workflow_cli.schedule_workflow_command(workflow_name, schedule_config)
    click.echo(f"Workflow '{workflow_name}' scheduled with ID: {schedule_id}")


# API Testing Commands
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
@click.option('--parallel/--sequential', default=True, help='Run tests in parallel')
@click.option('--max-concurrent', type=int, default=5, help='Maximum concurrent requests')
def run_collection(collection_id, environment, parallel, max_concurrent):
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


@test.command('generate-data')
@click.option('--schema', type=click.Path(exists=True), help='JSON schema file')
@click.option('--count', type=int, default=1, help='Number of data items to generate')
@click.option('--output', type=click.Path(), help='Output file')
@click.option('--format', 'output_format', type=click.Choice(['json', 'yaml', 'csv']), default='json', help='Output format')
def generate_data(schema, count, output, output_format):
    """Generate test data based on schema"""
    if not schema:
        click.echo("Schema file is required")
        return
    
    with open(schema) as f:
        schema_data = json.load(f)
    
    from .main import Jsonformer
    from .model_backends import DummyBackend
    
    backend = DummyBackend()
    generated_data = []
    
    for i in range(count):
        jsonformer = Jsonformer(
            model_backend=backend,
            json_schema=schema_data,
            prompt=f"Generate test data item {i+1}",
            output_format=output_format
        )
        data = jsonformer.generate_data()
        generated_data.append(data)
    
    if count == 1:
        result = generated_data[0]
    else:
        result = generated_data
    
    if output:
        with open(output, 'w') as f:
            if output_format == 'json':
                json.dump(result, f, indent=2)
            elif output_format == 'yaml':
                yaml.dump(result, f, default_flow_style=False)
            else:
                f.write(str(result))
        click.echo(f"Generated data written to {output}")
    else:
        if output_format == 'json':
            click.echo(json.dumps(result, indent=2))
        elif output_format == 'yaml':
            click.echo(yaml.dump(result, default_flow_style=False))
        else:
            click.echo(result)


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
        click.echo(report_content)


# Data Pipeline Commands
@cli.group()
def data():
    """Data pipeline commands"""
    pass


@data.command('validate')
@click.argument('data_file', type=click.Path(exists=True))
@click.argument('schema_file', type=click.Path(exists=True))
def validate(data_file, schema_file):
    """Validate data against schema"""
    with open(data_file) as f:
        data = json.load(f)
    
    with open(schema_file) as f:
        schema = json.load(f)
    
    from .schema_validator import SchemaValidator
    validator = SchemaValidator()
    is_valid, errors = validator.validate(data, schema)
    
    if is_valid:
        click.echo("✓ Data is valid")
    else:
        click.echo("✗ Data validation failed:")
        for error in errors:
            click.echo(f"  - {error}")


@data.command('transform')
@click.argument('data_file', type=click.Path(exists=True))
@click.argument('config_file', type=click.Path(exists=True))
@click.option('--output', type=click.Path(), help='Output file')
def transform(data_file, config_file, output):
    """Transform data using configuration"""
    with open(data_file) as f:
        data = json.load(f)
    
    with open(config_file) as f:
        config = yaml.safe_load(f)
    
    # Simple transformation implementation
    transformations = config.get('transformations', [])
    result = data
    
    for transform in transformations:
        if transform['type'] == 'filter':
            # Filter implementation
            pass
        elif transform['type'] == 'map':
            # Map implementation
            pass
    
    if output:
        with open(output, 'w') as f:
            json.dump(result, f, indent=2)
        click.echo(f"Transformed data written to {output}")
    else:
        click.echo(json.dumps(result, indent=2))


# Integration Commands
@cli.group()
def integration():
    """Integration management commands"""
    pass


@integration.command('github')
@click.option('--token', required=True, help='GitHub personal access token')
@click.option('--repo', help='Repository in format owner/repo')
def github(token, repo):
    """Setup GitHub integration"""
    from .integration_hub import IntegrationHub
    
    async def setup_github():
        hub = IntegrationHub()
        await hub.github_integration(token=token, repo=repo)
        click.echo("GitHub integration configured")
    
    asyncio.run(setup_github())


@integration.command('slack')
@click.option('--webhook-url', required=True, help='Slack webhook URL')
def slack(webhook_url):
    """Setup Slack integration"""
    from .integration_hub import IntegrationHub
    
    async def setup_slack():
        hub = IntegrationHub()
        await hub.slack_integration(webhook_url=webhook_url)
        click.echo("Slack integration configured")
    
    asyncio.run(setup_slack())


# Server Commands
@cli.group()
def server():
    """Server management commands"""
    pass


@server.command('start')
@click.option('--host', default='localhost', help='Host to bind to')
@click.option('--port', default=8000, type=int, help='Port to bind to')
@click.option('--workers', default=1, type=int, help='Number of worker processes')
def start(host, port, workers):
    """Start the JsonAI API server"""
    import uvicorn
    from .api import app
    
    click.echo(f"Starting JsonAI API server on {host}:{port}")
    uvicorn.run(
        "jsonAI.api:app",
        host=host,
        port=port,
        workers=workers,
        reload=False
    )


# Utility Commands
@cli.group()
def utils():
    """Utility commands"""
    pass


@utils.command('init')
@click.argument('project_name')
@click.option('--type', 'project_type', type=click.Choice(['workflow', 'api-testing', 'full']), default='full', help='Project type')
def init(project_name, project_type):
    """Initialize a new JsonAI project"""
    project_path = Path(project_name)
    project_path.mkdir(exist_ok=True)
    
    # Create basic project structure
    (project_path / 'workflows').mkdir(exist_ok=True)
    (project_path / 'collections').mkdir(exist_ok=True)
    (project_path / 'schemas').mkdir(exist_ok=True)
    (project_path / 'config').mkdir(exist_ok=True)
    
    # Create example files
    if project_type in ['workflow', 'full']:
        example_workflow = {
            'name': 'example_workflow',
            'version': '1.0',
            'description': 'Example workflow for JsonAI',
            'variables': {
                'api_base_url': 'https://api.example.com'
            },
            'steps': [
                {
                    'id': 'generate_user_data',
                    'name': 'Generate User Data',
                    'type': 'json_generation',
                    'config': {
                        'schema': {
                            'type': 'object',
                            'properties': {
                                'name': {'type': 'string'},
                                'email': {'type': 'string', 'format': 'email'},
                                'age': {'type': 'integer', 'minimum': 18}
                            }
                        },
                        'prompt': 'Generate a realistic user profile',
                        'output_variable': 'user_data'
                    }
                },
                {
                    'id': 'send_api_request',
                    'name': 'Send API Request',
                    'type': 'api_request',
                    'depends_on': ['generate_user_data'],
                    'config': {
                        'method': 'POST',
                        'url': '${api_base_url}/users',
                        'headers': {
                            'Content-Type': 'application/json'
                        },
                        'body': '${user_data}',
                        'output_variable': 'api_response'
                    }
                }
            ]
        }
        
        with open(project_path / 'workflows' / 'example_workflow.yaml', 'w') as f:
            yaml.dump(example_workflow, f, default_flow_style=False)
    
    if project_type in ['api-testing', 'full']:
        example_schema = {
            'type': 'object',
            'properties': {
                'id': {'type': 'integer'},
                'name': {'type': 'string'},
                'email': {'type': 'string', 'format': 'email'},
                'created_at': {'type': 'string', 'format': 'date-time'}
            },
            'required': ['name', 'email']
        }
        
        with open(project_path / 'schemas' / 'user_schema.json', 'w') as f:
            json.dump(example_schema, f, indent=2)
    
    # Create config file
    config = {
        'project_name': project_name,
        'version': '1.0.0',
        'description': f'{project_name} JsonAI project',
        'settings': {
            'model_backend': 'dummy',
            'default_output_format': 'json',
            'max_retries': 3,
            'timeout': 300
        }
    }
    
    with open(project_path / 'config' / 'project.yaml', 'w') as f:
        yaml.dump(config, f, default_flow_style=False)
    
    # Create README
    readme_content = f"""# {project_name}

JsonAI project for workflow automation and API testing.

## Structure

- `workflows/` - Workflow definitions
- `collections/` - API collections (Postman, OpenAPI)
- `schemas/` - JSON schemas for data generation
- `config/` - Project configuration

## Quick Start

1. Run example workflow:
   ```bash
   jsonai workflow run example_workflow
   ```

2. Generate test data:
   ```bash
   jsonai test generate-data --schema schemas/user_schema.json --count 10
   ```

3. Start API server:
   ```bash
   jsonai server start
   ```

## Documentation

Visit the [JsonAI documentation](https://github.com/kishoretvk/jsonAI) for more information.
"""
    
    with open(project_path / 'README.md', 'w') as f:
        f.write(readme_content)
    
    click.echo(f"✓ Project '{project_name}' initialized successfully")
    click.echo(f"  Directory: {project_path.absolute()}")
    click.echo(f"  Type: {project_type}")


@utils.command('validate-workflow')
@click.argument('workflow_file', type=click.Path(exists=True))
def validate_workflow(workflow_file):
    """Validate workflow configuration file"""
    try:
        with open(workflow_file) as f:
            if workflow_file.endswith(('.yml', '.yaml')):
                workflow_data = yaml.safe_load(f)
            else:
                workflow_data = json.load(f)
        
        # Basic validation
        required_fields = ['name', 'version', 'steps']
        for field in required_fields:
            if field not in workflow_data:
                click.echo(f"✗ Missing required field: {field}")
                return
        
        steps = workflow_data.get('steps', [])
        if not steps:
            click.echo("✗ Workflow must have at least one step")
            return
        
        step_ids = set()
        for step in steps:
            if 'id' not in step:
                click.echo("✗ Step missing required 'id' field")
                return
            if step['id'] in step_ids:
                click.echo(f"✗ Duplicate step ID: {step['id']}")
                return
            step_ids.add(step['id'])
            
            if 'type' not in step:
                click.echo(f"✗ Step '{step['id']}' missing required 'type' field")
                return
        
        click.echo("✓ Workflow configuration is valid")
        
    except Exception as e:
        click.echo(f"✗ Error validating workflow: {e}")


if __name__ == '__main__':
    cli()