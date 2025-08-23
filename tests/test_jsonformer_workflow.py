"""
Test cases for Jsonformer workflow extension.
"""

import unittest
import asyncio
from jsonAI.main import Jsonformer
from jsonAI.model_backends import DummyBackend


class TestJsonformerWorkflow(unittest.TestCase):
    """Test cases for Jsonformer workflow extension."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.backend = DummyBackend()
        self.schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"}
            }
        }
        self.prompt = "Generate a person profile"
        
    def test_jsonformer_without_workflow(self):
        """Test Jsonformer without workflow configuration."""
        jsonformer = Jsonformer(
            model_backend=self.backend,
            json_schema=self.schema,
            prompt=self.prompt
        )
        
        self.assertIsNone(jsonformer.workflow_config)
        self.assertIsNone(jsonformer.workflow_orchestrator)
        
    def test_jsonformer_with_workflow_config(self):
        """Test Jsonformer with workflow configuration."""
        workflow_config = {
            "steps": [
                {
                    "id": "step1",
                    "name": "Generation Step",
                    "type": "generation",
                    "config": {
                        "prompt": "Generate first object",
                        "schema": {"type": "object"}
                    },
                    "dependencies": []
                }
            ]
        }
        
        jsonformer = Jsonformer(
            model_backend=self.backend,
            json_schema=self.schema,
            prompt=self.prompt,
            workflow_config=workflow_config
        )
        
        self.assertIsNotNone(jsonformer.workflow_config)
        self.assertIsNotNone(jsonformer.workflow_orchestrator)
        self.assertEqual(len(jsonformer.workflow_orchestrator.steps), 1)
        
    def test_workflow_execution_fails_without_config(self):
        """Test that workflow execution fails when no workflow is configured."""
        jsonformer = Jsonformer(
            model_backend=self.backend,
            json_schema=self.schema,
            prompt=self.prompt
        )
        
        async def run_test():
            with self.assertRaises(ValueError) as context:
                await jsonformer.execute_workflow()
            self.assertIn("No workflow configuration provided", str(context.exception))
        
        asyncio.run(run_test())
        
    def test_workflow_execution_with_config(self):
        """Test workflow execution with a simple configuration."""
        workflow_config = {
            "steps": [
                {
                    "id": "step1",
                    "name": "Generation Step",
                    "type": "generation",
                    "config": {
                        "prompt": "Generate first object",
                        "schema": {"type": "object"}
                    },
                    "dependencies": []
                }
            ]
        }
        
        jsonformer = Jsonformer(
            model_backend=self.backend,
            json_schema=self.schema,
            prompt=self.prompt,
            workflow_config=workflow_config,
            debug=True
        )
        
        async def run_test():
            result = await jsonformer.execute_workflow()
            self.assertIn("results", result)
            self.assertIn("step1", result["results"])
        
        asyncio.run(run_test())


if __name__ == "__main__":
    unittest.main()