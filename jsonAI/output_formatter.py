import json
import xml.etree.ElementTree as ET
import yaml
import csv
from collections import OrderedDict
from typing import Any, Union

try:
    import pandas as pd
    _HAS_PANDAS = True
except ImportError:
    _HAS_PANDAS = False

class OutputFormatter:
    """
    A class for formatting data into JSON, XML, and YAML formats.
    """

    def format(
        self,
        data: Union[dict[str, Any], list[dict[str, Any]]],
        output_format: str = 'json',
        root_element: str = 'root',
        root_attributes: Union[dict[str, Any], None] = None,
        schema: Union[dict[str, Any], None] = None,
    ) -> str:
        """
        Format data into the specified output format, with optional schema-driven validation.

        Args:
            data (dict or list): The data to format.
            output_format (str): The format to output ('json', 'xml', 'yaml', 'csv').
            root_element (str): The root element name for XML output.
            root_attributes (dict): Attributes for the root XML element.
            schema (dict): Optional schema for validation and structure.

        Returns:
            str: The formatted data.

        Raises:
            ValueError: If the output format is unsupported or validation fails.
        """
        if output_format == 'json':
            return json.dumps(data)
        elif output_format == 'xml':
            return self._dict_to_xml(data, root_element, root_attributes)
        elif output_format == 'yaml':
            return yaml.dump(data, Dumper=yaml.Dumper, sort_keys=False)
        elif output_format == 'csv':
            return self._dict_to_csv(data)
        else:
            raise ValueError(f"Unsupported output format: {output_format}")

    def sanitize_primitive(self, value: Any, schema_type: str, enum_values=None) -> Any:
        """
        Sanitize a primitive value to ensure it is valid JSON for the given schema type.
        - Wraps unquoted strings.
        - Converts Python None to JSON null.
        - Ensures enums are quoted and valid.
        """
        if schema_type == "string":
            if isinstance(value, str):
                # If already quoted as JSON, return as is
                try:
                    parsed = json.loads(value)
                    if isinstance(parsed, str):
                        return parsed
                except Exception:
                    pass
                # Otherwise, wrap as JSON string
                return value
            elif value is None:
                return ""
            else:
                return str(value)
        if schema_type == "number":
            try:
                return float(value)
            except Exception:
                return 0.0
        if schema_type == "integer":
            try:
                return int(float(value))
            except Exception:
                return 0
        if schema_type == "boolean":
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                if value.lower() in ["true", "1"]:
                    return True
                if value.lower() in ["false", "0"]:
                    return False
            return bool(value)
        if schema_type == "null":
            print(f"[DEBUG] sanitize_primitive: value={repr(value)}, schema_type={schema_type}")
            if value is None:
                return None
            if isinstance(value, str):
                cleaned = value.strip().strip('"\'').strip().lower()
                print(f"[DEBUG] cleaned value for null: {repr(cleaned)}")
                if cleaned in ("none", "null"):
                    return None
            return None
        if schema_type == "enum" and enum_values:
            # Accept only valid enum values, as string
            if value in enum_values:
                return value
            # Try to coerce
            if isinstance(value, str):
                for ev in enum_values:
                    if value.strip('"\'') == ev:
                        return ev
            return enum_values[0]
        return value

    def _dict_to_xml(
        self,
        data: dict[str, Any],
        root_element: str = 'root',
        root_attributes: Union[dict[str, Any], None] = None
    ) -> str:
        """
        Convert a dictionary to an XML string.

        Args:
            data (dict): The data to convert.
            root_element (str): The root element name.
            root_attributes (dict): Attributes for the root XML element.

        Returns:
            str: The XML string.
        """
        root = ET.Element(root_element)
        if root_attributes:
            for attr_key, attr_value in root_attributes.items():
                root.set(attr_key, attr_value)
        self._add_dict_to_xml(root, data)
        return ET.tostring(root, encoding='unicode')

    def _add_dict_to_xml(
        self,
        parent: ET.Element,
        data: object
    ) -> None:
        """
        Recursively add dictionary data to an XML element.

        Args:
            parent (xml.etree.ElementTree.Element): The parent XML element.
            data (any): The data to add.

        Raises:
            TypeError: If the data type is unsupported.
        """
        if isinstance(data, dict):
            for key, value in data.items():
                element = ET.SubElement(parent, key)
                self._add_dict_to_xml(element, value)
        elif isinstance(data, list):
            for item in data:
                element = ET.SubElement(parent, 'item')
                self._add_dict_to_xml(element, item)
        elif isinstance(data, (str, int, float, bool)) or data is None:
            parent.text = str(data) if data is not None else ''
        else:
            raise TypeError(f"Unsupported data type: {type(data)}")

    def _dict_to_csv(self, data: Union[dict[str, Any], list[dict[str, Any]]], schema: Union[dict[str, Any], None] = None) -> str:
        """
        Convert a dictionary or list of dicts to a CSV string.
        Uses pandas if available for tabular data.
        Optionally validates columns against schema.

        Args:
            data (dict or list): The data to convert.
            schema (dict): Optional schema for column validation.

        Returns:
            str: The CSV string.
        """
        # Determine expected columns from schema if provided
        expected_columns = None
        if schema is not None:
            if schema.get("type") == "array" and "items" in schema and "properties" in schema["items"]:
                expected_columns = list(schema["items"]["properties"].keys())
            elif schema.get("type") == "object" and "properties" in schema:
                expected_columns = list(schema["properties"].keys())

        # Use pandas for tabular data if available
        if _HAS_PANDAS:
            if isinstance(data, list):
                if all(isinstance(row, dict) for row in data):
                    df = pd.DataFrame(data)
                    if expected_columns:
                        df = df[expected_columns]
                    return df.to_csv(index=False)
            elif isinstance(data, dict):
                # If dict of lists, treat as columns
                if all(isinstance(v, list) for v in data.values()):
                    df = pd.DataFrame(data)
                    if expected_columns:
                        df = df[expected_columns]
                    return df.to_csv(index=False)
                # Otherwise, treat as single row
                df = pd.DataFrame([data])
                if expected_columns:
                    df = df[expected_columns]
                return df.to_csv(index=False)
        # Fallback: original logic for flat dicts
        if isinstance(data, dict):
            if expected_columns:
                headers = ",".join(expected_columns)
                values = ",".join(str(data.get(col, "")) for col in expected_columns)
            else:
                headers = ",".join(data.keys())
                values = ",".join(map(str, data.values()))
            return f"{headers}\n{values}"
        raise TypeError("CSV output requires a dictionary or list of dictionaries.")
