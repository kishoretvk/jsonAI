"""
Conversational Agent Interface for JsonAI.

This module provides a natural language interface for interacting with JsonAI agents,
enabling conversational workflows and multi-agent collaboration.
"""

from typing import Dict, Any, List, Optional, Callable, AsyncGenerator
import asyncio
import json
import re
from datetime import datetime
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from jsonAI.main import Jsonformer
    from jsonAI.workflow_orchestrator import WorkflowOrchestrator, WorkflowStep, WorkflowStepType
import json
import re
from datetime import datetime
from dataclasses import dataclass

from jsonAI.main import Jsonformer
from jsonAI.model_backends import ModelBackend
from jsonAI.workflow_orchestrator import WorkflowOrchestrator, WorkflowStep, WorkflowStepType
from jsonAI.tool_registry import ToolRegistry


@dataclass
class ConversationMessage:
    """Represents a message in a conversation."""
    role: str  # "user", "assistant", "agent", "system"
    content: str
    timestamp: datetime
    metadata: Dict[str, Any] = None


@dataclass
class Agent:
    """Represents an agent in the system."""
    id: str
    name: str
    role: str
    capabilities: List[str]
    jsonformer: Jsonformer
    memory: List[ConversationMessage] = None

    def __post_init__(self):
        if self.memory is None:
            self.memory = []


class ConversationalAgentInterface:
    """Natural language interface for JsonAI with multi-agent support."""

    def __init__(self, model_backend: ModelBackend):
        self.model_backend = model_backend
        self.agents: Dict[str, Agent] = {}
        self.conversations: Dict[str, List[ConversationMessage]] = {}
        self.workflow_orchestrator = WorkflowOrchestrator(debug=False)

    def create_agent(self, agent_id: str, name: str, role: str,
                    capabilities: List[str], schema: Dict[str, Any],
                    max_tokens: Optional[int] = None) -> Agent:
        """Create a new agent with specific capabilities."""

        jsonformer = Jsonformer(
            model_backend=self.model_backend,
            json_schema=schema,
            prompt=f"You are {name}, a {role}. Help users with: {', '.join(capabilities)}",
            debug=False,
            max_tokens=max_tokens
        )

        agent = Agent(
            id=agent_id,
            name=name,
            role=role,
            capabilities=capabilities,
            jsonformer=jsonformer
        )

        self.agents[agent_id] = agent
        return agent

    async def process_conversation(self, conversation_id: str,
                                 user_message: str) -> AsyncGenerator[str, None]:
        """Process a conversation with streaming responses."""

        # Initialize conversation if new
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = []

        # Add user message
        user_msg = ConversationMessage(
            role="user",
            content=user_message,
            timestamp=datetime.now()
        )
        self.conversations[conversation_id].append(user_msg)

        # Analyze intent and route to appropriate agent
        intent = await self._analyze_intent(user_message)
        target_agent = self._route_to_agent(intent)

        if not target_agent:
            yield "I don't have an agent capable of handling that request."
            return

        # Generate response using the agent
        response = await self._generate_agent_response(target_agent, user_message)

        # Stream the response
        for chunk in self._stream_response(response):
            yield chunk

        # Add assistant response to conversation
        assistant_msg = ConversationMessage(
            role="assistant",
            content=response,
            timestamp=datetime.now(),
            metadata={"agent": target_agent.id}
        )
        self.conversations[conversation_id].append(assistant_msg)

    async def _analyze_intent(self, message: str) -> Dict[str, Any]:
        """Analyze user intent from message."""
        # Simple intent analysis - could be enhanced with ML
        intents = {
            "generate_data": ["generate", "create", "make", "build"],
            "validate_schema": ["validate", "check", "verify"],
            "transform_data": ["convert", "transform", "change"],
            "analyze_data": ["analyze", "review", "examine"]
        }

        message_lower = message.lower()
        detected_intents = []

        for intent, keywords in intents.items():
            if any(keyword in message_lower for keyword in keywords):
                detected_intents.append(intent)

        return {
            "primary_intent": detected_intents[0] if detected_intents else "general",
            "all_intents": detected_intents,
            "confidence": len(detected_intents) / len(message.split()) if detected_intents else 0
        }

    def _route_to_agent(self, intent: Dict[str, Any]) -> Optional[Agent]:
        """Route request to the most appropriate agent."""
        intent_type = intent.get("primary_intent", "general")

        # Find agent with matching capabilities
        for agent in self.agents.values():
            if intent_type in agent.capabilities or "general" in agent.capabilities:
                return agent

        return None

    async def _generate_agent_response(self, agent: Agent, user_message: str) -> str:
        """Generate response using the specified agent."""
        # Update agent's memory
        agent.memory.append(ConversationMessage(
            role="user",
            content=user_message,
            timestamp=datetime.now()
        ))

        # Create context from conversation history
        context = self._build_context(agent.memory[-5:])  # Last 5 messages

        # Generate response using Jsonformer
        prompt = f"""
Context: {context}

User: {user_message}

As {agent.name}, the {agent.role}, provide a helpful response focusing on: {', '.join(agent.capabilities)}
"""

        try:
            # Use the agent's jsonformer to generate structured response
            result = agent.jsonformer.generate_data()

            # Format response
            if isinstance(result, dict):
                response = json.dumps(result, indent=2)
            else:
                response = str(result)

            return f"Here's the generated data:\n\n{response}"

        except Exception as e:
            return f"I encountered an error: {str(e)}"

    def _build_context(self, messages: List[ConversationMessage]) -> str:
        """Build conversation context from message history."""
        context_parts = []
        for msg in messages:
            context_parts.append(f"{msg.role}: {msg.content}")
        return "\n".join(context_parts)

    def _stream_response(self, response: str) -> List[str]:
        """Stream response in chunks for better UX."""
        words = response.split()
        chunks = []
        current_chunk = []

        for word in words:
            current_chunk.append(word)
            if len(current_chunk) >= 10:  # Stream every 10 words
                chunks.append(" ".join(current_chunk))
                current_chunk = []

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks

    async def collaborate_agents(self, task: str, agent_ids: List[str]) -> Dict[str, Any]:
        """Enable multiple agents to collaborate on a task."""
        if len(agent_ids) < 2:
            return {"error": "Need at least 2 agents for collaboration"}

        agents = [self.agents[aid] for aid in agent_ids if aid in self.agents]
        if len(agents) != len(agent_ids):
            return {"error": "Some agents not found"}

        # Import workflow components locally to avoid circular imports
        from jsonAI.workflow_orchestrator import WorkflowOrchestrator, WorkflowStep, WorkflowStepType

        # Create collaborative workflow
        workflow_orchestrator = WorkflowOrchestrator(debug=False)
        steps = []
        for i, agent in enumerate(agents):
            steps.append(WorkflowStep(
                id=f"agent_{i}",
                name=f"{agent.name} Task",
                type=WorkflowStepType.GENERATION,
                config={
                    "agent_id": agent.id,
                    "task": task
                },
                dependencies=[f"agent_{i-1}"] if i > 0 else []
            ))

        workflow_orchestrator.define_workflow(steps)

        # Execute collaborative workflow
        results = {}
        for step in steps:
            agent = self.agents[step.config["agent_id"]]
            response = await self._generate_agent_response(agent, step.config["task"])
            results[agent.name] = response

        return {
            "collaboration_results": results,
            "summary": f"Completed collaborative task with {len(agents)} agents"
        }
