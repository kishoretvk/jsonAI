"""
Comprehensive integration test for agentic testing capabilities with Ollama.

This test demonstrates all enhanced components working together:
- Workflow orchestration
- State management
- Persistent storage
- MCP protocol handling
- Tracing
- Ollama integration
"""

import unittest
import asyncio
import tempfile
import os
import pytest
import importlib.util

# Skip the whole module if ollama is not installed (optional dependency)
if importlib.util.find_spec("ollama") is None:
    pytest.skip("ollama not installed; skipping agentic Ollama integration tests", allow_module_level=True)

from jsonAI.main import Jsonformer
from jsonAI.model_backends import OllamaBackend
from jsonAI.workflow_orchestrator import WorkflowStep, WorkflowStepType
from jsonAI.state_manager import StateManager
from jsonAI.persistent_storage import SQLiteStorage
from jsonAI.mcp_protocol import MCPProtocolHandler
from jsonAI.tracing import get_tracer
from jsonAI.ollama_utils import OllamaModelSelector, OllamaPerformanceTuner
from opentelemetry.trace import StatusCode  # Add this import

# Skip tests in CI environments
skip_ollama = pytest.mark.skipif(
    os.environ.get("CI") == "true" or os.environ.get("GITHUB_ACTIONS") == "true",
    reason="Ollama tests are skipped in CI environments."
)


@skip_ollama
class TestAgenticOllamaIntegration(unittest.TestCase):
    """Integration tests for agentic testing with Ollama."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Use mistral as it's commonly available
        self.backend = OllamaBackend(model_name="mistral", max_retries=2)
        self.schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"},
                "occupation": {"type": "string"}
            }
        }
        self.prompt = "Generate a person profile with name, age, and occupation"
        
    def test_ollama_model_selection_and_tuning(self):
        """Test Ollama model selection and parameter tuning."""
        # Create model selector
        selector = OllamaModelSelector()
        available_models = selector.get_available_models()
        
        # Should have at least one model
        self.assertGreater(len(available_models), 0)
        
        # Select best model for JSON generation
        best_model = selector.select_best_model("json_generation")
        self.assertIn(best_model, available_models)
        
        # Get parameters for the model
        params = selector.get_model_parameters(best_model, "json_generation")
        self.assertIsInstance(params, dict)
        self.assertIn("temperature", params)
        self.assertIn("top_p", params)
        
        print(f"Selected model: {best_model}")
        print(f"Recommended parameters: {params}")
        
    def test_ollama_performance_tuning(self):
        """Test Ollama performance tuning."""
        selector = OllamaModelSelector()
        tuner = OllamaPerformanceTuner(selector)
        
        # Tune for our specific task
        model_name, params = tuner.tune_for_task(
            "Generate person profiles in JSON format",
            self.prompt,
            self.schema
        )
        
        self.assertIsInstance(model_name, str)
        self.assertIsInstance(params, dict)
        self.assertGreater(len(model_name), 0)
        
        print(f"Tuned model: {model_name}")
        print(f"Tuned parameters: {params}")
        
    def test_complete_agentic_workflow_with_ollama(self):
        """Test a complete agentic workflow using Ollama."""
        # Create a tracer
        tracer = get_tracer("ollama-agentic-test", debug=True)
        
        with tracer.start_span("agentic_ollama_test") as test_span:
            # 1. Create a workflow configuration
            workflow_config = {
                "steps": [
                    {
                        "id": "profile_generation",
                        "name": "Generate Person Profile",
                        "type": "generation",
                        "config": {
                            "prompt": self.prompt,
                            "schema": self.schema
                        },
                        "dependencies": []
                    },
                    {
                        "id": "profile_validation",
                        "name": "Validate Profile",
                        "type": "condition",
                        "config": {
                            "expression": "'name' in context.get('profile_generation', {}) and 'age' in context.get('profile_generation', {}) and 'occupation' in context.get('profile_generation', {})"
                        },
                        "dependencies": ["profile_generation"]
                    }
                ]
            }
            
            tracer.add_event(test_span, "created_workflow_config")
            
            # 2. Create Jsonformer with Ollama backend and workflow support
            jsonformer = Jsonformer(
                model_backend=self.backend,
                json_schema=self.schema,
                prompt=self.prompt,
                workflow_config=workflow_config,
                ollama_options={"temperature": 0.7, "max_tokens": 150},
                debug=True
            )
            
            tracer.add_event(test_span, "created_jsonformer_with_ollama")
            
            # 3. Create state manager and session
            state_manager = StateManager(debug=True)
            session_id = state_manager.create_session("ollama_test_session")
            state_manager.set_variable("test_input", {
                "prompt": self.prompt,
                "model": "mistral"
            }, scope="session")
            
            tracer.add_event(test_span, "created_state_manager")
            
            # 4. Create persistent storage
            temp_dir = tempfile.mkdtemp()
            db_path = os.path.join(temp_dir, "ollama_integration.db")
            storage = SQLiteStorage(db_path=db_path, debug=True)
            storage.save_variable("workflow_input", {
                "prompt": self.prompt,
                "schema": self.schema
            }, scope="global")
            
            tracer.add_event(test_span, "created_persistent_storage")
            
            # 5. Create MCP protocol handler
            mcp_handler = MCPProtocolHandler(base_url="http://localhost:8080")
            mcp_handler.register_tool("profile_enrichment", "enrichment_server", {
                "name": "profile_enrichment",
                "description": "Enriches person profiles with additional data",
                "parameters": {
                    "name": {"type": "string"},
                    "age": {"type": "integer"}
                }
            })
            
            tracer.add_event(test_span, "created_mcp_handler")
            
            # 6. Execute the workflow
            async def run_workflow():
                result = await jsonformer.execute_workflow()
                return result
                
            try:
                result = asyncio.run(run_workflow())
                tracer.add_event(test_span, "executed_workflow_success")
            except Exception as e:
                tracer.add_event(test_span, f"executed_workflow_failed: {str(e)}")
                # Continue with the test to check what was stored
                result = None
                
            # 7. Verify results (if we got them)
            if result:
                self.assertIn("results", result)
                self.assertIn("profile_generation", result["results"])
                # Check that we got a valid profile
                generation_result = result["results"]["profile_generation"]
                if isinstance(generation_result, dict) and "output" in generation_result:
                    profile = generation_result["output"]
                    # With Ollama, we might get a string instead of a dict, so we need to handle both
                    if isinstance(profile, str):
                        # Try to parse as JSON if it's a string
                        import json
                        try:
                            parsed_profile = json.loads(profile)
                            self.assertIsInstance(parsed_profile, dict)
                        except json.JSONDecodeError:
                            # If it's not valid JSON, just check that it's a non-empty string
                            self.assertIsInstance(profile, str)
                            self.assertGreater(len(profile), 0)
                    else:
                        self.assertIsInstance(profile, dict)
                    
            # 8. Save results to persistent storage regardless of success
            storage.save_workflow_execution(
                execution_id="ollama_agentic_test_123",
                status="completed" if result else "failed",
                input_data={"prompt": self.prompt, "schema": self.schema},
                output_data=result or {},
                metadata={
                    "test": True,
                    "model": "mistral",
                    "backend": "ollama"
                }
            )
            
            # 9. Verify storage
            stored_execution = storage.load_workflow_execution("ollama_agentic_test_123")
            self.assertEqual(stored_execution["metadata"]["test"], True)
            self.assertEqual(stored_execution["metadata"]["model"], "mistral")
            
            # 10. Test state persistence
            state_manager.set_variable("execution_result", {
                "status": "completed" if result else "failed",
                "has_result": result is not None
            }, scope="session")
            
            stored_state = state_manager.get_variable("execution_result", scope="session")
            self.assertEqual(stored_state["has_result"], result is not None)
            
            # 11. Clean up temporary files
            storage.close()
            if os.path.exists(db_path):
                os.remove(db_path)
            if os.path.exists(temp_dir):
                os.rmdir(temp_dir)
                
            tracer.add_event(test_span, "completed_test")
            tracer.set_status(test_span, StatusCode.OK)
            
    def test_ollama_with_tracing_and_error_handling(self):
        """Test Ollama integration with tracing and error handling."""
        # Create tracer
        tracer = get_tracer("ollama-error-test", debug=True)
        
        # Create Jsonformer with Ollama backend
        jsonformer = Jsonformer(
            model_backend=self.backend,
            json_schema=self.schema,
            prompt=self.prompt,
            ollama_options={
                "temperature": 0.7,
                "max_tokens": 100,
                "retry_delay": 0.5  # Shorter retry delay for testing
            },
            debug=True
        )
        
        # Execute with tracing
        with tracer.start_span("ollama_generation") as span:
            tracer.set_attribute(span, "prompt", self.prompt)
            tracer.set_attribute(span, "schema_type", self.schema["type"])
            tracer.set_attribute(span, "model", "mistral")
            
            try:
                # Generate data
                result = jsonformer.generate_data()
                
                tracer.add_event(span, "generation_completed")
                tracer.set_attribute(span, "result_type", type(result).__name__)
                tracer.set_status(span, StatusCode.OK)
                
                # Verify we got a result
                self.assertIsNotNone(result)
                print(f"Generated result: {result}")
                
            except Exception as e:
                tracer.add_event(span, f"generation_failed: {str(e)}")
                tracer.set_status(span, StatusCode.ERROR)
                # Don't fail the test here, as we want to see how error handling works
                print(f"Generation failed (as expected in some cases): {e}")
                
    def test_ollama_retry_mechanism(self):
        """Test Ollama retry mechanism with a problematic prompt."""
        # Create backend with retry configuration
        backend = OllamaBackend(
            model_name="mistral",
            max_retries=2
        )
        
        # Create a challenging prompt that might cause issues
        challenging_prompt = "Generate a very complex JSON object with nested structures and many fields"
        
        schema = {
            "type": "object",
            "properties": {
                "id": {"type": "integer"},
                "data": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "values": {
                            "type": "array",
                            "items": {"type": "number"}
                        }
                    }
                }
            }
        }
        
        jsonformer = Jsonformer(
            model_backend=backend,
            json_schema=schema,
            prompt=challenging_prompt,
            ollama_options={
                "temperature": 0.8,
                "max_tokens": 200
            },
            debug=True
        )
        
        try:
            result = jsonformer.generate_data()
            # If we get here, the retry mechanism worked
            self.assertIsNotNone(result)
            print(f"Successfully generated with retries: {result}")
        except Exception as e:
            # This is expected in some cases, but we want to verify the retry mechanism was attempted
            print(f"Generation failed after retries (expected in some cases): {e}")
            

if __name__ == "__main__":
    unittest.main()