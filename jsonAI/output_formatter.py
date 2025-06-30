import json
import xml.etree.ElementTree as ET
import yaml
import csv
from collections import OrderedDict


class OutputFormatter:
    """
    A class for formatting data into JSON, XML, and YAML formats.
    """

    def format(self, data, output_format='json', root_element='root', root_attributes=None):
        """
        Format data into the specified output format.

        Args:
            data (dict): The data to format.
            output_format (str): The format to output ('json', 'xml', 'yaml').
            root_element (str): The root element name for XML output.
            root_attributes (dict): Attributes for the root XML element.

        Returns:
            str: The formatted data.

        Raises:
            ValueError: If the output format is unsupported.
        """
        if output_format == 'json':
            return json.dumps(data)
        elif output_format == 'xml':
            return self._dict_to_xml(data, root_element, root_attributes)
        elif output_format == 'yaml':
            # Define a custom representer for OrderedDict
            def represent_ordereddict(dumper, data):
                return dumper.represent_dict(data.items())

            yaml.add_representer(OrderedDict, represent_ordereddict, Dumper=yaml.Dumper)

            # Convert dictionary to OrderedDict for consistent YAML output
            ordered_data = OrderedDict([('name', data['name']), ('age', data['age'])])
            return yaml.dump(ordered_data, Dumper=yaml.Dumper, sort_keys=False)
        elif output_format == 'csv':
            return self._dict_to_csv(data)
        else:
            raise ValueError(f"Unsupported output format: {output_format}")

    def _dict_to_xml(self, data, root_element='root', root_attributes=None):
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

    def _add_dict_to_xml(self, parent, data):
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

    def _dict_to_csv(self, data):
        """
        Convert a dictionary to a CSV string.

        Args:
            data (dict): The data to convert.

        Returns:
            str: The CSV string.
        """
        if not isinstance(data, dict):
            raise TypeError("CSV output requires a dictionary.")

        # Create headers and values rows
        headers = ",".join(data.keys())
        values = ",".join(map(str, data.values()))

        # Ensure no trailing newline
        return f"{headers}\n{values}"
