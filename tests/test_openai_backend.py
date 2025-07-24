import unittest
from unittest.mock import patch, MagicMock
from jsonAI.model_backends import OpenAIBackend
import asyncio

class TestOpenAIBackend(unittest.TestCase):
    def setUp(self):
        self.api_key = "test_api_key"  # Mock API key
        self.backend = OpenAIBackend(api_key=self.api_key)

    @patch("openai.ChatCompletion.create")
    def test_generate(self, mock_create):
        # Corrected mock response structure
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message={"content": "{\"name\": \"Alice\", \"age\": 30}"})
        ]
        mock_create.return_value = mock_response

        prompt = "Generate a JSON object with name and age."
        try:
            result = self.backend.generate(prompt, model="gpt-3.5-turbo", max_tokens=50)
            self.assertIsInstance(result, str)
            self.assertGreater(len(result), 0)
        except ValueError as e:
            self.fail(f"OpenAIBackend.generate raised an exception: {e}")

    @patch("openai.ChatCompletion.create")
    def test_agenerate(self, mock_create):
        # Corrected mock response structure
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message={"content": "{\"name\": \"Alice\", \"age\": 30}"})
        ]
        mock_create.return_value = mock_response

        async def run_test():
            prompt = "Generate a JSON object with name and age."
            try:
                result = await self.backend.agenerate(prompt, model="gpt-3.5-turbo", max_tokens=50)
                self.assertIsInstance(result, str)
                self.assertGreater(len(result), 0)
            except ValueError as e:
                self.fail(f"OpenAIBackend.agenerate raised an exception: {e}")

        asyncio.run(run_test())

if __name__ == "__main__":
    unittest.main()
