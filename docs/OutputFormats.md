# Output Formats in jsonAI

jsonAI supports multiple output formats:

- **JSON**: Default format for structured data.
- **XML**: Hierarchical data representation.
- **YAML**: Human-readable data serialization.
- **CSV**: Tabular data representation.

## Examples

### JSON
```json
{
  "name": "Alice",
  "age": 30
}
```

### XML
```xml
<root>
  <name>Alice</name>
  <age>30</age>
</root>
```

### YAML
```yaml
name: Alice
age: 30
```

### CSV
```csv
name,age
Alice,30
```

## Advanced Usage

### Converting Between Formats
jsonAI provides utilities to convert data between supported formats. Example:

```python
from jsonAI.output_formatter import convert_format

# Convert JSON to YAML
json_data = {"name": "Alice", "age": 30}
yaml_data = convert_format(json_data, "yaml")
print(yaml_data)
```

### Format-Specific Notes

- **JSON**: Ideal for APIs and structured data.
- **XML**: Best for hierarchical data but verbose.
- **YAML**: Human-readable but indentation-sensitive.
- **CSV**: Suitable for tabular data but lacks hierarchy.

## Limitations and Optimizations

- Ensure proper escaping for special characters in CSV.
- Use libraries for large XML datasets to optimize performance.
- Validate YAML for indentation errors.
