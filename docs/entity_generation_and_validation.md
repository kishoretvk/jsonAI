# Entity Generation Configuration (EGC) and Validation in jsonAI

## Overview

jsonAI supports robust, schema-driven entity generation and validation. This system allows users to:
- Automatically generate realistic values for common entities (email, phone, SSN, etc.)
- Validate generated values using built-in or custom rules
- Override or extend generation/validation logic per field, type, or globally
- Configure fallback, skip-validation, and max-attempts options

## How It Works

- For supported schema types/formats, jsonAI uses the EGC registry to generate values and the validation registry to check them.
- If generation fails validation, fallback and retry strategies are applied.
- Users can override defaults or skip validation as needed.

## Usage

### Default Behavior

For a schema field with a recognized format (e.g., `"format": "email"`), jsonAI will:
1. Use the corresponding EGC to generate a value.
2. Validate the value using the corresponding rule.
3. Retry or fallback if validation fails.

### User Overrides

You can override generation or validation logic by:
- Registering a custom EGC or validation rule for a specific type/format.
- Passing user_overrides or skip_validation options to the generation controller.

### Example

```python
from jsonAI.entity_generation import EntityGenerationController, EntityGenerationRegistry
from jsonAI.validation_rules import ValidationRuleRegistry

# Custom generation config for email
class MyEmailGen:
    name = "email"
    description = "Always generates test@example.com"
    def generate(self):
        return "test@example.com"

EntityGenerationRegistry.register(MyEmailGen())

controller = EntityGenerationController(
    registry=EntityGenerationRegistry,
    validation_registry=ValidationRuleRegistry,
    user_overrides={"email": MyEmailGen()},
    skip_validation=False,
    max_attempts=3,
)

value = controller.generate("email")
print(value)  # "test@example.com"
```

### Skipping Validation

Set `skip_validation=True` in the controller to bypass validation for all generations.

### Extending

To add support for new entity types, subclass `BaseEntityGenerationConfig` or `BaseValidationRule` and register your class.

## Configuration Options

- **user_overrides**: Dict of entity type to custom generation config
- **skip_validation**: Bool, skip validation if True
- **max_attempts**: Int, number of retries before fallback/error

## Integration

EGC and validation are integrated into the main jsonAI pipeline. All schema-driven generation will use these systems by default.

## Advanced

- You can expose these options via config files or schema extensions for end users.
- See the codebase for more advanced hooks and fallback strategies.
