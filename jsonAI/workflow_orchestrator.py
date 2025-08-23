"""
WorkflowOrchestrator for managing complex agent workflows in JsonAI.

This module provides capabilities for defining, executing, and managing
complex workflows with conditional execution, loops, and parallel processing.
"""

from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass
from enum import Enum
import asyncio
import json
import uuid
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class WorkflowStepType(Enum):
    """Types of workflow steps."""
    GENERATION = "generation"
    CONDITION = "condition"
    LOOP = "loop"
    PARALLEL = "parallel"
    TOOL_CALL = "tool_call"


class ExecutionStatus(Enum):
    """Status of workflow execution."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class WorkflowStep:
    """Represents a single step in a workflow."""
    id: str
    name: str
    type: WorkflowStepType
    config: Dict[str, Any]
    dependencies: List[str]  # List of step IDs this step depends on
    condition: Optional[str] = None  # Condition expression for conditional execution
    on_success: Optional[str] = None  # Next step ID on success
    on_failure: Optional[str] = None  # Next step ID on failure
    retry_count: int = 0
    max_retries: int = 3


@dataclass
class WorkflowContext:
    """Context data that flows through the workflow."""
    variables: Dict[str, Any]
    history: List[Dict[str, Any]]
    current_step: Optional[str] = None
    execution_id: str = ""
    
    
class WorkflowResult:
    """Result of workflow execution."""
    def __init__(self, execution_id: str, status: ExecutionStatus, 
                 output: Dict[str, Any], context: WorkflowContext):
        self.execution_id = execution_id
        self.status = status
        self.output = output
        self.context = context
        self.timestamp = datetime.now()


class WorkflowOrchestrator:
    """Orchestrates complex workflows with conditional execution and parallel processing."""
    
    def __init__(self, debug: bool = False):
        self.debug = debug
        self.steps: Dict[str, WorkflowStep] = {}
        self.context = WorkflowContext(variables={}, history=[])
        self.results: Dict[str, Any] = {}
        self.execution_id = str(uuid.uuid4())
        self.context.execution_id = self.execution_id
        
    def add_step(self, step: WorkflowStep) -> None:
        """Add a step to the workflow."""
        self.steps[step.id] = step
        if self.debug:
            logger.debug(f"Added step {step.id} of type {step.type.value}")
            
    def define_workflow(self, steps: List[WorkflowStep]) -> None:
        """Define the entire workflow with a list of steps."""
        for step in steps:
            self.add_step(step)
        if self.debug:
            logger.debug(f"Defined workflow with {len(steps)} steps")
            
    async def execute_step(self, step: WorkflowStep, context: WorkflowContext) -> Any:
        """Execute a single workflow step."""
        if self.debug:
            logger.debug(f"Executing step {step.id}: {step.name}")
            
        context.current_step = step.id
        context.history.append({
            "step_id": step.id,
            "step_name": step.name,
            "started_at": datetime.now().isoformat()
        })
        
        try:
            result = None
            if step.type == WorkflowStepType.GENERATION:
                result = await self._execute_generation_step(step, context)
            elif step.type == WorkflowStepType.CONDITION:
                result = await self._execute_condition_step(step, context)
            elif step.type == WorkflowStepType.LOOP:
                result = await self._execute_loop_step(step, context)
            elif step.type == WorkflowStepType.PARALLEL:
                result = await self._execute_parallel_step(step, context)
            elif step.type == WorkflowStepType.TOOL_CALL:
                result = await self._execute_tool_step(step, context)
            else:
                raise ValueError(f"Unknown step type: {step.type}")
                
            # Store result in context
            context.variables[step.id] = result
            context.history[-1]["completed_at"] = datetime.now().isoformat()
            context.history[-1]["status"] = "completed"
            
            if self.debug:
                logger.debug(f"Step {step.id} completed with result: {result}")
                
            return result
            
        except Exception as e:
            context.history[-1]["completed_at"] = datetime.now().isoformat()
            context.history[-1]["status"] = "failed"
            context.history[-1]["error"] = str(e)
            
            if self.debug:
                logger.error(f"Step {step.id} failed with error: {str(e)}")
                
            raise
            
    async def _execute_generation_step(self, step: WorkflowStep, context: WorkflowContext) -> Any:
        """Execute a JSON generation step."""
        # This would integrate with Jsonformer in the full implementation
        config = step.config
        prompt = config.get("prompt", "")
        schema = config.get("schema", {})
        
        # For now, return a mock result
        # In the full implementation, this would call Jsonformer
        result = {
            "step_type": "generation",
            "prompt": prompt,
            "output": f"Generated result for: {prompt[:50]}..."
        }
        
        return result
        
    async def _execute_condition_step(self, step: WorkflowStep, context: WorkflowContext) -> bool:
        """Execute a conditional step."""
        # Evaluate condition expression
        condition = step.config.get("expression", "True")
        # In a real implementation, this would use a proper expression evaluator
        try:
            # This is a simplified condition evaluation
            # A real implementation would use a proper expression parser
            result = eval(condition, {"context": context.variables})
            return bool(result)
        except Exception as e:
            logger.error(f"Condition evaluation failed: {e}")
            return False
            
    async def _execute_loop_step(self, step: WorkflowStep, context: WorkflowContext) -> Any:
        """Execute a loop step."""
        # Execute loop logic
        loop_config = step.config
        max_iterations = loop_config.get("max_iterations", 10)
        condition_expr = loop_config.get("condition", "False")
        
        results = []
        for i in range(max_iterations):
            # Check loop condition
            try:
                should_continue = eval(condition_expr, {"context": context.variables, "iteration": i})
                if not should_continue:
                    break
            except Exception:
                break
                
            # Execute loop body (would be defined in config)
            loop_result = {
                "iteration": i,
                "timestamp": datetime.now().isoformat()
            }
            results.append(loop_result)
            
        return results
        
    async def _execute_parallel_step(self, step: WorkflowStep, context: WorkflowContext) -> List[Any]:
        """Execute parallel steps."""
        # Execute multiple steps in parallel
        parallel_steps = step.config.get("steps", [])
        tasks = []
        
        for parallel_step_config in parallel_steps:
            # Create a temporary step for parallel execution
            temp_step = WorkflowStep(
                id=f"parallel_{uuid.uuid4()}",
                name=parallel_step_config.get("name", "parallel_step"),
                type=WorkflowStepType.GENERATION,  # Simplified for now
                config=parallel_step_config,
                dependencies=[]
            )
            task = self.execute_step(temp_step, context)
            tasks.append(task)
            
        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results
        
    async def _execute_tool_step(self, step: WorkflowStep, context: WorkflowContext) -> Any:
        """Execute a tool call step."""
        # Execute tool with provided configuration
        tool_config = step.config
        tool_name = tool_config.get("name")
        tool_args = tool_config.get("arguments", {})
        
        # In a real implementation, this would call the actual tool
        result = {
            "tool_name": tool_name,
            "arguments": tool_args,
            "result": f"Executed tool {tool_name} with args {tool_args}"
        }
        
        return result
        
    async def execute(self) -> WorkflowResult:
        """Execute the entire workflow."""
        if self.debug:
            logger.debug(f"Starting workflow execution: {self.execution_id}")
            
        try:
            # Execute steps in dependency order
            # For simplicity, we'll execute them in the order they were added
            # A real implementation would use a proper dependency resolver
            for step_id, step in self.steps.items():
                # Check if step should be executed based on dependencies
                can_execute = True
                for dep_id in step.dependencies:
                    if dep_id not in self.results:
                        can_execute = False
                        break
                        
                if can_execute:
                    result = await self.execute_step(step, self.context)
                    self.results[step_id] = result
                else:
                    # Mark as skipped
                    self.context.history.append({
                        "step_id": step_id,
                        "step_name": step.name,
                        "status": "skipped",
                        "reason": "dependency not met"
                    })
                    
            # Return final result
            final_output = {
                "workflow_id": self.execution_id,
                "results": self.results,
                "context": {
                    "variables": self.context.variables,
                    "history": self.context.history
                }
            }
            
            if self.debug:
                logger.debug(f"Workflow execution completed: {self.execution_id}")
                
            return WorkflowResult(
                execution_id=self.execution_id,
                status=ExecutionStatus.COMPLETED,
                output=final_output,
                context=self.context
            )
            
        except Exception as e:
            if self.debug:
                logger.error(f"Workflow execution failed: {str(e)}")
                
            return WorkflowResult(
                execution_id=self.execution_id,
                status=ExecutionStatus.FAILED,
                output={"error": str(e)},
                context=self.context
            )