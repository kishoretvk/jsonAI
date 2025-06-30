# JSON Schema Support in jsonAI

jsonAI supports advanced JSON Schema features, including:

- **Basic Types**: string, number, integer, boolean, null.
- **Complex Types**: object, array.
- **Combinators**: oneOf, anyOf, allOf.
- **Custom Formats**: email, uuid, date, datetime, binary.

## Combinators

### oneOf
Allows validation against one schema from a list.

Example:
```json
{
  "oneOf": [
    {"type": "string"},
    {"type": "integer"}
  ]
}
```

Use Case:
- Validating user input that can be either a string or an integer.

### anyOf
Allows validation against any schema from a list.

Example:
```json
{
  "anyOf": [
    {"type": "string"},
    {"type": "integer"}
  ]
}
```

Use Case:
- Accepting multiple data types for flexible API design.

### allOf
Requires validation against all schemas in a list.

Example:
```json
{
  "allOf": [
    {"type": "object", "properties": {"name": {"type": "string"}}},
    {"type": "object", "properties": {"age": {"type": "integer"}}}
  ]
}
```

Use Case:
- Combining multiple constraints for complex data validation.

## Custom Formats

### email
Validates email addresses.

Example:
```json
{
  "type": "string",
  "format": "email"
}
```

### uuid
Validates UUIDs.

Example:
```json
{
  "type": "string",
  "format": "uuid"
}
```

### datetime
Validates ISO 8601 datetime strings.

Example:
```json
{
  "type": "string",
  "format": "datetime"
}
```

## Best Practices

- Use `oneOf` for mutually exclusive options.
- Use `anyOf` for flexible validation.
- Use `allOf` for combining constraints.
- Leverage custom formats for standardized data types.
