from typing import Dict, Any
import json
from jsonAI.model_backends import ModelBackend
from jsonschema import validate as jsonschema_validate, ValidationError

class SchemaGenerator:
    """
    A class for generating JSON schemas based on textual descriptions using a model backend.
    """

    def __init__(self, model_backend: ModelBackend):
        """
        Initialize the SchemaGenerator.

        Args:
            model_backend (ModelBackend): The model backend to use for schema generation.
        """
        self.model_backend = model_backend

    def generate_schema(self, description: str, max_new_tokens: int = 500, temperature: float = 0.3) -> Dict[str, Any]:
        """
        Generate a JSON schema from a textual description.

        Args:
            description (str): The textual description to convert into a JSON schema.
            max_new_tokens (int): Maximum number of tokens to generate.
            temperature (float): Sampling temperature for the model.

        Returns:
            Dict[str, Any]: The generated JSON schema.

        Raises:
            ValueError: If the model's response is not valid JSON.
        """
        prompt = f"""Convert the following description to a valid JSON Schema:

        Description:
        {description}

        Output ONLY the JSON Schema without any additional text or explanations.
        The output must be valid JSON that can be parsed by Python's json.loads().
        """

        schema_str = self.model_backend.generate(
            prompt,
            max_new_tokens=max_new_tokens,
            temperature=temperature
        )

        schema_str = self._clean_response(schema_str)

        try:
            return json.loads(schema_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON response: {e}")

    def _clean_response(self, response: str) -> str:
        """
        Clean up the model's response to extract the JSON schema.

        Args:
            response (str): The raw response from the model.

        Returns:
            str: The cleaned JSON schema string.
        """
        if '```json' in response:
            response = response.split('```json')[1].split('```')[0]
        elif '```' in response:
            response = response.split('```')[1].split('```')[0]
        return response.strip()

    def validate(self, schema: Dict[str, Any], data: Any) -> bool:
        """
        Validate data against a JSON schema.

        Args:
            schema (Dict[str, Any]): The JSON schema to validate against.
            data (Any): The data to validate.

        Returns:
            bool: True if the data is valid, False otherwise.

        Raises:
            ValidationError: If the data does not conform to the schema.
        """
        try:
            jsonschema_validate(data, schema)
            return True
        except ValidationError as e:
            return False
