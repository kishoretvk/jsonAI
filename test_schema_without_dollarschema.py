import json
from jsonschema import validate, ValidationError

with open("examples/stripe_schemas/tax_rates_metadata.schema.json") as f:
    schema = json.load(f)

# Remove $schema if present
schema.pop("$schema", None)

# Minimal valid data for this schema
data = {
    "tax_rate_id": "txr_123",
    "key": "region",
    "value": "US"
}

try:
    validate(instance=data, schema=schema)
    print("Validation succeeded without $schema.")
except ValidationError as e:
    print("Validation failed:", e)
