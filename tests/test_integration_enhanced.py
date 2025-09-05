"""
Integration test for enhanced JsonAI components.

This test verifies that all the newly added components work together
to provide agentic testing capabilities.
"""

import unittest
import asyncio
import tempfile
import os
from jsonAI.main import Jsonformer
from jsonAI.model_backends import DummyBackend
from jsonAI.workflow_orchestrator import WorkflowStep, WorkflowStepType
from jsonAI.state_manager import StateManager
from jsonAI.persistent_storage import SQLiteStorage
from jsonAI.mcp_protocol import MCPProtocolHandler
from jsonAI.tracing import get_tracer
from opentelemetry.trace import StatusCode


class TestEnhancedJsonAIIntegration(unittest.TestCase):
    """Integration tests for enhanced JsonAI components."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.backend = DummyBackend()
        self.schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"},
                "email": {"type": "string", "format": "email"}
            }
        }
        self.prompt = "Generate a person profile"
        
    def test_complete_workflow_with_all_components(self):
        """Test a complete workflow using all enhanced components."""
        # Create a tracer
        tracer = get_tracer("test-service", debug=True)
        
        with tracer.start_span("integration_test") as test_span:
            # 1. Create a workflow configuration
            workflow_config = {
                "steps": [
                    {
                        "id": "generation_step",
                        "name": "Generate Person Profile",
                        "type": "generation",
                        "config": {
                            "prompt": "Generate a person profile",
                            "schema": self.schema
                        },
                        "dependencies": []
                    },
                    {
                        "id": "validation_step",
                        "name": "Validate Profile",
                        "type": "condition",
                        "config": {
                            "expression": "True"  # Always pass for this test
                        },
                        "dependencies": ["generation_step"]
                    }
                ]
            }
            
            # Add event to trace
            tracer.add_event(test_span, "created_workflow_config")
            
            # 2. Create Jsonformer with workflow support
            jsonformer = Jsonformer(
                model_backend=self.backend,
                json_schema=self.schema,
                prompt=self.prompt,
                workflow_config=workflow_config,
                debug=True
            )
            
            tracer.add_event(test_span, "created_jsonformer")
            
            # 3. Create state manager and session
            state_manager = StateManager(debug=True)
            session_id = state_manager.create_session("test_session_123")
            state_manager.set_variable("test_input", {"prompt": self.prompt}, scope="session")
            
            tracer.add_event(test_span, "created_state_manager")
            
            # 4. Create persistent storage
            temp_dir = tempfile.mkdtemp()
            db_path = os.path.join(temp_dir, "test_integration.db")
            storage = SQLiteStorage(db_path=db_path, debug=True)
            storage.save_variable("workflow_input", {"prompt": self.prompt}, scope="global")
            
            tracer.add_event(test_span, "created_persistent_storage")
            
            # 5. Create MCP protocol handler
            mcp_handler = MCPProtocolHandler(base_url="http://localhost:8080")
            mcp_handler.register_tool("test_tool", "test_server", {
                "name": "test_tool",
                "description": "A test tool for integration",
                "parameters": {
                    "input": {"type": "string"}
                }
            })
            
            tracer.add_event(test_span, "created_mcp_handler")
            
            # 6. Execute the workflow
            async def run_workflow():
                result = await jsonformer.execute_workflow()
                return result
                
            result = asyncio.run(run_workflow())
            
            tracer.add_event(test_span, "executed_workflow")
            
            # 7. Verify results
            self.assertIn("results", result)
            self.assertIn("generation_step", result["results"])
            self.assertIn("validation_step", result["results"])
            
            # 8. Save results to persistent storage
            storage.save_workflow_execution(
                execution_id="integration_test_123",
                status="completed",
                input_data={"prompt": self.prompt, "schema": self.schema},
                output_data=result,
                metadata={"test": True}
            )
            
            # 9. Verify storage
            stored_execution = storage.load_workflow_execution("integration_test_123")
            self.assertEqual(stored_execution["status"], "completed")
            self.assertEqual(stored_execution["metadata"]["test"], True)
            
            # 10. Clean up temporary files
            storage.close()
            if os.path.exists(db_path):
                os.remove(db_path)
            if os.path.exists(temp_dir):
                os.rmdir(temp_dir)
                
            tracer.add_event(test_span, "completed_test")
            tracer.set_status(test_span, StatusCode.OK)
            
    def test_state_management_with_storage(self):
        """Test state management with persistent storage."""
        # Create state manager
        state_manager = StateManager(debug=True)
        session_id = state_manager.create_session("persistence_test")
        
        # Set some variables
        state_manager.set_variable("user_id", "user_123", scope="session")
        state_manager.set_variable("workflow_name", "test_workflow", scope="global")
        
        # Create storage
        temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(temp_dir, "state_test.db")
        storage = SQLiteStorage(db_path=db_path, debug=True)
        
        # Save state to persistent storage
        storage.save_variable("user_id", "user_123", scope="session", session_id=session_id)
        storage.save_variable("workflow_name", "test_workflow", scope="global")
        
        # Load state from persistent storage
        loaded_user_id = storage.load_variable("user_id", scope="session", session_id=session_id)
        loaded_workflow_name = storage.load_variable("workflow_name", scope="global")
        
        self.assertEqual(loaded_user_id, "user_123")
        self.assertEqual(loaded_workflow_name, "test_workflow")
        
        # Clean up
        storage.close()
        if os.path.exists(db_path):
            os.remove(db_path)
        if os.path.exists(temp_dir):
            os.rmdir(temp_dir)
            
    def test_mcp_tool_discovery_and_execution(self):
        """Test MCP tool discovery and execution."""
        # Create MCP handler
        mcp_handler = MCPProtocolHandler(base_url="http://localhost:8080")
        
        # Register a tool manually
        mcp_handler.register_tool("calculation_tool", "math_server", {
            "name": "calculation_tool",
            "description": "Performs calculations",
            "parameters": {
                "operation": {"type": "string"},
                "operands": {"type": "array"}
            }
        })
        
        # Verify tool registration
        tools = mcp_handler.list_tools()
        self.assertIn("calculation_tool", tools)
        
        tool_info = mcp_handler.get_tool("calculation_tool")
        self.assertIsNotNone(tool_info)
        self.assertEqual(tool_info["server"], "math_server")
        
        # Note: We're not actually calling the tool since there's no server running
        # In a real test, we would mock the HTTP calls
        
    def test_tracing_with_jsonformer(self):
        """Test tracing integration with Jsonformer."""
        from opentelemetry.trace import StatusCode
        
        # Create tracer
        tracer = get_tracer("jsonformer-test", debug=True)
        
        # Create Jsonformer
        jsonformer = Jsonformer(
            model_backend=self.backend,
            json_schema=self.schema,
            prompt=self.prompt,
            debug=True
        )
        
        # Execute with tracing
        with tracer.start_span("jsonformer_generation") as span:
            tracer.set_attribute(span, "prompt", self.prompt)
            tracer.set_attribute(span, "schema_type", self.schema["type"])
            
            # Generate data
            result = jsonformer.generate_data()
            
            tracer.add_event(span, "generation_completed")
            tracer.set_attribute(span, "result_type", type(result).__name__)
            tracer.set_status(span, StatusCode.OK)
            
        # Verify we got a result
        self.assertIsNotNone(result)
        # Since we're using DummyBackend, we expect a dict with the schema properties
        self.assertIsInstance(result, dict)


if __name__ == "__main__":
    unittest.main()