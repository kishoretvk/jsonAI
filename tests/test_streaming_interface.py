"""
Test cases for Streaming Interface.

Tests real-time streaming capabilities and event handling.
"""

import unittest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from jsonAI.streaming_interface import (
    StreamingJsonformer,
    StreamingAgentInterface,
    RealTimeDashboard
)
from jsonAI.main import Jsonformer
from jsonAI.model_backends import OllamaBackend


class TestStreamingJsonformer(unittest.TestCase):
    """Test cases for streaming Jsonformer."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_backend = Mock()
        self.mock_backend.generate.return_value = '{"name": "John", "age": 30}'

        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"}
            }
        }

        self.jsonformer = Jsonformer(
            model_backend=self.mock_backend,
            json_schema=schema,
            prompt="Generate a person"
        )

        self.streaming_jsonformer = StreamingJsonformer(self.jsonformer)

    def test_streaming_initialization(self):
        """Test streaming interface initialization."""
        self.assertIsNotNone(self.streaming_jsonformer.jsonformer)
        self.assertEqual(len(self.streaming_jsonformer.stream_callbacks), 0)

    def test_add_stream_callback(self):
        """Test adding stream callbacks."""
        callback = Mock()
        self.streaming_jsonformer.add_stream_callback(callback)

        self.assertEqual(len(self.streaming_jsonformer.stream_callbacks), 1)
        self.assertEqual(self.streaming_jsonformer.stream_callbacks[0], callback)

    def test_streaming_generation(self):
        """Test streaming generation."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            events = []
            async def collect_events():
                async for event in self.streaming_jsonformer.generate_with_streaming():
                    events.append(event)

            loop.run_until_complete(collect_events())

            # Verify we got session start and complete events
            self.assertTrue(len(events) >= 2)
            self.assertEqual(events[0]["type"], "session_start")
            self.assertIn("session_id", events[0])

            # Find completion event
            complete_events = [e for e in events if e["type"] == "generation_complete"]
            self.assertTrue(len(complete_events) > 0)

            complete_event = complete_events[0]
            self.assertIn("result", complete_event)
            self.assertIn("timestamp", complete_event)

        finally:
            loop.close()


class TestStreamingAgentInterface(unittest.TestCase):
    """Test cases for streaming agent interface."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_backend = Mock()
        self.mock_backend.generate.return_value = '{"response": "test"}'

        from jsonAI.conversational_agent import ConversationalAgentInterface
        self.agent_interface = ConversationalAgentInterface(self.mock_backend)
        self.streaming_agent = StreamingAgentInterface(self.agent_interface)

    def test_conversation_stream_initialization(self):
        """Test streaming conversation initialization."""
        conversation_id = "test_conv"
        result_id = self.streaming_agent.start_conversation_stream(conversation_id)

        self.assertEqual(result_id, conversation_id)
        self.assertIn(conversation_id, self.streaming_agent.active_streams)

    def test_end_conversation_stream(self):
        """Test ending streaming conversation."""
        conversation_id = "test_conv"
        self.streaming_agent.start_conversation_stream(conversation_id)

        self.assertIn(conversation_id, self.streaming_agent.active_streams)

        self.streaming_agent.end_conversation_stream(conversation_id)

        self.assertNotIn(conversation_id, self.streaming_agent.active_streams)


class TestRealTimeDashboard(unittest.TestCase):
    """Test cases for real-time dashboard."""

    def setUp(self):
        """Set up test fixtures."""
        self.dashboard = RealTimeDashboard()

    def test_dashboard_initialization(self):
        """Test dashboard initialization."""
        expected_metrics = {
            "active_conversations": 0,
            "total_generations": 0,
            "active_agents": 0,
            "performance_stats": {}
        }

        self.assertEqual(self.dashboard.metrics, expected_metrics)
        self.assertEqual(len(self.dashboard.subscribers), 0)

    def test_subscribe_to_updates(self):
        """Test subscribing to dashboard updates."""
        queue = self.dashboard.subscribe()
        self.assertEqual(len(self.dashboard.subscribers), 1)
        self.assertIsNotNone(queue)

    def test_update_metrics(self):
        """Test updating dashboard metrics."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            # Subscribe to updates
            queue = self.dashboard.subscribe()

            # Update metric
            loop.run_until_complete(
                self.dashboard.update_metrics("active_conversations", 5)
            )

            # Verify metric was updated
            self.assertEqual(self.dashboard.metrics["active_conversations"], 5)

        finally:
            loop.close()

    def test_broadcast_update(self):
        """Test broadcasting updates to subscribers."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            # Subscribe to updates
            queue = self.dashboard.subscribe()

            # Broadcast update
            loop.run_until_complete(
                self.dashboard.broadcast_update("test_event", {"data": "test"})
            )

            # Verify update was received
            message = loop.run_until_complete(queue.get())
            self.assertEqual(message["type"], "test_event")
            self.assertEqual(message["data"]["data"], "test")
            self.assertIn("timestamp", message)

        finally:
            loop.close()

    def test_log_generation_event(self):
        """Test logging generation events."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            # Subscribe to updates
            queue = self.dashboard.subscribe()

            # Log generation event
            generation_data = {"result": "success", "duration": 1.5}
            loop.run_until_complete(
                self.dashboard.log_generation_event(generation_data)
            )

            # Verify event was logged and broadcast
            self.assertEqual(self.dashboard.metrics["total_generations"], 1)

            # Verify broadcast
            message = loop.run_until_complete(queue.get())
            self.assertEqual(message["type"], "generation_event")
            self.assertEqual(message["data"]["result"], "success")

        finally:
            loop.close()


class TestStreamingIntegration(unittest.TestCase):
    """Integration tests for streaming functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_backend = Mock()
        self.mock_backend.generate.return_value = '{"name": "Test", "value": 123}'

        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "value": {"type": "integer"}
            }
        }

        self.jsonformer = Jsonformer(
            model_backend=self.mock_backend,
            json_schema=schema,
            prompt="Generate test data"
        )

    def test_full_streaming_workflow(self):
        """Test complete streaming workflow."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            streaming = StreamingJsonformer(self.jsonformer)

            # Track events
            events = []
            async def collect_events():
                async for event in streaming.generate_with_streaming():
                    events.append(event)

            loop.run_until_complete(collect_events())

            # Verify workflow
            event_types = [e["type"] for e in events]
            self.assertIn("session_start", event_types)
            self.assertIn("generation_complete", event_types)

            # Verify session ID consistency
            session_ids = [e.get("session_id") for e in events if "session_id" in e]
            self.assertTrue(len(set(session_ids)) == 1)  # All same session ID

        finally:
            loop.close()


if __name__ == "__main__":
    unittest.main()
