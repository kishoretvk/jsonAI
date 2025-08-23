"""
Example script demonstrating Ollama integration with JsonAI.

This example shows how to use JsonAI with Ollama for structured data generation,
including workflow orchestration, state management, and tracing.
"""

import asyncio
import tempfile
import os
from jsonAI.main import Jsonformer
from jsonAI.model_backends import OllamaBackend
from jsonAI.workflow_orchestrator import WorkflowStep, WorkflowStepType
from jsonAI.state_manager import StateManager
from jsonAI.persistent_storage import SQLiteStorage
from jsonAI.tracing import get_tracer
from jsonAI.ollama_utils import OllamaModelSelector, OllamaPerformanceTuner


def basic_ollama_example():
    """Basic example of using JsonAI with Ollama."""
    print("=== Basic Ollama Example ===")
    
    # Create Ollama backend (make sure Ollama is running with mistral model)
    backend = OllamaBackend(model_name="mistral")
    
    # Define a simple schema
    schema = {
        "type": "object",
        "properties": {
            "product_name": {"type": "string"},
            "price": {"type": "number"},
            "in_stock": {"type": "boolean"}
        }
    }
    
    # Create prompt
    prompt = "Generate information about a fictional product"
    
    # Create Jsonformer
    jsonformer = Jsonformer(
        model_backend=backend,
        json_schema=schema,
        prompt=prompt,
        ollama_options={
            "temperature": 0.7,
            "repeat_penalty": 1.2
        },
        debug=True
    )
    
    try:
        # Generate data
        result = jsonformer.generate_data()
        print(f"Generated product: {result}")
        return result
    except Exception as e:
        print(f"Error generating data: {e}")
        return None


def advanced_ollama_workflow_example():
    """Advanced example with workflow orchestration."""
    print("\n=== Advanced Ollama Workflow Example ===")
    
    # Create tracer
    tracer = get_tracer("ollama-workflow-example")
    
    with tracer.start_span("advanced_ollama_workflow") as workflow_span:
        # Create Ollama backend
        backend = OllamaBackend(model_name="mistral", max_retries=2)
        
        # Define schema
        user_schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "email": {"type": "string", "format": "email"},
                "preferences": {
                    "type": "object",
                    "properties": {
                        "newsletter": {"type": "boolean"},
                        "sms_alerts": {"type": "boolean"}
                    }
                }
            }
        }
        
        # Define workflow configuration
        workflow_config = {
            "steps": [
                {
                    "id": "user_generation",
                    "name": "Generate User Profile",
                    "type": "generation",
                    "config": {
                        "prompt": "Generate a realistic user profile for a tech product",
                        "schema": user_schema
                    },
                    "dependencies": []
                },
                {
                    "id": "validation",
                    "name": "Validate User Profile",
                    "type": "condition",
                    "config": {
                        "expression": "result.get('name') and '@' in result.get('email', '')"
                    },
                    "dependencies": ["user_generation"]
                }
            ]
        }
        
        tracer.add_event(workflow_span, "created_workflow")
        
        # Create Jsonformer with workflow
        jsonformer = Jsonformer(
            model_backend=backend,
            json_schema=user_schema,
            prompt="Generate user profiles",
            workflow_config=workflow_config,
            ollama_options={
                "temperature": 0.6,
                "top_p": 0.9
            },
            debug=True
        )
        
        tracer.add_event(workflow_span, "created_jsonformer")
        
        # Execute workflow
        async def run_workflow():
            return await jsonformer.execute_workflow()
            
        try:
            result = asyncio.run(run_workflow())
            tracer.add_event(workflow_span, "workflow_completed")
            print(f"Workflow result: {result}")
            return result
        except Exception as e:
            tracer.add_event(workflow_span, f"workflow_failed: {str(e)}")
            print(f"Workflow failed: {e}")
            return None


def ollama_model_selection_example():
    """Example of automatic model selection and tuning."""
    print("\n=== Ollama Model Selection Example ===")
    
    # Create model selector and tuner
    selector = OllamaModelSelector()
    tuner = OllamaPerformanceTuner(selector)
    
    # Get available models
    available_models = selector.get_available_models()
    print(f"Available models: {available_models}")
    
    # Select best model for JSON generation
    best_model = selector.select_best_model("json_generation")
    print(f"Selected model for JSON generation: {best_model}")
    
    # Get recommended parameters
    params = selector.get_model_parameters(best_model, "json_generation")
    print(f"Recommended parameters: {params}")
    
    # Tune for specific task
    task_schema = {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "content": {"type": "string"},
            "tags": {
                "type": "array",
                "items": {"type": "string"}
            }
        }
    }
    
    model_name, tuned_params = tuner.tune_for_task(
        "Generate blog post metadata",
        "Generate metadata for a technical blog post",
        task_schema
    )
    
    print(f"Tuned model: {model_name}")
    print(f"Tuned parameters: {tuned_params}")
    
    # Use the tuned configuration
    backend = OllamaBackend(model_name=model_name)
    jsonformer = Jsonformer(
        model_backend=backend,
        json_schema=task_schema,
        prompt="Generate metadata for a technical blog post",
        ollama_options=tuned_params,
        debug=True
    )
    
    try:
        result = jsonformer.generate_data()
        print(f"Generated blog post metadata: {result}")
        return result
    except Exception as e:
        print(f"Error generating blog post metadata: {e}")
        return None


def main():
    """Run all examples."""
    print("JsonAI Ollama Integration Examples")
    print("===================================")
    
    # Run basic example
    basic_result = basic_ollama_example()
    
    # Run advanced workflow example
    workflow_result = advanced_ollama_workflow_example()
    
    # Run model selection example
    selection_result = ollama_model_selection_example()
    
    print("\n=== Summary ===")
    print(f"Basic example result: {'Success' if basic_result else 'Failed'}")
    print(f"Workflow example result: {'Success' if workflow_result else 'Failed'}")
    print(f"Model selection example result: {'Success' if selection_result else 'Failed'}")


if __name__ == "__main__":
    main()