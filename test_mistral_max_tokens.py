#!/usr/bin/env python3
"""
Test script for max_tokens parameter with local Mistral model.
"""

import json
from jsonAI.main import Jsonformer
from jsonAI.model_backends import OllamaBackend

def test_mistral_max_tokens():
    """Test JsonAI with max_tokens parameter for Mistral model."""

    # Schema for user profile
    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"},
            "email": {"type": "string"},
            "bio": {"type": "string"}
        },
        "required": ["name", "age"]
    }

    # Initialize Ollama backend for Mistral
    backend = OllamaBackend(model_name="mistral:latest")

    # Create Jsonformer with max_tokens limit for small model
    jsonformer = Jsonformer(
        model_backend=backend,
        json_schema=schema,
        prompt="Generate a user profile for a software developer",
        max_tokens=100,  # Limit tokens for better performance with small model
        debug=True
    )

    # Generate data
    result = jsonformer.generate_data()
    print("Generated result:")
    print(json.dumps(result, indent=2))

    return result

if __name__ == "__main__":
    test_mistral_max_tokens()
