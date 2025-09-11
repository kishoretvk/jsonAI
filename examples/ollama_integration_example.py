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
    
    # Create Ollama backend with different model and lower temperature
    backend = OllamaBackend(model_name="qwen3:0.6b")
    
    # Define a better schema with examples and constraints
    schema = {
        "type": "object",
        "properties": {
            "product_name": {
                "type": "string",
                "description": "The name of the product",
                "examples": ["Wireless Bluetooth Headphones", "Smart Fitness Tracker", "Organic Coffee Beans"]
            },
            "price": {
                "type": "number",
                "description": "Price in USD",
                "minimum": 1.99,
                "maximum": 999.99,
                "examples": [29.99, 149.99, 24.99]
            },
            "in_stock": {
                "type": "boolean",
                "description": "Whether the product is currently available"
            },
            "category": {
                "type": "string",
                "enum": ["electronics", "clothing", "books", "home", "sports"],
                "description": "Product category"
            }
        },
        "required": ["product_name", "price", "in_stock"]
    }
    
    # Create a more detailed prompt with examples
    prompt = """Generate information for a realistic e-commerce product.

    Examples of good products:
    - Product: "Wireless Bluetooth Headphones", Price: $89.99, Category: "electronics", In Stock: true
    - Product: "Organic Cotton T-Shirt", Price: $24.99, Category: "clothing", In Stock: false
    - Product: "Stainless Steel Water Bottle", Price: $19.99, Category: "sports", In Stock: true

    Create a product that would be found in an online store with a reasonable price for its category.
    Make sure the product name is descriptive and professional."""
    
    # Create Jsonformer
    jsonformer = Jsonformer(
        model_backend=backend,
        json_schema=schema,
        prompt=prompt,
        ollama_options={
            "temperature": 0.3,  # Lower temperature for more focused output
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
        backend = OllamaBackend(model_name="qwen3:0.6b", max_retries=2)
        
        # Define improved schema with examples and constraints
        user_schema = {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Full name of the user",
                    "examples": ["John Smith", "Sarah Johnson", "Michael Chen"]
                },
                "email": {
                    "type": "string",
                    "format": "email",
                    "description": "Valid email address",
                    "examples": ["john.smith@email.com", "sarah.j@email.com"]
                },
                "age": {
                    "type": "integer",
                    "description": "Age in years",
                    "minimum": 18,
                    "maximum": 80,
                    "examples": [25, 35, 42]
                },
                "preferences": {
                    "type": "object",
                    "properties": {
                        "newsletter": {
                            "type": "boolean",
                            "description": "Whether user wants to receive newsletters"
                        },
                        "sms_alerts": {
                            "type": "boolean",
                            "description": "Whether user wants SMS notifications"
                        }
                    }
                }
            },
            "required": ["name", "email", "age"]
        }
        
        # Define workflow configuration
        workflow_config = {
            "steps": [
                {
                    "id": "user_generation",
                    "name": "Generate User Profile",
                    "type": "generation",
                    "config": {
                        "prompt": """Generate a realistic user profile for a tech product website.

                        Examples of realistic user profiles:
                        - Name: "Alex Rodriguez", Email: "alex.r@email.com", Age: 28, Newsletter: true, SMS: false
                        - Name: "Maria Chen", Email: "maria.chen@techcorp.com", Age: 34, Newsletter: true, SMS: true
                        - Name: "David Kim", Email: "dkim85@gmail.com", Age: 42, Newsletter: false, SMS: true

                        Create a profile for someone who would realistically use tech products.
                        Use a realistic name, professional email, appropriate age for a tech user, and realistic subscription preferences.""",
                        "schema": user_schema
                    },
                    "dependencies": []
                },
                {
                    "id": "validation",
                    "name": "Validate User Profile",
                    "type": "condition",
                    "config": {
                        "expression": "context.get('user_generation', {}).get('name') and '@' in context.get('user_generation', {}).get('email', '')"
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
            "title": {
                "type": "string",
                "description": "An engaging title for the blog post",
                "examples": ["Getting Started with Python Async Programming", "Building REST APIs with FastAPI"]
            },
            "content": {
                "type": "string",
                "description": "The main content of the blog post",
                "examples": ["In this post, we'll explore how to use async/await in Python..."]
            },
            "tags": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Relevant tags for the blog post",
                "minItems": 2,
                "maxItems": 5,
                "examples": [["python", "async"], ["web-development", "api", "fastapi"]]
            },
            "category": {
                "type": "string",
                "enum": ["tutorial", "news", "opinion", "review"],
                "description": "The category of the blog post"
            }
        },
        "required": ["title", "content", "tags"]
    }
    
    model_name, tuned_params = tuner.tune_for_task(
        "Generate blog post metadata",
        """Generate comprehensive metadata for a technical blog post about programming or software development.

        Examples of good blog posts:
        - Title: "Mastering Async/Await in Python: A Complete Guide"
          Content: "Learn how to write efficient asynchronous code in Python using async/await patterns, with practical examples and best practices."
          Tags: ["python", "async", "concurrency", "programming"]
          Category: "tutorial"

        - Title: "FastAPI vs Django: Choosing the Right Framework"
          Content: "Compare FastAPI and Django for modern web development, analyzing performance, ease of use, and use cases."
          Tags: ["python", "web-development", "fastapi", "django", "frameworks"]
          Category: "review"

        Generate an engaging title, brief but informative content summary, relevant technical tags, and appropriate category.""",
        task_schema
    )
    
    print(f"Tuned model: {model_name}")
    print(f"Tuned parameters: {tuned_params}")
    
    # Use the tuned configuration with lower temperature
    backend = OllamaBackend(model_name="qwen3:0.6b")
    jsonformer = Jsonformer(
        model_backend=backend,
        json_schema=task_schema,
        prompt="Generate metadata for a technical blog post",
        ollama_options={
            "temperature": 0.2,  # Very low temperature for focused, relevant output
            "top_p": 0.9,
            "repeat_penalty": 1.1
        },
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