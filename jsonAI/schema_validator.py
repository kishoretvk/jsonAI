from jsonschema import validate, ValidationError


class SchemaValidator:
    def validate(self, data, schema):
        try:
            validate(instance=data, schema=schema)
            return True
        except ValidationError as e:
            print(f"Validation error: {e.message}")
            return False
