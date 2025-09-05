"""
Test cases for Conversational Agent Interface.

Tests the natural language interaction capabilities and multi-agent collaboration.
"""

import unittest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock

from jsonAI.conversational_agent import (
    ConversationalAgentInterface,
    Agent,
    ConversationMessage
)
from jsonAI.model_backends import OllamaBackend, OpenAIBackend


class TestConversationalAgentInterface(unittest.TestCase):
    """Test cases for conversational agent interface."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_backend = Mock()
        self.mock_backend.generate.return_value = '{"name": "John", "age": 30}'
        # Mock the tokenizer with proper vocab structure
        self.mock_backend.tokenizer = Mock()
        self.mock_backend.tokenizer.vocab = {
            "123": 123, "true": 456, "false": 789, "null": 101,
            "hello": 202, "2023-01-01": 303, "12:00:00": 404
        }
        self.mock_backend.tokenizer.get_vocab.return_value = self.mock_backend.tokenizer.vocab
        self.mock_backend.tokenizer.__len__ = Mock(return_value=len(self.mock_backend.tokenizer.vocab))
        self.mock_backend.tokenizer.decode = Mock(side_effect=lambda token_id, **kwargs: {
            123: "John",
            456: "true", 
            789: "false",
            101: "null",
            202: "Alice",
            303: "2023-01-01",
            404: "12:00:00"
        }.get(token_id, f"token_{token_id}"))
        self.agent_interface = ConversationalAgentInterface(self.mock_backend)

    def test_create_agent(self):
        """Test agent creation."""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"}
            }
        }

        agent = self.agent_interface.create_agent(
            agent_id="test_agent",
            name="TestAgent",
            role="Tester",
            capabilities=["generate_data"],
            schema=schema
        )

        self.assertEqual(agent.id, "test_agent")
        self.assertEqual(agent.name, "TestAgent")
        self.assertEqual(agent.role, "Tester")
        self.assertIn("generate_data", agent.capabilities)
        self.assertIsNotNone(agent.jsonformer)

    def test_analyze_intent(self):
        """Test intent analysis."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            intent = loop.run_until_complete(
                self.agent_interface._analyze_intent("Generate a user profile")
            )

            self.assertIn("primary_intent", intent)
            self.assertIn("all_intents", intent)
            self.assertIn("confidence", intent)
        finally:
            loop.close()

    def test_route_to_agent(self):
        """Test agent routing."""
        # Create test agent
        schema = {"type": "object", "properties": {"name": {"type": "string"}}}
        agent = self.agent_interface.create_agent(
            "test_agent", "Test", "Role", ["generate_data"], schema
        )

        # Test routing
        intent = {"primary_intent": "generate_data"}
        routed_agent = self.agent_interface._route_to_agent(intent)

        self.assertEqual(routed_agent.id, "test_agent")

    def test_conversation_flow(self):
        """Test basic conversation flow."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            conversation_id = "test_conv"
            user_message = "Generate a user profile"

            # Create an agent with data generation capabilities
            schema = {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "age": {"type": "integer"}
                }
            }
            agent = self.agent_interface.create_agent(
                agent_id="data_generator",
                name="DataGenerator",
                role="Data Generation",
                capabilities=["generate_data", "create_profiles"],
                schema=schema,
                max_tokens=50  # Limit tokens for small models
            )

            # Mock the backend response
            self.mock_backend.generate.return_value = '{"name": "Alice", "age": 25}'

            # Process conversation
            responses = []
            async def collect_responses():
                async for chunk in self.agent_interface.process_conversation(
                    conversation_id, user_message
                ):
                    responses.append(chunk)

            loop.run_until_complete(collect_responses())

            # Verify response was generated
            self.assertTrue(len(responses) > 0)
            response_text = "".join(responses)
            self.assertIn("generated data", response_text.lower())
            # Check that we got a JSON-like structure
            self.assertTrue("{" in response_text or "[" in response_text)

        finally:
            loop.close()

    def test_agent_memory(self):
        """Test agent memory functionality."""
        schema = {"type": "object", "properties": {"name": {"type": "string"}}}
        agent = Agent(
            id="test_agent",
            name="TestAgent",
            role="Tester",
            capabilities=["generate_data"],
            jsonformer=Mock()
        )

        # Add messages to memory
        msg1 = ConversationMessage(
            role="user",
            content="Hello",
            timestamp=Mock()
        )
        msg2 = ConversationMessage(
            role="assistant",
            content="Hi there",
            timestamp=Mock()
        )

        agent.memory.extend([msg1, msg2])

        self.assertEqual(len(agent.memory), 2)
        self.assertEqual(agent.memory[0].content, "Hello")
        self.assertEqual(agent.memory[1].content, "Hi there")


class TestAgentCollaboration(unittest.TestCase):
    """Test cases for multi-agent collaboration."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_backend = Mock()
        self.mock_backend.generate.return_value = '{"result": "success"}'
        # Mock the tokenizer with proper vocab structure
        self.mock_backend.tokenizer = Mock()
        self.mock_backend.tokenizer.vocab = {
            "123": 123, "true": 456, "false": 789, "null": 101,
            "hello": 202, "2023-01-01": 303, "12:00:00": 404
        }
        self.mock_backend.tokenizer.get_vocab.return_value = self.mock_backend.tokenizer.vocab
        self.mock_backend.tokenizer.__len__ = Mock(return_value=len(self.mock_backend.tokenizer.vocab))
        self.mock_backend.tokenizer.decode = Mock(side_effect=lambda token_id, **kwargs: {
            123: "John",
            456: "true", 
            789: "false",
            101: "null",
            202: "Alice",
            303: "2023-01-01",
            404: "12:00:00"
        }.get(token_id, f"token_{token_id}"))
        self.agent_interface = ConversationalAgentInterface(self.mock_backend)

        # Create test agents
        schema = {"type": "object", "properties": {"result": {"type": "string"}}}
        self.agent1 = self.agent_interface.create_agent(
            "agent1", "Agent1", "Role1", ["task1"], schema, max_tokens=50
        )
        self.agent2 = self.agent_interface.create_agent(
            "agent2", "Agent2", "Role2", ["task2"], schema, max_tokens=50
        )

    def test_collaborate_agents(self):
        """Test agent collaboration."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            result = loop.run_until_complete(
                self.agent_interface.collaborate_agents(
                    task="Test collaboration",
                    agent_ids=["agent1", "agent2"]
                )
            )

            self.assertIn("collaboration_results", result)
            self.assertIn("summary", result)
            self.assertEqual(len(result["collaboration_results"]), 2)

        finally:
            loop.close()


class TestConversationMessage(unittest.TestCase):
    """Test cases for conversation message handling."""

    def test_message_creation(self):
        """Test conversation message creation."""
        from datetime import datetime
        msg = ConversationMessage(
            role="user",
            content="Test message",
            timestamp=datetime.now(),
            metadata={"test": "data"}
        )

        self.assertEqual(msg.role, "user")
        self.assertEqual(msg.content, "Test message")
        self.assertIsNotNone(msg.timestamp)
        self.assertEqual(msg.metadata["test"], "data")


if __name__ == "__main__":
    unittest.main()
