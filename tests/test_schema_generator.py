import unittest
from unittest.mock import Mock
from jsonAI.schema_generator import SchemaGenerator
from jsonAI.model_backends import ModelBackend

class TestSchemaGenerator(unittest.TestCase):
    def setUp(self):
        mock_backend = Mock(spec=ModelBackend)
        self.generator = SchemaGenerator(model_backend=mock_backend)

    def test_oneOf(self):
        schema = {
            "oneOf": [
                {"type": "string"},
                {"type": "integer"}
            ]
        }
        result = self.generator.validate(schema, "test")
        self.assertTrue(result)

    def test_anyOf(self):
        schema = {
            "anyOf": [
                {"type": "string"},
                {"type": "integer"}
            ]
        }
        result = self.generator.validate(schema, 123)
        self.assertTrue(result)

    def test_allOf(self):
        schema = {
            "allOf": [
                {"type": "object", "properties": {"name": {"type": "string"}}},
                {"type": "object", "properties": {"age": {"type": "integer"}}}
            ]
        }
        data = {"name": "Alice", "age": 30}
        result = self.generator.validate(schema, data)
        self.assertTrue(result)

    def test_custom_format_email(self):
        schema = {"type": "string", "format": "email"}
        result = self.generator.validate(schema, "test@example.com")
        self.assertTrue(result)

    def test_custom_format_uuid(self):
        schema = {"type": "string", "format": "uuid"}
        result = self.generator.validate(schema, "123e4567-e89b-12d3-a456-426614174000")
        self.assertTrue(result)

    def test_custom_format_datetime(self):
        schema = {"type": "string", "format": "datetime"}
        result = self.generator.validate(schema, "2023-01-01T12:00:00Z")
        self.assertTrue(result)

if __name__ == "__main__":
    unittest.main()
