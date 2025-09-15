# JsonAI Enhanced Features Installation and Usage Guide

## Overview

This guide covers the new enhanced features added to JsonAI for workflow automation and API collection testing. These enhancements transform JsonAI from a simple JSON generation library into a comprehensive automation and testing platform.

## Installation

### Prerequisites

- Python 3.9 or higher
- pip or poetry for package management

### Standard Installation

```bash
pip install jsonai
```

### Development Installation

```bash
git clone https://github.com/kishoretvk/jsonAI.git
cd jsonAI
pip install -e .
```

### Required Dependencies for Enhanced Features

```bash
pip install aiohttp pydantic click PyYAML
```

## New Features Overview

### 1. Enhanced Workflow Automation Engine

- **YAML/JSON workflow definitions**
- **Conditional branching and loops**
- **Parallel execution support**
- **Error handling and retry mechanisms**
- **Workflow scheduling**
- **Progress monitoring and reporting**

### 2. API Collection Testing Framework

- **Postman collection import/export**
- **OpenAPI specification testing**
- **Automated test data generation**
- **Response validation**
- **Performance metrics collection**
- **Comprehensive test reporting**

### 3. Enhanced CLI Interface

- **Workflow management commands**
- **API testing commands**
- **Data pipeline operations**
- **Integration management**
- **Project initialization utilities**

## Quick Start Examples

### 1. Basic Workflow Creation

Create a workflow file `example_workflow.yaml`:

```yaml
name: "api_testing_workflow"
version: "1.0"
description: "Simple API testing workflow"
variables:
  api_base_url: "https://jsonplaceholder.typicode.com"
  
steps:
  - id: "generate_user_data"
    name: "Generate Test User Data"
    type: "json_generation"
    config:
      schema:
        type: "object"
        properties:
          name: {type: "string"}
          email: {type: "string", format: "email"}
          age: {type: "integer", minimum: 18}
      prompt: "Generate a realistic user profile"
      output_variable: "user_data"
      
  - id: "send_api_request"
    name: "Test API Endpoint"
    type: "api_request"
    depends_on: ["generate_user_data"]
    config:
      method: "POST"
      url: "${api_base_url}/users"
      headers:
        Content-Type: "application/json"
      body: "${user_data}"
      expected_status: 201
```

Run the workflow:

```bash
# Create workflow
jsonai workflow create example_workflow.yaml

# Run workflow
jsonai workflow run api_testing_workflow

# Check status
jsonai workflow list
```

### 2. API Collection Testing

Import and test a Postman collection:

```bash
# Import Postman collection
jsonai test import-collection --source postman my_api_collection.json

# Run tests
jsonai test run-collection <collection_id> --environment dev

# Generate HTML report
jsonai test report --format html --output test_report.html
```

### 3. Advanced Data Generation

Generate multiple test data items:

```bash
# Generate 100 user records
jsonai generate --schema user_schema.json --prompt "Generate user data" --count 100 --output users.json

# Generate in different formats
jsonai generate --schema user_schema.json --prompt "Generate user data" --output-format yaml --output users.yaml
```

## Workflow Configuration Reference

### Workflow Definition Structure

```yaml
name: "workflow_name"           # Required: Unique workflow name
version: "1.0"                  # Required: Version string
description: "Description"      # Optional: Workflow description

variables:                      # Optional: Global variables
  key: "value"

steps:                          # Required: List of workflow steps
  - id: "step_id"              # Required: Unique step identifier
    name: "Step Name"          # Required: Human-readable name
    type: "step_type"          # Required: Step type (see below)
    depends_on: ["step1"]      # Optional: Dependencies
    parallel: true             # Optional: Enable parallel execution
    retry_count: 3             # Optional: Retry attempts
    timeout: 300               # Optional: Timeout in seconds
    on_failure: "continue"     # Optional: stop|continue|retry
    conditions:                # Optional: Execution conditions
      variable_equals: "var=value"
    config:                    # Required: Step-specific configuration
      # Configuration varies by step type

error_handling:                # Optional: Global error handling
  retry_count: 3
  timeout: 300
  on_failure: "stop"

schedule:                      # Optional: Workflow scheduling
  type: "daily"               # daily|interval|cron
  time: "09:00"              # For daily schedules

notifications:                 # Optional: Notifications
  on_success:
    type: "slack"
    webhook_url: "https://..."
  on_failure:
    type: "email"
    to: "admin@company.com"
```

### Supported Step Types

#### 1. JSON Generation (`json_generation`)

```yaml
type: "json_generation"
config:
  schema:                      # JSON schema for generation
    type: "object"
    properties:
      name: {type: "string"}
  prompt: "Generate test data"   # Generation prompt
  output_variable: "var_name"   # Variable to store result
  jsonformer_options:          # Optional Jsonformer options
    temperature: 0.7
    max_tokens: 150
```

#### 2. API Request (`api_request`)

```yaml
type: "api_request"
config:
  method: "POST"               # HTTP method
  url: "https://api.example.com/endpoint"
  headers:                     # Request headers
    Content-Type: "application/json"
    Authorization: "Bearer ${token}"
  body: "${data_variable}"     # Request body (supports variables)
  expected_status: 200         # Expected HTTP status code
  output_variable: "response"  # Variable to store response
```

#### 3. API Test Collection (`api_test_collection`)

```yaml
type: "api_test_collection"
config:
  collection_path: "./collection.json"  # Path to collection file
  collection_type: "postman"            # postman|openapi
  environment: "staging"                # Environment name
  output_variable: "test_results"       # Variable to store results
```

#### 4. Data Validation (`data_validation`)

```yaml
type: "data_validation"
config:
  data_variable: "data_to_validate"     # Variable containing data
  schema:                               # Validation schema
    type: "object"
    required: ["name", "email"]
  fail_on_invalid: true                 # Fail workflow if invalid
```

#### 5. Data Transformation (`data_transformation`)

```yaml
type: "data_transformation"
config:
  input_variable: "input_data"          # Input data variable
  transformation:                       # Transformation configuration
    type: "filter"                     # filter|map|aggregate
    condition:                         # For filter operations
      type: "equals"
      field: "status"
      value: "active"
  output_variable: "filtered_data"      # Output variable
```

#### 6. Conditional (`conditional`)

```yaml
type: "conditional"
config:
  condition:                           # Condition to evaluate
    type: "equals"                    # equals|greater_than|contains
    field: "status"                   # Field to check
    value: "success"                  # Expected value
```

#### 7. Loop (`loop`)

```yaml
type: "loop"
config:
  loop_variable: "items"               # Variable containing array
  steps:                               # Steps to execute for each item
    - type: "api_request"
      config:
        method: "POST"
        url: "https://api.example.com/process"
        body: "${_current_item}"       # Current loop item
```

#### 8. Parallel (`parallel`)

```yaml
type: "parallel"
config:
  steps:                               # Steps to execute in parallel
    - type: "api_request"
      config: {...}
    - type: "json_generation"
      config: {...}
```

#### 9. Delay (`delay`)

```yaml
type: "delay"
config:
  seconds: 30                          # Delay duration in seconds
```

#### 10. Script (`script`)

```yaml
type: "script"
config:
  language: "python"                   # Script language
  script: |                           # Script content
    result = {"processed": True}
    print(f"Processing complete")
```

#### 11. Notification (`notification`)

```yaml
type: "notification"
config:
  type: "slack"                        # email|slack|webhook
  message: "Workflow ${workflow_name} completed"
  webhook_url: "https://hooks.slack.com/..."  # For webhook notifications
```

#### 12. Cleanup (`cleanup`)

```yaml
type: "cleanup"
config:
  variables: ["temp_data", "cache"]    # Variables to remove
```

## API Collection Testing

### Postman Collection Format

JsonAI can import standard Postman collection files:

```json
{
  "info": {
    "name": "My API Collection",
    "description": "Collection description"
  },
  "variable": [
    {"key": "baseUrl", "value": "https://api.example.com"}
  ],
  "item": [
    {
      "name": "Get Users",
      "request": {
        "method": "GET",
        "url": {
          "raw": "{{baseUrl}}/users",
          "host": ["{{baseUrl}}"],
          "path": ["users"]
        },
        "header": [
          {"key": "Accept", "value": "application/json"}
        ]
      }
    }
  ]
}
```

### OpenAPI Specification Support

JsonAI can also import OpenAPI 3.0 specifications:

```yaml
openapi: 3.0.0
info:
  title: My API
  version: 1.0.0
servers:
  - url: https://api.example.com
paths:
  /users:
    get:
      operationId: getUsers
      responses:
        '200':
          description: Success
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/User'
    post:
      operationId: createUser
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/UserInput'
      responses:
        '201':
          description: Created
components:
  schemas:
    User:
      type: object
      properties:
        id: {type: integer}
        name: {type: string}
        email: {type: string}
    UserInput:
      type: object
      properties:
        name: {type: string}
        email: {type: string}
      required: [name, email]
```

## CLI Command Reference

### Workflow Commands

```bash
# Create workflow from file
jsonai workflow create workflow.yaml

# Run workflow
jsonai workflow run workflow_name

# Run with variables
jsonai workflow run workflow_name --variables '{"env": "prod"}'
jsonai workflow run workflow_name --variables-file vars.json

# List workflows
jsonai workflow list

# Check execution status
jsonai workflow status <execution_id>

# Schedule workflow
jsonai workflow schedule workflow_name --type daily --time "09:00"
```

### API Testing Commands

```bash
# Import collections
jsonai test import-collection --source postman collection.json
jsonai test import-collection --source openapi api_spec.yaml

# Run tests
jsonai test run-collection <collection_id>
jsonai test run-collection <collection_id> --environment staging

# Generate reports
jsonai test report --format html --output report.html
jsonai test report --format json --output report.json
jsonai test report --format junit --output results.xml
```

### Data Generation Commands

```bash
# Basic generation
jsonai generate --schema schema.json --prompt "Generate data"

# Multiple items
jsonai generate --schema schema.json --prompt "Generate data" --count 100

# Different formats
jsonai generate --schema schema.json --prompt "Generate data" --output-format yaml

# Output to file
jsonai generate --schema schema.json --prompt "Generate data" --output data.json

# Use Ollama backend
jsonai generate --schema schema.json --prompt "Generate data" --use-ollama --ollama-model mistral:latest
```

### Data Validation Commands

```bash
# Validate data against schema
jsonai data validate data.json schema.json

# Transform data
jsonai data transform data.json transform_config.yaml --output transformed.json
```

### Utility Commands

```bash
# Initialize new project
jsonai utils init my_project --type full

# Validate workflow
jsonai utils validate-workflow workflow.yaml

# Validate schema
jsonai generate-schema --description "User profile with name, email, and age"
```

### Server Commands

```bash
# Start API server
jsonai server start --host 0.0.0.0 --port 8000

# Start with multiple workers
jsonai server start --workers 4
```

## Integration Examples

### CI/CD Integration

#### GitHub Actions

```yaml
name: API Testing Workflow
on: [push, pull_request]

jobs:
  api-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
          
      - name: Install JsonAI
        run: pip install jsonai
        
      - name: Run API Tests
        run: |
          jsonai test import-collection --source postman tests/api_collection.json
          jsonai test run-collection <collection_id> --environment staging
          
      - name: Generate Test Report
        run: |
          jsonai test report --format junit --output test-results.xml
          
      - name: Upload Test Results
        uses: actions/upload-artifact@v2
        with:
          name: test-results
          path: test-results.xml
```

#### Jenkins Pipeline

```groovy
pipeline {
    agent any
    
    stages {
        stage('API Testing') {
            steps {
                script {
                    sh 'pip install jsonai'
                    sh 'jsonai workflow run api_testing_workflow'
                    sh 'jsonai test report --format html --output test_report.html'
                }
            }
        }
    }
    
    post {
        always {
            publishHTML([
                allowMissing: false,
                alwaysLinkToLastBuild: true,
                keepAll: true,
                reportDir: '.',
                reportFiles: 'test_report.html',
                reportName: 'API Test Report'
            ])
        }
    }
}
```

### Docker Integration

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install JsonAI
RUN pip install jsonai

# Copy workflow and collection files
COPY workflows/ ./workflows/
COPY collections/ ./collections/
COPY schemas/ ./schemas/

# Set environment variables
ENV PYTHONPATH=/app

# Run workflow
CMD ["jsonai", "workflow", "run", "api_testing_workflow"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  jsonai-server:
    image: jsonai:latest
    ports:
      - "8000:8000"
    environment:
      - JSONAI_MODEL_BACKEND=ollama
      - OLLAMA_HOST=http://ollama:11434
    command: jsonai server start --host 0.0.0.0 --port 8000
    
  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
      
  workflow-runner:
    image: jsonai:latest
    volumes:
      - ./workflows:/app/workflows
      - ./collections:/app/collections
    environment:
      - JSONAI_API_URL=http://jsonai-server:8000
    command: jsonai workflow run scheduled_tests
    depends_on:
      - jsonai-server

volumes:
  ollama_data:
```

## Best Practices

### 1. Workflow Design

- **Modular Steps**: Keep steps small and focused on single tasks
- **Error Handling**: Always define error handling strategies
- **Variable Management**: Use meaningful variable names and proper scoping
- **Dependencies**: Clearly define step dependencies to ensure proper execution order

### 2. API Testing

- **Data Validation**: Always validate API responses against schemas
- **Environment Management**: Use environment-specific configurations
- **Test Data**: Generate realistic test data for better coverage
- **Reporting**: Generate comprehensive reports for stakeholder review

### 3. Performance Optimization

- **Parallel Execution**: Use parallel steps when operations are independent
- **Caching**: Leverage JsonAI's built-in caching for repeated operations
- **Batch Processing**: Use batch operations for multiple similar requests
- **Timeouts**: Set appropriate timeouts for long-running operations

### 4. Security Considerations

- **Sensitive Data**: Never hardcode secrets in workflow files
- **Environment Variables**: Use environment variables for sensitive configuration
- **Access Control**: Implement proper authentication for API testing
- **Data Sanitization**: Sanitize generated test data before using in production environments

## Troubleshooting

### Common Issues

#### 1. Workflow Execution Failures

```bash
# Check workflow logs
jsonai workflow status <execution_id>

# Validate workflow configuration
jsonai utils validate-workflow workflow.yaml

# Test individual steps
jsonai generate --schema step_schema.json --prompt "test"
```

#### 2. API Collection Import Issues

```bash
# Verify collection format
jsonai test validate-collection collection.json

# Check for missing dependencies
pip install aiohttp pydantic

# Test with dummy backend
jsonai generate --schema test_schema.json --prompt "test" --model dummy
```

#### 3. Model Backend Issues

```bash
# Test Ollama connection
curl http://localhost:11434/api/tags

# Use dummy backend for testing
jsonai generate --schema schema.json --prompt "test" --model dummy

# Check model availability
jsonai models list
```

### Performance Issues

#### 1. Slow Generation

- Use smaller, optimized models for testing
- Implement caching for repeated requests
- Use batch processing for multiple items
- Optimize JSON schemas to be more specific

#### 2. Memory Issues

- Reduce batch sizes for large datasets
- Implement cleanup steps in workflows
- Use streaming for large responses
- Monitor memory usage during execution

### Debug Mode

Enable debug mode for detailed logging:

```bash
# Enable debug in CLI
jsonai generate --schema schema.json --prompt "test" --debug

# Enable debug in workflow
jsonai workflow run workflow_name --variables '{"debug": true}'
```

## Advanced Features

### Custom Step Types

Create custom step executors:

```python
from jsonAI.enhanced_workflow_engine import WorkflowEngine, WorkflowStepType

class CustomWorkflowEngine(WorkflowEngine):
    def __init__(self):
        super().__init__()
        self.step_executors[WorkflowStepType.CUSTOM] = self._execute_custom_step
    
    async def _execute_custom_step(self, step, execution):
        # Custom step implementation
        return {"result": "custom_step_completed"}
```

### Plugin Development

Create JsonAI plugins:

```python
from jsonAI.plugin_system import PluginRegistry

class MyPlugin:
    def __init__(self):
        self.name = "my_plugin"
    
    def execute(self, config):
        # Plugin implementation
        return {"status": "success"}

# Register plugin
registry = PluginRegistry()
registry.register_plugin(MyPlugin())
```

### Custom Backends

Implement custom model backends:

```python
from jsonAI.model_backends import ModelBackend

class CustomBackend(ModelBackend):
    def __init__(self, config):
        self.config = config
    
    def generate(self, prompt, schema):
        # Custom generation logic
        return {"generated": "data"}
```

## Support and Contributing

### Getting Help

- **Documentation**: [GitHub Repository](https://github.com/kishoretvk/jsonAI)
- **Issues**: Report bugs and feature requests on GitHub
- **Community**: Join discussions in GitHub Discussions

### Contributing

1. Fork the repository
2. Create a feature branch
3. Implement your changes
4. Add tests for new features
5. Submit a pull request

### Development Setup

```bash
git clone https://github.com/kishoretvk/jsonAI.git
cd jsonAI
pip install -e ".[dev]"
pytest tests/
```

This enhanced version of JsonAI provides a comprehensive platform for workflow automation and API testing, making it suitable for enterprise use cases and complex automation scenarios.