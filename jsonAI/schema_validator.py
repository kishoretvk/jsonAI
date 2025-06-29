from jsonschema import validate, ValidationError


class SchemaValidator:
    """
    A class for validating data against JSON schemas.
    """

    def validate(self, data, schema, raise_on_error: bool = False) -> bool:
        """
        Validate data against a JSON schema.

        Args:
            data (dict): The data to validate.
            schema (dict): The JSON schema to validate against.
            raise_on_error (bool): Whether to raise an exception on validation error.

        Returns:
            bool: True if validation succeeds, False otherwise.

        Raises:
            ValidationError: If validation fails and `raise_on_error` is True.
        """
        try:
            validate(instance=data, schema=schema)
            return True
        except ValidationError as e:
            error_message = f"Validation error: {e.message}\nContext: {e.context}\nPath: {list(e.path)}"
            if raise_on_error:
                raise ValidationError(error_message) from e
            else:
                print(error_message)
                return False
