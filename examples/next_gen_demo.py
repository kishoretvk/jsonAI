"""
JsonAI Next-Gen Demo: Conversational Agents + Streaming + Integrations

This example demonstrates the next generation of JsonAI features:
- Conversational agents with natural language interaction
- Real-time streaming generation
- Plugin system for extensibility
- Integration with popular developer tools
- One-click deployment capabilities
"""

import asyncio
import json
from jsonAI.model_backends import OllamaBackend
from jsonAI.conversational_agent import ConversationalAgentInterface, Agent
from jsonAI.streaming_interface import StreamingJsonformer, StreamingAgentInterface
from jsonAI.plugin_system import PluginRegistry, register_plugin, ExampleBackendPlugin
from jsonAI.integration_hub import IntegrationHub
from jsonAI.one_click_deploy import OneClickDeployer


async def demo_conversational_agents():
    """Demonstrate conversational agent capabilities."""
    print("🤖 Demo: Conversational Agents")
    print("=" * 50)

    # Initialize backend
    backend = OllamaBackend(model_name="mistral")

    # Create conversational agent interface
    agent_interface = ConversationalAgentInterface(backend)

    # Define agent schemas
    data_generator_schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"},
            "occupation": {"type": "string"},
            "skills": {"type": "array", "items": {"type": "string"}}
        }
    }

    validator_schema = {
        "type": "object",
        "properties": {
            "is_valid": {"type": "boolean"},
            "errors": {"type": "array", "items": {"type": "string"}},
            "suggestions": {"type": "array", "items": {"type": "string"}}
        }
    }

    # Create agents
    data_agent = agent_interface.create_agent(
        agent_id="data_generator",
        name="DataGen",
        role="Data Generation Specialist",
        capabilities=["generate_data", "create_samples"],
        schema=data_generator_schema
    )

    validator_agent = agent_interface.create_agent(
        agent_id="validator",
        name="Validator",
        role="Data Validation Specialist",
        capabilities=["validate_data", "check_quality"],
        schema=validator_schema
    )

    print(f"✅ Created agents: {data_agent.name}, {validator_agent.name}")

    # Simulate conversation
    conversation_id = "demo_conversation"

    print("\n💬 Conversation Demo:")
    print("-" * 30)

    user_messages = [
        "Generate a profile for a software engineer",
        "Validate this data and suggest improvements",
        "Create 3 more profiles with different occupations"
    ]

    for message in user_messages:
        print(f"👤 User: {message}")

        # Process through conversational interface
        response_chunks = []
        async for chunk in agent_interface.process_conversation(conversation_id, message):
            response_chunks.append(chunk)
            print(f"🤖 Agent: {chunk}", end="", flush=True)

        print("\n")

    # Demonstrate agent collaboration
    print("\n🤝 Agent Collaboration Demo:")
    print("-" * 35)

    collaboration_result = await agent_interface.collaborate_agents(
        task="Generate and validate a comprehensive user profile dataset",
        agent_ids=["data_generator", "validator"]
    )

    print("📊 Collaboration Results:")
    for agent_name, result in collaboration_result["collaboration_results"].items():
        print(f"🔹 {agent_name}: {result[:100]}...")


async def demo_streaming_generation():
    """Demonstrate real-time streaming capabilities."""
    print("\n📡 Demo: Real-time Streaming")
    print("=" * 50)

    # Initialize backend and jsonformer
    backend = OllamaBackend(model_name="mistral")

    from jsonAI.main import Jsonformer
    schema = {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "description": {"type": "string"},
            "tags": {"type": "array", "items": {"type": "string"}},
            "metadata": {"type": "object"}
        }
    }

    jsonformer = Jsonformer(
        model_backend=backend,
        json_schema=schema,
        prompt="Generate a project description"
    )

    # Create streaming interface
    streaming_jsonformer = StreamingJsonformer(jsonformer)

    print("🚀 Streaming Generation:")
    print("-" * 25)

    # Stream generation with progress updates
    async for update in streaming_jsonformer.generate_with_streaming():
        if update["type"] == "session_start":
            print(f"📋 Session: {update['session_id']}")
        elif update["type"] == "processing_schema":
            print(f"⚙️  {update['message']}")
        elif update["type"] == "generating_field":
            progress = update["progress"] * 100
            print(".1f")
        elif update["type"] == "generation_complete":
            print(f"\n✅ Generation Complete!")
            print(f"📄 Result: {json.dumps(update['result'], indent=2)}")
        elif update["type"] == "error":
            print(f"❌ Error: {update['error']}")


async def demo_plugin_system():
    """Demonstrate plugin system capabilities."""
    print("\n🔌 Demo: Plugin System")
    print("=" * 50)

    # Initialize plugin registry
    registry = PluginRegistry()
    registry.setup_default_paths()

    # Register example plugin
    example_plugin = ExampleBackendPlugin()
    register_plugin(example_plugin)

    print("📦 Available Plugins:")
    print("-" * 20)

    # List registered plugins
    backend_plugins = registry.manager.get_plugins_by_type("backend")
    for plugin in backend_plugins:
        print(f"🔹 {plugin.name} v{plugin.version}")

    # Auto-discover plugins
    print("\n🔍 Auto-discovering plugins...")
    registry.manager.discover_plugins()

    print(f"📊 Total plugins loaded: {len(registry.manager.plugins)}")


async def demo_integrations():
    """Demonstrate integration capabilities."""
    print("\n🔗 Demo: Tool Integrations")
    print("=" * 50)

    # Initialize integration hub
    hub = IntegrationHub()

    print("🌐 Available Integrations:")
    print("-" * 25)

    integrations = hub.list_available_integrations()
    for integration in integrations:
        print(f"🔹 {integration}")

    # Demonstrate VS Code integration
    print("\n💻 VS Code Integration Demo:")
    print("-" * 30)

    # Create sample schema
    sample_schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "email": {"type": "string"},
            "active": {"type": "boolean"}
        }
    }

    # Generate VS Code snippet
    snippet = hub.vscode.create_vscode_snippet(sample_schema, "user_profile")
    print("📝 Generated VS Code Snippet:")
    print(json.dumps(snippet, indent=2))

    # Demonstrate webhook integration
    print("\n🪝 Webhook Integration Demo:")
    print("-" * 30)

    # Register webhook
    hub.webhooks.register_webhook("generation_complete", "https://httpbin.org/post")

    # Trigger event
    await hub.webhooks.trigger_event("generation_complete", {
        "result": {"status": "success"},
        "timestamp": "2025-09-04T10:00:00Z"
    })

    print("✅ Webhook event triggered!")


async def demo_deployment():
    """Demonstrate one-click deployment."""
    print("\n🚀 Demo: One-Click Deployment")
    print("=" * 50)

    # Initialize deployer
    deployer = OneClickDeployer()

    print("📋 Available Deployment Options:")
    print("-" * 35)

    options = deployer.list_deployment_options()
    for option in options:
        print(f"🔹 {option}")

    print("\n🏗️  Creating deployment configurations...")

    # Create Docker setup
    docker_result = deployer.deploy("docker", base_image="python:3.9-slim", expose_port=8000)
    print(f"🐳 Docker: {docker_result}")

    # Create Docker Compose setup
    compose_result = deployer.deploy("docker-compose", services=["api", "ollama"])
    print(f"🐙 Docker Compose: {compose_result}")

    # Create cloud deployment configs
    railway_result = deployer.deploy("railway")
    print(f"🚂 Railway: {railway_result}")

    print("\n✅ Deployment configurations created!")
    print("💡 Run 'docker-compose up' to start locally")


async def main():
    """Run all demos."""
    print("🎉 JsonAI Next-Gen Feature Demo")
    print("=" * 60)
    print("Showcasing the future of structured data generation!")
    print()

    try:
        await demo_conversational_agents()
        await demo_streaming_generation()
        await demo_plugin_system()
        await demo_integrations()
        await demo_deployment()

        print("\n🎊 All demos completed successfully!")
        print("\n🚀 JsonAI is ready for the next generation of AI-powered development!")

    except Exception as e:
        print(f"\n❌ Demo error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
