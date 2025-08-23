"""
Test cases for the WorkflowOrchestrator.
"""

import unittest
import asyncio
from jsonAI.workflow_orchestrator import (
    WorkflowOrchestrator, 
    WorkflowStep, 
    WorkflowStepType, 
    WorkflowContext
)


class TestWorkflowOrchestrator(unittest.TestCase):
    """Test cases for WorkflowOrchestrator."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.orchestrator = WorkflowOrchestrator(debug=True)
        
    def test_workflow_step_creation(self):
        """Test creation of workflow steps."""
        step = WorkflowStep(
            id="test_step_1",
            name="Test Generation Step",
            type=WorkflowStepType.GENERATION,
            config={
                "prompt": "Generate a test object",
                "schema": {"type": "object", "properties": {"name": {"type": "string"}}}
            },
            dependencies=[]
        )
        
        self.assertEqual(step.id, "test_step_1")
        self.assertEqual(step.name, "Test Generation Step")
        self.assertEqual(step.type, WorkflowStepType.GENERATION)
        self.assertEqual(step.config["prompt"], "Generate a test object")
        
    def test_add_step(self):
        """Test adding steps to the orchestrator."""
        step = WorkflowStep(
            id="test_step_1",
            name="Test Step",
            type=WorkflowStepType.GENERATION,
            config={"prompt": "Test prompt"},
            dependencies=[]
        )
        
        self.orchestrator.add_step(step)
        self.assertIn("test_step_1", self.orchestrator.steps)
        self.assertEqual(self.orchestrator.steps["test_step_1"], step)
        
    def test_define_workflow(self):
        """Test defining a complete workflow."""
        steps = [
            WorkflowStep(
                id="step_1",
                name="First Step",
                type=WorkflowStepType.GENERATION,
                config={"prompt": "First prompt"},
                dependencies=[]
            ),
            WorkflowStep(
                id="step_2",
                name="Second Step",
                type=WorkflowStepType.GENERATION,
                config={"prompt": "Second prompt"},
                dependencies=["step_1"]
            )
        ]
        
        self.orchestrator.define_workflow(steps)
        self.assertEqual(len(self.orchestrator.steps), 2)
        self.assertIn("step_1", self.orchestrator.steps)
        self.assertIn("step_2", self.orchestrator.steps)
        
    def test_execute_generation_step(self):
        """Test executing a generation step."""
        async def run_test():
            step = WorkflowStep(
                id="gen_step_1",
                name="Generation Step",
                type=WorkflowStepType.GENERATION,
                config={
                    "prompt": "Generate a user profile",
                    "schema": {"type": "object"}
                },
                dependencies=[]
            )
            
            context = WorkflowContext(variables={}, history=[])
            result = await self.orchestrator.execute_step(step, context)
            
            self.assertIn("step_type", result)
            self.assertEqual(result["step_type"], "generation")
            self.assertEqual(result["prompt"], "Generate a user profile")
        
        asyncio.run(run_test())
        
    def test_execute_condition_step(self):
        """Test executing a condition step."""
        async def run_test():
            step = WorkflowStep(
                id="cond_step_1",
                name="Condition Step",
                type=WorkflowStepType.CONDITION,
                config={"expression": "True"},
                dependencies=[]
            )
            
            context = WorkflowContext(variables={}, history=[])
            result = await self.orchestrator.execute_step(step, context)
            
            self.assertTrue(result)
        
        asyncio.run(run_test())
        
    def test_execute_tool_step(self):
        """Test executing a tool call step."""
        async def run_test():
            step = WorkflowStep(
                id="tool_step_1",
                name="Tool Call Step",
                type=WorkflowStepType.TOOL_CALL,
                config={
                    "name": "test_tool",
                    "arguments": {"param1": "value1"}
                },
                dependencies=[]
            )
            
            context = WorkflowContext(variables={}, history=[])
            result = await self.orchestrator.execute_step(step, context)
            
            self.assertEqual(result["tool_name"], "test_tool")
            self.assertEqual(result["arguments"], {"param1": "value1"})
        
        asyncio.run(run_test())
        
    def test_full_workflow_execution(self):
        """Test executing a complete workflow."""
        async def run_test():
            steps = [
                WorkflowStep(
                    id="step_1",
                    name="First Generation",
                    type=WorkflowStepType.GENERATION,
                    config={
                        "prompt": "Generate first object",
                        "schema": {"type": "object"}
                    },
                    dependencies=[]
                ),
                WorkflowStep(
                    id="step_2",
                    name="Second Generation",
                    type=WorkflowStepType.GENERATION,
                    config={
                        "prompt": "Generate second object",
                        "schema": {"type": "object"}
                    },
                    dependencies=["step_1"]
                )
            ]
            
            self.orchestrator.define_workflow(steps)
            result = await self.orchestrator.execute()
            
            self.assertEqual(result.status.name, "COMPLETED")
            self.assertIn("results", result.output)
            self.assertIn("step_1", result.output["results"])
            self.assertIn("step_2", result.output["results"])
        
        asyncio.run(run_test())


if __name__ == "__main__":
    unittest.main()