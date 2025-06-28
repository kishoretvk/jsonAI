import json
import xml.etree.ElementTree as ET
import yaml


class OutputFormatter:
    def format(self, data, output_format='json'):
        if output_format == 'json':
            return json.dumps(data)
        elif output_format == 'xml':
            return self._dict_to_xml(data)
        elif output_format == 'yaml':
            return yaml.dump(data)
        else:
            raise ValueError(f"Unsupported output format: {output_format}")

    def _dict_to_xml(self, data, root_element='root'):
        root = ET.Element(root_element)
        self._add_dict_to_xml(root, data)
        return ET.tostring(root, encoding='unicode')

    def _add_dict_to_xml(self, parent, data):
        if isinstance(data, dict):
            for key, value in data.items():
                element = ET.SubElement(parent, key)
                self._add_dict_to_xml(element, value)
        elif isinstance(data, list):
            for item in data:
                element = ET.SubElement(parent, 'item')
                self._add_dict_to_xml(element, item)
        else:
            parent.text = str(data)
