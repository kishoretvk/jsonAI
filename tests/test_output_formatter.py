import unittest
from jsonAI.output_formatter import OutputFormatter

class TestOutputFormatter(unittest.TestCase):
    def setUp(self):
        self.formatter = OutputFormatter()

    def test_format_json(self):
        data = {"name": "Alice", "age": 30}
        result = self.formatter.format(data, "json")
        self.assertEqual(result, '{"name": "Alice", "age": 30}')

    def test_format_xml(self):
        data = {"name": "Alice", "age": 30}
        result = self.formatter.format(data, "xml")
        self.assertEqual(result, '<root><name>Alice</name><age>30</age></root>')

    def test_format_yaml(self):
        data = {"name": "Alice", "age": 30}
        result = self.formatter.format(data, "yaml")
        self.assertEqual(result, "name: Alice\nage: 30\n")

    def test_format_csv(self):
        data = {"name": "Alice", "age": 30}
        result = self.formatter.format(data, "csv")
        normalized = result.replace("\r\n", "\n").strip()
        self.assertEqual(normalized, "name,age\nAlice,30")

    def test_format_edge_case(self):
        data = {"name": "Alice", "age": None}
        result = self.formatter.format(data, "json")
        self.assertEqual(result, '{"name": "Alice", "age": null}')

    def test_format_csv_list_of_dicts(self):
        data = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]
        result = self.formatter.format(data, "csv")
        normalized = result.replace("\r\n", "\n").strip()
        self.assertIn("name,age", normalized)
        self.assertIn("Alice,30", normalized)
        self.assertIn("Bob,25", normalized)

    def test_format_yaml_nested(self):
        data = {"person": {"name": "Alice", "age": 30, "skills": ["python", "ai"]}}
        result = self.formatter.format(data, "yaml")
        self.assertIn("person:", result)
        self.assertIn("skills:", result)

    def test_format_xml_nested(self):
        data = {"person": {"name": "Alice", "age": 30, "skills": ["python", "ai"]}}
        result = self.formatter.format(data, "xml")
        self.assertIn("<person>", result)
        self.assertIn("<skills>", result)

    def test_format_csv_with_schema(self):
        data = {"name": "Alice", "age": 30, "extra": "ignore"}
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"}
            }
        }
        result = self.formatter._dict_to_csv(data, schema)
        normalized = result.replace("\r\n", "\n").strip()
        self.assertEqual(normalized, "name,age\nAlice,30")

    def test_format_unsupported(self):
        data = {"name": "Alice"}
        with self.assertRaises(ValueError):
            self.formatter.format(data, "unsupported")

if __name__ == "__main__":
    unittest.main()
