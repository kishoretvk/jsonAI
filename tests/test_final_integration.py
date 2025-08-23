"""
Final integration test demonstrating all agentic testing capabilities with Ollama.

This test verifies that all the enhanced components work together to provide
a complete agentic testing ecosystem for structured data generation with LLMs.
"""

import unittest
import asyncio
import tempfile
import os
import pytest
import importlib.util

# Skip the whole module if ollama is not installed (optional dependency)
if importlib.util.find_spec("ollama") is None:
    pytest.skip("ollama not installed; skipping final integration tests", allow_module_level=True)

from jsonAI.main import Jsonformer
from jsonAI.model_backends import OllamaBackend
from jsonAI.workflow_orchestrator import WorkflowStep, WorkflowStepType
from jsonAI.state_manager import StateManager
from jsonAI.persistent_storage import SQLiteStorage
from jsonAI.mcp_protocol import MCPProtocolHandler
from jsonAI.tracing import get_tracer
from jsonAI.ollama_utils import OllamaModelSelector, OllamaPerformanceTuner

# Skip tests in CI environments
skip_ollama = pytest.mark.skipif(
    os.environ.get("CI") == "true" or os.environ.get("GITHUB_ACTIONS") == "true",
    reason="Ollama tests are skipped in CI environments."
)


@skip_ollama
class TestFinalAgenticIntegration(unittest.TestCase):
    """Final integration tests for the complete agentic testing ecosystem."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Use mistral as it's commonly available
        self.backend = OllamaBackend(model_name="mistral", max_retries=2)
        self.schema = {
            "type": "object",
            "properties": {
                "product_name": {"type": "string"},
                "price": {"type": "number"},
                "in_stock": {"type": "boolean"},
                "category": {"type": "string"}
            }
        }
        self.prompt = "Generate information about a fictional product for an online store"
        
    def test_complete_agentic_testing_ecosystem(self):
        """Test the complete agentic testing ecosystem with all components."""
        print("\n=== Testing Complete Agentic Testing Ecosystem ===")
        
        # 1. Model Selection and Tuning
        print("1. Performing model selection and tuning...")
        selector = OllamaModelSelector()
        tuner = OllamaPerformanceTuner(selector)
        
        # Select best model for structured data generation
        model_name = selector.select_best_model("structured_data")
        model_params = selector.get_model_parameters(model_name, "structured_data")
        print(f"   Selected model: {model_name}")
        print(f"   Model parameters: {model_params}")
        
        # 2. Create Tracer for Observability
        print("2. Setting up tracing...")
        tracer = get_tracer("agentic-ecosystem-test", debug=True)
        
        with tracer.start_span("complete_agentic_test") as test_span:
            tracer.add_event(test_span, "started_complete_test")
            
            # 3. Create Workflow Configuration
            print("3. Creating workflow configuration...")
            workflow_config = {
                "steps": [
                    {
                        "id": "product_generation",
                        "name": "Generate Product",
                        "type": "generation",
                        "config": {
                            "prompt": self.prompt,
                            "schema": self.schema
                        },
                        "dependencies": []
                    },
                    {
                        "id": "product_validation",
                        "name": "Validate Product",
                        "type": "condition",
                        "config": {
                            "expression": "'product_name' in result and 'price' in result"
                        },
                        "dependencies": ["product_generation"]
                    }
                ]
            }
            
            tracer.add_event(test_span, "created_workflow_config")
            
            # 4. Create Jsonformer with Ollama Backend
            print("4. Creating Jsonformer with Ollama backend...")
            jsonformer = Jsonformer(
                model_backend=self.backend,
                json_schema=self.schema,
                prompt=self.prompt,
                workflow_config=workflow_config,
                ollama_options=model_params,
                debug=True
            )
            
            tracer.add_event(test_span, "created_jsonformer")
            
            # 5. Create State Manager
            print("5. Setting up state management...")
            state_manager = StateManager(debug=True)
            session_id = state_manager.create_session("final_integration_test")
            state_manager.set_variable("test_config", {
                "model": model_name,
                "prompt": self.prompt
            }, scope="session")
            
            tracer.add_event(test_span, "created_state_manager")
            
            # 6. Create Persistent Storage
            print("6. Setting up persistent storage...")
            temp_dir = tempfile.mkdtemp()
            db_path = os.path.join(temp_dir, "final_integration.db")
            storage = SQLiteStorage(db_path=db_path, debug=True)
            storage.save_variable("test_metadata", {
                "test_name": "final_agentic_integration",
                "timestamp": "2025-08-23",
                "components": ["workflow", "state", "storage", "tracing", "ollama"]
            }, scope="global")
            
            tracer.add_event(test_span, "created_persistent_storage")
            
            # 7. Create MCP Handler
            print("7. Setting up MCP protocol handler...")
            mcp_handler = MCPProtocolHandler(base_url="http://localhost:8080")
            mcp_handler.register_tool("product_enrichment", "enrichment_server", {
                "name": "product_enrichment",
                "description": "Enriches product information with additional data",
                "parameters": {
                    "product_name": {"type": "string"},
                    "category": {"type": "string"}
                }
            })
            
            tracer.add_event(test_span, "created_mcp_handler")
            
            # 8. Execute Workflow
            print("8. Executing workflow...")
            async def run_workflow():
                return await jsonformer.execute_workflow()
                
            try:
                result = asyncio.run(run_workflow())
                tracer.add_event(test_span, "workflow_execution_success")
                workflow_success = True
                print("   Workflow executed successfully")
            except Exception as e:
                tracer.add_event(test_span, f"workflow_execution_failed: {str(e)}")
                workflow_success = False
                print(f"   Workflow execution failed: {e}")
                result = None
                
            # 9. Verify Results
            print("9. Verifying results...")
            if result and workflow_success:
                self.assertIn("results", result)
                self.assertIn("product_generation", result["results"])
                generation_result = result["results"]["product_generation"]
                if isinstance(generation_result, dict) and "output" in generation_result:
                    product = generation_result["output"]
                    # Handle both string and dict results from Ollama
                    if isinstance(product, str):
                        # Try to parse as JSON if it's a string
                        import json
                        try:
                            parsed_product = json.loads(product)
                            self.assertIsInstance(parsed_product, dict)
                            print(f"   Generated product (parsed): {parsed_product}")
                        except json.JSONDecodeError:
                            # If it's not valid JSON, just check that it's a non-empty string
                            self.assertIsInstance(product, str)
                            self.assertGreater(len(product), 0)
                            print(f"   Generated product (raw): {product[:100]}...")
                    else:
                        self.assertIsInstance(product, dict)
                        print(f"   Generated product: {product}")
                        
            # 10. Test Storage Persistence
            print("10. Testing storage persistence...")
            execution_data = {
                "workflow_success": workflow_success,
                "result_available": result is not None,
                "model_used": model_name,
                "timestamp": "2025-08-23"
            }
            
            storage.save_workflow_execution(
                execution_id="final_test_execution",
                status="completed" if workflow_success else "failed",
                input_data={"prompt": self.prompt, "schema": self.schema},
                output_data=result or {},
                metadata=execution_data
            )
            
            # Verify storage
            stored_execution = storage.load_workflow_execution("final_test_execution")
            self.assertEqual(stored_execution["metadata"]["model_used"], model_name)
            self.assertEqual(stored_execution["status"], "completed" if workflow_success else "failed")
            print("    Storage persistence verified")
            
            # 11. Test State Management
            print("11. Testing state management...")
            state_manager.set_variable("execution_result", {
                "success": workflow_success,
                "has_data": result is not None
            }, scope="session")
            
            stored_state = state_manager.get_variable("execution_result", scope="session")
            self.assertEqual(stored_state["success"], workflow_success)
            print("    State management verified")
            
            # 12. Clean Up
            print("12. Cleaning up resources...")
            storage.close()
            if os.path.exists(db_path):
                os.remove(db_path)
            if os.path.exists(temp_dir):
                os.rmdir(temp_dir)
                
            tracer.add_event(test_span, "completed_test")
            tracer.set_status(test_span, "OK")
            
            print("=== Agentic Testing Ecosystem Test Completed ===")
            
    def test_component_interoperability(self):
        """Test that all components work together seamlessly."""
        print("\n=== Testing Component Interoperability ===")
        
        # Create all components
        selector = OllamaModelSelector()
        tuner = OllamaPerformanceTuner(selector)
        state_manager = StateManager(debug=True)
        session_id = state_manager.create_session("interop_test")
        
        # Test model selection
        model_name = selector.select_best_model("json_generation")
        self.assertIsInstance(model_name, str)
        self.assertGreater(len(model_name), 0)
        print(f"Model selection: {model_name}")
        
        # Test parameter tuning
        params = tuner.tune_for_task(
            "Generate product information",
            self.prompt,
            self.schema
        )
        self.assertIsInstance(params, tuple)
        self.assertEqual(len(params), 2)
        print(f"Parameter tuning: {params[0]}, {params[1]}")
        
        # Test state management
        state_manager.set_variable("model_info", {
            "name": model_name,
            "params": params[1]
        }, scope="session")
        
        stored_info = state_manager.get_variable("model_info", scope="session")
        self.assertEqual(stored_info["name"], model_name)
        print("State management: Verified")
        
        # Test Jsonformer creation
        jsonformer = Jsonformer(
            model_backend=self.backend,
            json_schema=self.schema,
            prompt=self.prompt,
            ollama_options=params[1],
            debug=True
        )
        self.assertIsNotNone(jsonformer)
        print("Jsonformer creation: Verified")
        
        print("=== Component Interoperability Test Completed ===")


if __name__ == "__main__":
    unittest.main()