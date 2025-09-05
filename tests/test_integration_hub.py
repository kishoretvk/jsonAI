"""
Test cases for Integration Hub.

Tests integrations with external services and tools.
"""

import unittest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from jsonAI.integration_hub import (
    GitHubIntegration,
    SlackIntegration,
    VSCodeIntegration,
    WebhookIntegration,
    IntegrationHub
)


class TestGitHubIntegration(unittest.TestCase):
    """Test cases for GitHub integration."""

    def setUp(self):
        """Set up test fixtures."""
        self.github = GitHubIntegration(token="fake_token")

    @patch('requests.post')
    def test_create_issue_with_generated_data(self, mock_post):
        """Test creating GitHub issue with generated data."""
        # Mock the response
        mock_response = Mock()
        mock_response.json.return_value = {"number": 123, "html_url": "https://github.com/test/repo/issues/123"}
        mock_post.return_value = mock_response

        # Mock jsonformer
        mock_jsonformer = Mock()
        mock_jsonformer.generate_data.return_value = {"name": "John", "age": 30}

        result = self.github.create_issue_with_generated_data(
            repo="test/repo",
            title="Test Issue",
            jsonformer=mock_jsonformer,
            prompt="Generate test data"
        )

        # Verify API call was made
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        self.assertIn("test/repo/issues", call_args[0][0])
        self.assertEqual(call_args[1]["json"]["title"], "Test Issue")

        # Verify result
        self.assertEqual(result["number"], 123)

    @patch('requests.get')
    def test_generate_from_issue(self, mock_get):
        """Test generating data from GitHub issue."""
        # Mock issue response
        mock_issue_response = Mock()
        mock_issue_response.json.return_value = {
            "body": "Please generate user data",
            "title": "Generate User Data"
        }
        mock_get.return_value = mock_issue_response

        # Mock jsonformer
        mock_jsonformer = Mock()
        mock_jsonformer.generate_data.return_value = {"name": "Alice", "role": "developer"}

        result = self.github.generate_from_issue(
            repo="test/repo",
            issue_number=123,
            jsonformer=mock_jsonformer
        )

        # Verify API call was made
        mock_get.assert_called_once_with(
            "https://api.github.com/repos/test/repo/issues/123",
            headers={"Authorization": "token fake_token"}
        )

        # Verify result structure
        self.assertIn("issue", result)
        self.assertIn("generated_data", result)
        self.assertEqual(result["generated_data"]["name"], "Alice")


class TestSlackIntegration(unittest.TestCase):
    """Test cases for Slack integration."""

    def setUp(self):
        """Set up test fixtures."""
        self.slack = SlackIntegration(token="fake_token")

    @patch('requests.post')
    def test_post_generated_data(self, mock_post):
        """Test posting generated data to Slack."""
        # Mock the response
        mock_response = Mock()
        mock_response.json.return_value = {"ok": True, "ts": "1234567890.123456"}
        mock_post.return_value = mock_response

        # Mock jsonformer
        mock_jsonformer = Mock()
        mock_jsonformer.generate_data.return_value = {"product": "Widget", "price": 29.99}

        result = self.slack.post_generated_data(
            channel="#test",
            jsonformer=mock_jsonformer,
            prompt="Generate product data",
            title="New Product Data"
        )

        # Verify API call was made
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        self.assertIn("chat.postMessage", call_args[0][0])

        # Verify message structure
        message = call_args[1]["json"]
        self.assertEqual(message["channel"], "#test")
        self.assertIn("New Product Data", message["text"])
        self.assertIn("blocks", message)

    def test_slack_command_processing(self):
        """Test Slack command processing."""
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            # Mock jsonformer
            mock_jsonformer = Mock()
            mock_jsonformer.generate_data.return_value = {"status": "success"}

            result = loop.run_until_complete(
                self.slack.handle_slack_command(
                    "generate Test data generation",
                    mock_jsonformer
                )
            )

            # Verify command was processed
            mock_jsonformer.generate_data.assert_called_once_with("Test data generation")
            self.assertIn("success", result)

        finally:
            loop.close()


class TestVSCodeIntegration(unittest.TestCase):
    """Test cases for VS Code integration."""

    def setUp(self):
        """Set up test fixtures."""
        self.vscode = VSCodeIntegration()

    def test_generate_schema_from_file(self):
        """Test generating schema from file content."""
        import tempfile
        import os

        # Create a temporary JSON file
        test_data = '{"name": "John", "age": 30, "active": true}'
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write(test_data)
            temp_file = f.name

        try:
            # Mock jsonformer
            mock_jsonformer = Mock()

            result = self.vscode.generate_schema_from_file(temp_file, mock_jsonformer)

            # Verify schema structure
            self.assertIn("type", result)
            self.assertEqual(result["type"], "object")
            self.assertIn("properties", result)
            self.assertIn("name", result["properties"])
            self.assertIn("age", result["properties"])
            self.assertIn("active", result["properties"])

        finally:
            os.unlink(temp_file)

    def test_infer_schema_from_data(self):
        """Test schema inference from data."""
        test_data = {
            "name": "John",
            "age": 30,
            "active": True,
            "tags": ["developer", "python"],
            "profile": {"city": "NYC", "country": "USA"}
        }

        schema = self.vscode._infer_schema_from_data(test_data)

        # Verify schema structure
        self.assertEqual(schema["type"], "object")
        self.assertIn("name", schema["properties"])
        self.assertIn("age", schema["properties"])
        self.assertIn("active", schema["properties"])
        self.assertIn("tags", schema["properties"])
        self.assertIn("profile", schema["properties"])

        # Verify nested object
        profile_schema = schema["properties"]["profile"]
        self.assertEqual(profile_schema["type"], "object")
        self.assertIn("city", profile_schema["properties"])
        self.assertIn("country", profile_schema["properties"])

    def test_create_vscode_snippet(self):
        """Test creating VS Code snippet."""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"}
            }
        }

        snippet = self.vscode.create_vscode_snippet(schema, "user_profile")

        # Verify snippet structure
        self.assertIn("prefix", snippet)
        self.assertIn("body", snippet)
        self.assertIn("description", snippet)
        self.assertEqual(snippet["prefix"], "jsonai-user_profile")

        # Verify body contains generated data
        body = json.loads(snippet["body"])
        self.assertIn("name", body)
        self.assertIn("age", body)


class TestWebhookIntegration(unittest.TestCase):
    """Test cases for webhook integration."""

    def setUp(self):
        """Set up test fixtures."""
        self.webhooks = WebhookIntegration()

    def test_register_webhook(self):
        """Test webhook registration."""
        self.webhooks.register_webhook("test_event", "https://example.com/webhook")

        self.assertIn("test_event", self.webhooks.webhooks)
        self.assertIn("https://example.com/webhook", self.webhooks.webhooks["test_event"])

    def test_register_event_handler(self):
        """Test event handler registration."""
        handler = Mock()
        self.webhooks.register_event_handler("test_event", handler)

        self.assertIn("test_event", self.webhooks.event_handlers)
        self.assertIn(handler, self.webhooks.event_handlers["test_event"])

    @patch('requests.post')
    def test_trigger_event_with_webhook(self, mock_post):
        """Test triggering event with webhook."""
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            # Register webhook
            self.webhooks.register_webhook("test_event", "https://example.com/webhook")

            # Mock response
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response

            # Trigger event
            loop.run_until_complete(
                self.webhooks.trigger_event("test_event", {"data": "test"})
            )

            # Verify webhook was called
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            self.assertEqual(call_args[0][0], "https://example.com/webhook")

            # Verify payload
            payload = call_args[1]["json"]
            self.assertEqual(payload["event"], "test_event")
            self.assertEqual(payload["data"]["data"], "test")
            self.assertIn("timestamp", payload)

        finally:
            loop.close()

    def test_trigger_event_with_handler(self):
        """Test triggering event with handler."""
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            # Register handler
            handler = Mock()
            self.webhooks.register_event_handler("test_event", handler)

            # Trigger event
            loop.run_until_complete(
                self.webhooks.trigger_event("test_event", {"data": "test"})
            )

            # Verify handler was called
            handler.assert_called_once_with("test_event", {"data": "test"})

        finally:
            loop.close()


class TestIntegrationHub(unittest.TestCase):
    """Test cases for integration hub."""

    def setUp(self):
        """Set up test fixtures."""
        self.hub = IntegrationHub()

    def test_hub_initialization(self):
        """Test integration hub initialization."""
        self.assertIsInstance(self.hub.github, GitHubIntegration)
        self.assertIsInstance(self.hub.slack, SlackIntegration)
        self.assertIsInstance(self.hub.vscode, VSCodeIntegration)
        self.assertIsInstance(self.hub.webhooks, WebhookIntegration)

    def test_get_integration(self):
        """Test getting integration by name."""
        github = self.hub.get_integration("github")
        self.assertIsInstance(github, GitHubIntegration)

        slack = self.hub.get_integration("slack")
        self.assertIsInstance(slack, SlackIntegration)

        # Test non-existent integration
        none_integration = self.hub.get_integration("non_existent")
        self.assertIsNone(none_integration)

    def test_list_available_integrations(self):
        """Test listing available integrations."""
        integrations = self.hub.list_available_integrations()

        expected_integrations = ["github", "slack", "vscode", "webhooks"]
        self.assertEqual(set(integrations), set(expected_integrations))

    def test_enable_integration(self):
        """Test enabling integration with config."""
        # Mock integration with configure method
        mock_integration = Mock()
        self.hub.integrations["test"] = mock_integration

        config = {"setting": "value"}
        self.hub.enable_integration("test", config)

        mock_integration.configure.assert_called_once_with(config)


if __name__ == "__main__":
    unittest.main()
