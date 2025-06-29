from typing import Dict, Any
import json
from jsonAI.model_backends import ModelBackend

class SchemaGenerator:
    def __init__(self, model_backend: ModelBackend):
        self.model_backend = model_backend
        
    def generate_schema(self, description: str) -> Dict[str, Any]:
        prompt = f"""Convert the following description to a valid JSON Schema:
        
        Description:
        {description}
        
        Output ONLY the JSON Schema without any additional text or explanations.
        The output must be valid JSON that can be parsed by Python's json.loads().
        """
        
        # Generate schema string
        schema_str = self.model_backend.generate(
            prompt,
            max_new_tokens=500,
            temperature=0.3
        )
        
        # Clean up the response
        if '```json' in schema_str:
            schema_str = schema_str.split('```json')[1].split('```')[0]
        elif '```' in schema_str:
            schema_str = schema_str.split('```')[1].split('```')[0]
        
        # Parse to JSON
        return json.loads(schema_str)
