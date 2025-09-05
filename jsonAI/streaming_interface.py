"""
Streaming Interface for Real-time JsonAI Generation.

This module provides real-time streaming capabilities for JsonAI,
enabling live updates during data generation and agent interactions.
"""

import asyncio
import json
from typing import Dict, Any, List, Optional, AsyncGenerator, Callable
from datetime import datetime
import uuid

from jsonAI.main import Jsonformer
from jsonAI.model_backends import ModelBackend
from jsonAI.conversational_agent import ConversationalAgentInterface


class StreamingJsonformer:
    """Enhanced Jsonformer with real-time streaming capabilities."""

    def __init__(self, jsonformer: Jsonformer):
        self.jsonformer = jsonformer
        self.stream_callbacks: List[Callable] = []
        self.generation_id = str(uuid.uuid4())

    def add_stream_callback(self, callback: Callable):
        """Add a callback for streaming updates."""
        self.stream_callbacks.append(callback)

    async def generate_with_streaming(self, progress_callback: Optional[Callable] = None) -> AsyncGenerator[Dict[str, Any], None]:
        """Generate data with real-time streaming updates."""

        # Initialize streaming session
        session_id = str(uuid.uuid4())
        yield {
            "type": "session_start",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "schema": self.jsonformer.json_schema
        }

        try:
            # Stream schema processing
            yield {
                "type": "processing_schema",
                "message": "Analyzing JSON schema structure...",
                "timestamp": datetime.now().isoformat()
            }

            # Simulate processing steps (in real implementation, this would hook into actual generation)
            schema_keys = list(self.jsonformer.json_schema.get("properties", {}).keys())

            for i, key in enumerate(schema_keys):
                yield {
                    "type": "generating_field",
                    "field": key,
                    "progress": (i + 1) / len(schema_keys),
                    "message": f"Generating value for '{key}'...",
                    "timestamp": datetime.now().isoformat()
                }

                # Call progress callback if provided
                if progress_callback:
                    await progress_callback({
                        "field": key,
                        "progress": (i + 1) / len(schema_keys)
                    })

                # Simulate generation delay
                await asyncio.sleep(0.1)

            # Generate final result
            result = self.jsonformer()

            yield {
                "type": "generation_complete",
                "result": result,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            yield {
                "type": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }


class StreamingAgentInterface:
    """Streaming interface for conversational agents."""

    def __init__(self, conversational_agent: ConversationalAgentInterface):
        self.agent_interface = conversational_agent
        self.active_streams: Dict[str, asyncio.Queue] = {}

    async def start_conversation_stream(self, conversation_id: str) -> str:
        """Start a streaming conversation session."""
        if conversation_id in self.active_streams:
            return conversation_id

        self.active_streams[conversation_id] = asyncio.Queue()
        return conversation_id

    async def stream_conversation(self, conversation_id: str, user_message: str) -> AsyncGenerator[str, None]:
        """Stream a conversation with real-time updates."""

        if conversation_id not in self.active_streams:
            yield "Error: Conversation not initialized"
            return

        queue = self.active_streams[conversation_id]

        # Start processing in background
        asyncio.create_task(self._process_streaming_conversation(conversation_id, user_message, queue))

        # Stream responses
        while True:
            try:
                message = await asyncio.wait_for(queue.get(), timeout=30.0)

                if message.get("type") == "end":
                    break

                yield json.dumps(message)

            except asyncio.TimeoutError:
                yield json.dumps({
                    "type": "timeout",
                    "message": "Stream timeout",
                    "timestamp": datetime.now().isoformat()
                })
                break

    async def _process_streaming_conversation(self, conversation_id: str, user_message: str, queue: asyncio.Queue):
        """Process conversation with streaming updates."""

        try:
            # Stream thinking process
            await queue.put({
                "type": "thinking",
                "message": "Analyzing your request...",
                "timestamp": datetime.now().isoformat()
            })

            # Analyze intent
            await queue.put({
                "type": "intent_analysis",
                "message": "Understanding your intent...",
                "timestamp": datetime.now().isoformat()
            })

            # Route to agent
            await queue.put({
                "type": "agent_routing",
                "message": "Finding the right agent...",
                "timestamp": datetime.now().isoformat()
            })

            # Generate response
            await queue.put({
                "type": "generating_response",
                "message": "Generating response...",
                "timestamp": datetime.now().isoformat()
            })

            # Get actual response
            response_chunks = []
            async for chunk in self.agent_interface.process_conversation(conversation_id, user_message):
                response_chunks.append(chunk)
                await queue.put({
                    "type": "response_chunk",
                    "content": chunk,
                    "timestamp": datetime.now().isoformat()
                })

            # Complete
            await queue.put({
                "type": "complete",
                "full_response": "".join(response_chunks),
                "timestamp": datetime.now().isoformat()
            })

        except Exception as e:
            await queue.put({
                "type": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })

        finally:
            await queue.put({"type": "end"})

    def end_conversation_stream(self, conversation_id: str):
        """End a streaming conversation."""
        if conversation_id in self.active_streams:
            del self.active_streams[conversation_id]


class RealTimeDashboard:
    """Real-time dashboard for monitoring JsonAI operations."""

    def __init__(self):
        self.metrics: Dict[str, Any] = {
            "active_conversations": 0,
            "total_generations": 0,
            "active_agents": 0,
            "performance_stats": {}
        }
        self.subscribers: List[asyncio.Queue] = []

    def subscribe(self) -> asyncio.Queue:
        """Subscribe to real-time updates."""
        queue = asyncio.Queue()
        self.subscribers.append(queue)
        return queue

    async def broadcast_update(self, update_type: str, data: Dict[str, Any]):
        """Broadcast update to all subscribers."""
        message = {
            "type": update_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }

        for subscriber in self.subscribers:
            try:
                await subscriber.put(message)
            except:
                # Remove dead subscribers
                self.subscribers.remove(subscriber)

    async def update_metrics(self, metric: str, value: Any):
        """Update a metric and broadcast to subscribers."""
        self.metrics[metric] = value
        await self.broadcast_update("metric_update", {metric: value})

    async def log_generation_event(self, generation_data: Dict[str, Any]):
        """Log a generation event."""
        self.metrics["total_generations"] += 1
        await self.broadcast_update("generation_event", generation_data)
