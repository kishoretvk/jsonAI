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
        self.assertEqual(result, "name,age\nAlice,30")

    def test_format_edge_case(self):
        data = {"name": "Alice", "age": None}
        result = self.formatter.format(data, "json")
        self.assertEqual(result, '{"name": "Alice", "age": null}')

if __name__ == "__main__":
    unittest.main()
