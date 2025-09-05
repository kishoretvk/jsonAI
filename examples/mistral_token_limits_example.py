#!/usr/bin/env python3
"""
Example: Using JsonAI with local Mistral model and token limits.

This example demonstrates how to configure JsonAI for optimal performance
with smaller models like Mistral by setting appropriate token limits.
"""

import json
from jsonAI.main import Jsonformer
from jsonAI.model_backends import OllamaBackend
from jsonAI.conversational_agent import ConversationalAgentInterface

def example_mistral_user_profile():
    """Generate a user profile using Mistral with token limits."""

    # Schema for user profile
    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer", "minimum": 18, "maximum": 100},
            "email": {"type": "string"},
            "occupation": {"type": "string"},
            "bio": {"type": "string"}
        },
        "required": ["name", "age"]
    }

    # Initialize Ollama backend for Mistral
    backend = OllamaBackend(model_name="mistral:latest")

    # Create Jsonformer with optimized settings for small model
    jsonformer = Jsonformer(
        model_backend=backend,
        json_schema=schema,
        prompt="Generate a realistic user profile for a software developer",
        max_tokens=150,  # Limit tokens for better performance with Mistral
        temperature=0.7,  # Slightly creative but not too random
        debug=True
    )

    print("Generating user profile with Mistral...")
    result = jsonformer.generate_data()
    print("\nGenerated profile:")
    print(json.dumps(result, indent=2))

    return result

def example_conversational_agent():
    """Example using conversational agent with token limits."""

    # Initialize backend
    backend = OllamaBackend(model_name="mistral:latest")

    # Create agent interface
    agent_interface = ConversationalAgentInterface(backend)

    # Schema for responses
    schema = {
        "type": "object",
        "properties": {
            "response": {"type": "string"},
            "confidence": {"type": "number", "minimum": 0, "maximum": 1}
        }
    }

    # Create agent with token limits
    agent = agent_interface.create_agent(
        agent_id="mistral_assistant",
        name="Mistral Assistant",
        role="Helpful AI Assistant",
        capabilities=["answer_questions", "generate_content"],
        schema=schema,
        max_tokens=100  # Conservative token limit for small model
    )

    print(f"\nCreated agent: {agent.name}")
    print(f"Capabilities: {agent.capabilities}")
    print(f"Max tokens: {agent.jsonformer.max_tokens}")

def example_different_token_limits():
    """Demonstrate different token limits for different use cases."""

    backend = OllamaBackend(model_name="mistral:latest")

    # Simple schema - fewer tokens needed
    simple_schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"}
        }
    }

    # Complex schema - more tokens needed
    complex_schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"},
            "address": {
                "type": "object",
                "properties": {
                    "street": {"type": "string"},
                    "city": {"type": "string"},
                    "country": {"type": "string"}
                }
            },
            "hobbies": {"type": "array", "items": {"type": "string"}},
            "bio": {"type": "string"}
        }
    }

    # Simple generation - low token limit
    simple_jsonformer = Jsonformer(
        model_backend=backend,
        json_schema=simple_schema,
        prompt="Generate basic user info",
        max_tokens=50
    )

    # Complex generation - higher token limit
    complex_jsonformer = Jsonformer(
        model_backend=backend,
        json_schema=complex_schema,
        prompt="Generate detailed user profile",
        max_tokens=200
    )

    print("\nToken limit examples:")
    print(f"Simple schema max_tokens: {simple_jsonformer.max_tokens}")
    print(f"Complex schema max_tokens: {complex_jsonformer.max_tokens}")

if __name__ == "__main__":
    print("JsonAI with Mistral - Token Limits Example")
    print("=" * 50)

    try:
        example_mistral_user_profile()
        example_conversational_agent()
        example_different_token_limits()

        print("\n" + "=" * 50)
        print("Examples completed successfully!")
        print("\nKey takeaways for Mistral:")
        print("- Use max_tokens=50-150 for simple schemas")
        print("- Use max_tokens=150-300 for complex schemas")
        print("- Lower temperature (0.3-0.7) for more consistent output")
        print("- Monitor token usage to optimize performance")

    except Exception as e:
        print(f"Error running examples: {e}")
        print("Make sure Ollama is running with Mistral model:")
        print("  ollama serve")
        print("  ollama pull mistral:latest")
