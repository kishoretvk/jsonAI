"""
Enhanced Workflow Automation Framework for JsonAI

This module provides comprehensive workflow automation capabilities including:
- YAML/JSON workflow definitions
- Conditional branching and loops
- Parallel execution
- Error handling and retry mechanisms
- Workflow scheduling
- Progress monitoring and reporting
"""

import asyncio
import json
import time
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass, field
import yaml
from pathlib import Path

from .main import Jsonformer
from .api_collection_tester import APICollectionTester, APITestResult
from .model_backends import DummyBackend


class WorkflowStepType(Enum):
    """Types of workflow steps"""
    JSON_GENERATION = "json_generation"
    API_REQUEST = "api_request"
    API_TEST_COLLECTION = "api_test_collection"
    DATA_VALIDATION = "data_validation"
    DATA_TRANSFORMATION = "data_transformation"
    CONDITIONAL = "conditional"
    LOOP = "loop"
    PARALLEL = "parallel"
    DELAY = "delay"
    SCRIPT = "script"
    NOTIFICATION = "notification"
    CLEANUP = "cleanup"


class WorkflowStatus(Enum):
    """Workflow execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


@dataclass
class WorkflowStep:
    """Represents a single workflow step"""
    id: str
    name: str
    type: WorkflowStepType
    config: Dict[str, Any] = field(default_factory=dict)
    depends_on: List[str] = field(default_factory=list)
    parallel: bool = False
    retry_count: int = 0
    timeout: int = 300  # 5 minutes default
    on_failure: str = "stop"  # stop, continue, retry, fallback
    fallback_step: Optional[str] = None
    conditions: Optional[Dict[str, Any]] = None


@dataclass
class WorkflowStepResult:
    """Result of a workflow step execution"""
    step_id: str
    status: WorkflowStatus
    output: Any = None
    error: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    execution_time: float = 0.0
    retry_count: int = 0


@dataclass
class WorkflowDefinition:
    """Complete workflow definition"""
    name: str
    version: str
    description: str = ""
    variables: Dict[str, Any] = field(default_factory=dict)
    steps: List[WorkflowStep] = field(default_factory=list)
    error_handling: Dict[str, Any] = field(default_factory=dict)
    schedule: Optional[Dict[str, Any]] = None
    notifications: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowExecution:
    """Represents a workflow execution instance"""
    id: str
    workflow_name: str
    status: WorkflowStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    step_results: Dict[str, WorkflowStepResult] = field(default_factory=dict)
    variables: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None


class WorkflowEngine:
    """
    Enhanced workflow execution engine with advanced features
    """
    
    def __init__(self, model_backend=None):
        self.model_backend = model_backend or DummyBackend()
        self.api_tester = APICollectionTester(self.model_backend)
        self.workflows: Dict[str, WorkflowDefinition] = {}
        self.executions: Dict[str, WorkflowExecution] = {}
        self.step_executors: Dict[WorkflowStepType, Callable] = {
            WorkflowStepType.JSON_GENERATION: self._execute_json_generation,
            WorkflowStepType.API_REQUEST: self._execute_api_request,
            WorkflowStepType.API_TEST_COLLECTION: self._execute_api_test_collection,
            WorkflowStepType.DATA_VALIDATION: self._execute_data_validation,
            WorkflowStepType.DATA_TRANSFORMATION: self._execute_data_transformation,
            WorkflowStepType.CONDITIONAL: self._execute_conditional,
            WorkflowStepType.LOOP: self._execute_loop,
            WorkflowStepType.PARALLEL: self._execute_parallel,
            WorkflowStepType.DELAY: self._execute_delay,
            WorkflowStepType.SCRIPT: self._execute_script,
            WorkflowStepType.NOTIFICATION: self._execute_notification,
            WorkflowStepType.CLEANUP: self._execute_cleanup,
        }
    
    def load_workflow_from_file(self, file_path: str) -> str:
        """
        Load workflow definition from YAML or JSON file
        
        Args:
            file_path: Path to workflow definition file
            
        Returns:
            Workflow ID for reference
        """
        with open(file_path, 'r') as f:
            if file_path.endswith(('.yml', '.yaml')):
                workflow_data = yaml.safe_load(f)
            else:
                workflow_data = json.load(f)
        
        workflow = self._parse_workflow_definition(workflow_data)
        self.workflows[workflow.name] = workflow
        
        return workflow.name
    
    def create_workflow(self, workflow_data: Dict[str, Any]) -> str:
        """
        Create workflow from dictionary definition
        
        Args:
            workflow_data: Workflow definition as dictionary
            
        Returns:
            Workflow ID for reference
        """
        workflow = self._parse_workflow_definition(workflow_data)
        self.workflows[workflow.name] = workflow
        return workflow.name
    
    async def execute_workflow(self, workflow_name: str, 
                             variables: Optional[Dict[str, Any]] = None) -> str:
        """
        Execute a workflow
        
        Args:
            workflow_name: Name of the workflow to execute
            variables: Runtime variables to override defaults
            
        Returns:
            Execution ID for tracking
        """
        if workflow_name not in self.workflows:
            raise ValueError(f"Workflow '{workflow_name}' not found")
        
        workflow = self.workflows[workflow_name]
        execution_id = str(uuid.uuid4())
        
        # Initialize execution
        execution = WorkflowExecution(
            id=execution_id,
            workflow_name=workflow_name,
            status=WorkflowStatus.PENDING,
            start_time=datetime.now(),
            variables={**workflow.variables, **(variables or {})}
        )
        
        self.executions[execution_id] = execution
        
        try:
            # Start execution
            execution.status = WorkflowStatus.RUNNING
            
            # Build dependency graph
            dependency_graph = self._build_dependency_graph(workflow.steps)
            
            # Execute steps in dependency order
            await self._execute_workflow_steps(workflow, execution, dependency_graph)
            
            execution.status = WorkflowStatus.COMPLETED
            execution.end_time = datetime.now()
            
        except Exception as e:
            execution.status = WorkflowStatus.FAILED
            execution.error_message = str(e)
            execution.end_time = datetime.now()
            
            # Handle workflow-level error
            await self._handle_workflow_error(workflow, execution, e)
        
        return execution_id
    
    def get_execution_status(self, execution_id: str) -> Optional[WorkflowExecution]:
        """Get execution status and results"""
        return self.executions.get(execution_id)
    
    def cancel_execution(self, execution_id: str) -> bool:
        """Cancel a running workflow execution"""
        if execution_id in self.executions:
            execution = self.executions[execution_id]
            if execution.status == WorkflowStatus.RUNNING:
                execution.status = WorkflowStatus.CANCELLED
                execution.end_time = datetime.now()
                return True
        return False
    
    def list_workflows(self) -> List[str]:
        """List all available workflows"""
        return list(self.workflows.keys())
    
    def list_executions(self, workflow_name: Optional[str] = None) -> List[WorkflowExecution]:
        """List workflow executions, optionally filtered by workflow name"""
        executions = list(self.executions.values())
        if workflow_name:
            executions = [e for e in executions if e.workflow_name == workflow_name]
        return executions
    
    def _parse_workflow_definition(self, workflow_data: Dict[str, Any]) -> WorkflowDefinition:
        """Parse workflow definition from dictionary"""
        steps = []
        for step_data in workflow_data.get('steps', []):
            step = WorkflowStep(
                id=step_data['id'],
                name=step_data.get('name', step_data['id']),
                type=WorkflowStepType(step_data['type']),
                config=step_data.get('config', {}),
                depends_on=step_data.get('depends_on', []),
                parallel=step_data.get('parallel', False),
                retry_count=step_data.get('retry_count', 0),
                timeout=step_data.get('timeout', 300),
                on_failure=step_data.get('on_failure', 'stop'),
                fallback_step=step_data.get('fallback_step'),
                conditions=step_data.get('conditions')
            )
            steps.append(step)
        
        return WorkflowDefinition(
            name=workflow_data['name'],
            version=workflow_data.get('version', '1.0'),
            description=workflow_data.get('description', ''),
            variables=workflow_data.get('variables', {}),
            steps=steps,
            error_handling=workflow_data.get('error_handling', {}),
            schedule=workflow_data.get('schedule'),
            notifications=workflow_data.get('notifications', {})
        )
    
    def _build_dependency_graph(self, steps: List[WorkflowStep]) -> Dict[str, List[str]]:
        """Build dependency graph for steps"""
        graph = {}
        step_map = {step.id: step for step in steps}
        
        for step in steps:
            graph[step.id] = []
            for dep in step.depends_on:
                if dep in step_map:
                    graph[step.id].append(dep)
        
        return graph
    
    async def _execute_workflow_steps(self, workflow: WorkflowDefinition,
                                    execution: WorkflowExecution,
                                    dependency_graph: Dict[str, List[str]]):
        """Execute workflow steps respecting dependencies"""
        completed_steps = set()
        step_map = {step.id: step for step in workflow.steps}
        
        while len(completed_steps) < len(workflow.steps):
            # Find steps ready to execute (all dependencies completed)
            ready_steps = []
            for step_id, deps in dependency_graph.items():
                if step_id not in completed_steps and all(dep in completed_steps for dep in deps):
                    step = step_map[step_id]
                    
                    # Check conditions if any
                    if self._check_step_conditions(step, execution):
                        ready_steps.append(step)
                    else:
                        completed_steps.add(step_id)  # Skip step due to conditions
            
            if not ready_steps:
                break  # No more steps can be executed
            
            # Group parallel steps
            parallel_steps = [s for s in ready_steps if s.parallel]
            sequential_steps = [s for s in ready_steps if not s.parallel]
            
            # Execute parallel steps concurrently
            if parallel_steps:
                tasks = [self._execute_single_step(step, execution) for step in parallel_steps]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for step, result in zip(parallel_steps, results):
                    if isinstance(result, Exception):
                        execution.step_results[step.id] = WorkflowStepResult(
                            step_id=step.id,
                            status=WorkflowStatus.FAILED,
                            error=str(result)
                        )
                        await self._handle_step_error(step, execution, result)
                    else:
                        completed_steps.add(step.id)
            
            # Execute sequential steps one by one
            for step in sequential_steps:
                try:
                    await self._execute_single_step(step, execution)
                    completed_steps.add(step.id)
                except Exception as e:
                    await self._handle_step_error(step, execution, e)
                    if step.on_failure == 'stop':
                        raise
    
    async def _execute_single_step(self, step: WorkflowStep, execution: WorkflowExecution):
        """Execute a single workflow step"""
        result = WorkflowStepResult(
            step_id=step.id,
            status=WorkflowStatus.RUNNING,
            start_time=datetime.now()
        )
        
        execution.step_results[step.id] = result
        
        try:
            # Execute step with timeout
            executor = self.step_executors.get(step.type)
            if not executor:
                raise ValueError(f"No executor found for step type: {step.type}")
            
            output = await asyncio.wait_for(
                executor(step, execution),
                timeout=step.timeout
            )
            
            result.output = output
            result.status = WorkflowStatus.COMPLETED
            result.end_time = datetime.now()
            result.execution_time = (result.end_time - result.start_time).total_seconds()
            
        except asyncio.TimeoutError:
            result.status = WorkflowStatus.FAILED
            result.error = f"Step timed out after {step.timeout} seconds"
            result.end_time = datetime.now()
            raise
        except Exception as e:
            result.status = WorkflowStatus.FAILED
            result.error = str(e)
            result.end_time = datetime.now()
            raise
    
    def _check_step_conditions(self, step: WorkflowStep, execution: WorkflowExecution) -> bool:
        """Check if step conditions are met"""
        if not step.conditions:
            return True
        
        # Simple condition evaluation (can be extended)
        for condition_type, condition_value in step.conditions.items():
            if condition_type == "variable_equals":
                var_name, expected_value = condition_value.split('=', 1)
                if execution.variables.get(var_name) != expected_value:
                    return False
            elif condition_type == "step_success":
                step_result = execution.step_results.get(condition_value)
                if not step_result or step_result.status != WorkflowStatus.COMPLETED:
                    return False
        
        return True
    
    async def _handle_step_error(self, step: WorkflowStep, execution: WorkflowExecution, error: Exception):
        """Handle step execution error"""
        result = execution.step_results[step.id]
        
        if step.retry_count > result.retry_count:
            # Retry the step
            result.retry_count += 1
            await asyncio.sleep(2 ** result.retry_count)  # Exponential backoff
            await self._execute_single_step(step, execution)
        elif step.fallback_step:
            # Execute fallback step
            fallback_step = next((s for s in self.workflows[execution.workflow_name].steps 
                                if s.id == step.fallback_step), None)
            if fallback_step:
                await self._execute_single_step(fallback_step, execution)
        elif step.on_failure == 'continue':
            # Continue with next steps
            pass
        else:
            # Stop workflow
            raise error
    
    async def _handle_workflow_error(self, workflow: WorkflowDefinition,
                                   execution: WorkflowExecution, error: Exception):
        """Handle workflow-level error"""
        # Send notifications if configured
        if workflow.notifications.get('on_failure'):
            await self._send_notification(
                workflow.notifications['on_failure'],
                f"Workflow '{workflow.name}' failed: {str(error)}"
            )
    
    # Step Executors
    
    async def _execute_json_generation(self, step: WorkflowStep, execution: WorkflowExecution) -> Dict[str, Any]:
        """Execute JSON generation step"""
        config = step.config
        schema = config.get('schema', {})
        prompt = config.get('prompt', '')
        
        # Substitute variables in prompt
        prompt = self._substitute_variables(prompt, execution.variables)
        
        jsonformer = Jsonformer(
            model_backend=self.model_backend,
            json_schema=schema,
            prompt=prompt,
            **config.get('jsonformer_options', {})
        )
        
        result = jsonformer.generate_data()
        
        # Store result in execution variables for use by other steps
        var_name = config.get('output_variable', f"{step.id}_output")
        execution.variables[var_name] = result
        
        return result
    
    async def _execute_api_request(self, step: WorkflowStep, execution: WorkflowExecution) -> Dict[str, Any]:
        """Execute API request step"""
        import aiohttp
        
        config = step.config
        method = config.get('method', 'GET')
        url = self._substitute_variables(config.get('url', ''), execution.variables)
        headers = config.get('headers', {})
        body = config.get('body')
        
        # Substitute variables in body if it's a string template
        if isinstance(body, str):
            body = self._substitute_variables(body, execution.variables)
        
        async with aiohttp.ClientSession() as session:
            async with session.request(method, url, headers=headers, json=body) as response:
                result = {
                    'status_code': response.status,
                    'headers': dict(response.headers),
                    'body': await response.json() if response.content_type == 'application/json' else await response.text()
                }
                
                # Store result in execution variables
                var_name = config.get('output_variable', f"{step.id}_output")
                execution.variables[var_name] = result
                
                return result
    
    async def _execute_api_test_collection(self, step: WorkflowStep, execution: WorkflowExecution) -> List[APITestResult]:
        """Execute API test collection step"""
        config = step.config
        collection_path = config.get('collection_path')
        collection_type = config.get('collection_type', 'postman')
        environment = config.get('environment', 'default')
        
        # Import collection
        if collection_type == 'postman':
            collection_id = self.api_tester.import_postman_collection(collection_path)
        elif collection_type == 'openapi':
            collection_id = self.api_tester.import_openapi_spec(collection_path)
        else:
            raise ValueError(f"Unsupported collection type: {collection_type}")
        
        # Run tests
        results = await self.api_tester.run_collection_tests(collection_id, environment)
        
        # Store results in execution variables
        var_name = config.get('output_variable', f"{step.id}_output")
        execution.variables[var_name] = results
        
        return results
    
    async def _execute_data_validation(self, step: WorkflowStep, execution: WorkflowExecution) -> Dict[str, Any]:
        """Execute data validation step"""
        config = step.config
        data_variable = config.get('data_variable')
        schema = config.get('schema')
        
        if not data_variable or data_variable not in execution.variables:
            raise ValueError(f"Data variable '{data_variable}' not found")
        
        data = execution.variables[data_variable]
        
        from .schema_validator import SchemaValidator
        validator = SchemaValidator()
        is_valid, errors = validator.validate(data, schema)
        
        result = {
            'valid': is_valid,
            'errors': errors,
            'data': data
        }
        
        if not is_valid and config.get('fail_on_invalid', True):
            raise ValueError(f"Data validation failed: {errors}")
        
        return result
    
    async def _execute_data_transformation(self, step: WorkflowStep, execution: WorkflowExecution) -> Any:
        """Execute data transformation step"""
        config = step.config
        input_variable = config.get('input_variable')
        transformation = config.get('transformation', {})
        
        if not input_variable or input_variable not in execution.variables:
            raise ValueError(f"Input variable '{input_variable}' not found")
        
        data = execution.variables[input_variable]
        
        # Simple transformation operations
        if transformation.get('type') == 'filter':
            # Filter array based on condition
            condition = transformation.get('condition', {})
            if isinstance(data, list):
                data = [item for item in data if self._evaluate_condition(item, condition)]
        elif transformation.get('type') == 'map':
            # Transform each item in array
            mapping = transformation.get('mapping', {})
            if isinstance(data, list):
                data = [self._apply_mapping(item, mapping) for item in data]
        elif transformation.get('type') == 'aggregate':
            # Aggregate data
            operation = transformation.get('operation')
            if operation == 'count' and isinstance(data, list):
                data = len(data)
            elif operation == 'sum' and isinstance(data, list):
                data = sum(data)
        
        # Store result
        output_variable = config.get('output_variable', f"{step.id}_output")
        execution.variables[output_variable] = data
        
        return data
    
    async def _execute_conditional(self, step: WorkflowStep, execution: WorkflowExecution) -> str:
        """Execute conditional step"""
        config = step.config
        condition = config.get('condition', {})
        
        if self._evaluate_condition(execution.variables, condition):
            return "condition_met"
        else:
            return "condition_not_met"
    
    async def _execute_loop(self, step: WorkflowStep, execution: WorkflowExecution) -> List[Any]:
        """Execute loop step"""
        config = step.config
        loop_variable = config.get('loop_variable')
        loop_data = execution.variables.get(loop_variable, [])
        loop_steps = config.get('steps', [])
        
        results = []
        for item in loop_data:
            # Set current item as variable
            execution.variables['_current_item'] = item
            
            # Execute loop steps (simplified)
            for loop_step_config in loop_steps:
                # This is a simplified implementation
                # In practice, you'd parse and execute these as full workflow steps
                pass
        
        return results
    
    async def _execute_parallel(self, step: WorkflowStep, execution: WorkflowExecution) -> List[Any]:
        """Execute parallel step"""
        config = step.config
        parallel_steps = config.get('steps', [])
        
        # Execute all parallel steps concurrently
        tasks = []
        for parallel_step_config in parallel_steps:
            # This is a simplified implementation
            # In practice, you'd parse and execute these as full workflow steps
            pass
        
        results = await asyncio.gather(*tasks)
        return results
    
    async def _execute_delay(self, step: WorkflowStep, execution: WorkflowExecution) -> None:
        """Execute delay step"""
        config = step.config
        delay_seconds = config.get('seconds', 1)
        await asyncio.sleep(delay_seconds)
    
    async def _execute_script(self, step: WorkflowStep, execution: WorkflowExecution) -> Any:
        """Execute script step (simplified)"""
        config = step.config
        script = config.get('script', '')
        language = config.get('language', 'python')
        
        if language == 'python':
            # Very basic Python script execution (security risk in production)
            local_vars = execution.variables.copy()
            exec(script, {}, local_vars)
            
            # Update execution variables with changes
            execution.variables.update(local_vars)
            
            return local_vars.get('result')
        else:
            raise ValueError(f"Unsupported script language: {language}")
    
    async def _execute_notification(self, step: WorkflowStep, execution: WorkflowExecution) -> None:
        """Execute notification step"""
        config = step.config
        message = self._substitute_variables(config.get('message', ''), execution.variables)
        await self._send_notification(config, message)
    
    async def _execute_cleanup(self, step: WorkflowStep, execution: WorkflowExecution) -> None:
        """Execute cleanup step"""
        config = step.config
        cleanup_variables = config.get('variables', [])
        
        for var_name in cleanup_variables:
            execution.variables.pop(var_name, None)
    
    # Helper Methods
    
    def _substitute_variables(self, text: str, variables: Dict[str, Any]) -> str:
        """Substitute variables in text using ${variable} format"""
        import re
        
        def replace_var(match):
            var_name = match.group(1)
            return str(variables.get(var_name, match.group(0)))
        
        return re.sub(r'\$\{([^}]+)\}', replace_var, text)
    
    def _evaluate_condition(self, data: Any, condition: Dict[str, Any]) -> bool:
        """Evaluate a condition against data"""
        condition_type = condition.get('type')
        
        if condition_type == 'equals':
            field = condition.get('field')
            value = condition.get('value')
            if isinstance(data, dict):
                return data.get(field) == value
            else:
                return data == value
        elif condition_type == 'greater_than':
            field = condition.get('field')
            value = condition.get('value')
            if isinstance(data, dict):
                return data.get(field, 0) > value
            else:
                return data > value
        elif condition_type == 'contains':
            field = condition.get('field')
            value = condition.get('value')
            if isinstance(data, dict):
                return value in str(data.get(field, ''))
            else:
                return value in str(data)
        
        return False
    
    def _apply_mapping(self, item: Any, mapping: Dict[str, str]) -> Dict[str, Any]:
        """Apply field mapping to an item"""
        if not isinstance(item, dict):
            return item
        
        result = {}
        for new_field, old_field in mapping.items():
            result[new_field] = item.get(old_field)
        
        return result
    
    async def _send_notification(self, config: Dict[str, Any], message: str):
        """Send notification (simplified implementation)"""
        notification_type = config.get('type')
        
        if notification_type == 'email':
            # Implement email notification
            print(f"EMAIL: {message}")
        elif notification_type == 'slack':
            # Implement Slack notification
            print(f"SLACK: {message}")
        elif notification_type == 'webhook':
            # Implement webhook notification
            import aiohttp
            webhook_url = config.get('url')
            if webhook_url:
                async with aiohttp.ClientSession() as session:
                    await session.post(webhook_url, json={'message': message})
        else:
            print(f"NOTIFICATION: {message}")


class WorkflowScheduler:
    """
    Workflow scheduling and management
    """
    
    def __init__(self, workflow_engine: WorkflowEngine):
        self.engine = workflow_engine
        self.scheduled_workflows: Dict[str, Dict[str, Any]] = {}
        self.running = False
    
    def schedule_workflow(self, workflow_name: str, schedule_config: Dict[str, Any]) -> str:
        """Schedule a workflow for execution"""
        schedule_id = str(uuid.uuid4())
        self.scheduled_workflows[schedule_id] = {
            'workflow_name': workflow_name,
            'schedule': schedule_config,
            'next_run': self._calculate_next_run(schedule_config)
        }
        return schedule_id
    
    def _calculate_next_run(self, schedule_config: Dict[str, Any]) -> datetime:
        """Calculate next run time based on schedule configuration"""
        schedule_type = schedule_config.get('type', 'cron')
        
        if schedule_type == 'interval':
            interval_seconds = schedule_config.get('interval_seconds', 3600)
            return datetime.now() + timedelta(seconds=interval_seconds)
        elif schedule_type == 'daily':
            time_str = schedule_config.get('time', '00:00')
            hour, minute = map(int, time_str.split(':'))
            next_run = datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)
            if next_run <= datetime.now():
                next_run += timedelta(days=1)
            return next_run
        elif schedule_type == 'cron':
            # Simplified cron implementation
            # In practice, use a library like croniter
            return datetime.now() + timedelta(hours=1)
        
        return datetime.now() + timedelta(hours=1)
    
    async def start_scheduler(self):
        """Start the workflow scheduler"""
        self.running = True
        while self.running:
            current_time = datetime.now()
            
            for schedule_id, schedule_info in list(self.scheduled_workflows.items()):
                if current_time >= schedule_info['next_run']:
                    # Execute workflow
                    workflow_name = schedule_info['workflow_name']
                    try:
                        await self.engine.execute_workflow(workflow_name)
                        # Update next run time
                        schedule_info['next_run'] = self._calculate_next_run(schedule_info['schedule'])
                    except Exception as e:
                        print(f"Scheduled workflow '{workflow_name}' failed: {e}")
            
            # Sleep for a minute before checking again
            await asyncio.sleep(60)
    
    def stop_scheduler(self):
        """Stop the workflow scheduler"""
        self.running = False


# CLI Integration for Workflow Management
class WorkflowCLI:
    """CLI interface for workflow management"""
    
    def __init__(self):
        self.engine = WorkflowEngine()
        self.scheduler = WorkflowScheduler(self.engine)
    
    def create_workflow_command(self, config_file: str) -> str:
        """CLI command to create workflow from file"""
        return self.engine.load_workflow_from_file(config_file)
    
    async def run_workflow_command(self, workflow_name: str, variables: Optional[Dict[str, Any]] = None) -> str:
        """CLI command to run workflow"""
        return await self.engine.execute_workflow(workflow_name, variables)
    
    def list_workflows_command(self) -> List[str]:
        """CLI command to list workflows"""
        return self.engine.list_workflows()
    
    def status_command(self, execution_id: str) -> Optional[WorkflowExecution]:
        """CLI command to get execution status"""
        return self.engine.get_execution_status(execution_id)
    
    def schedule_workflow_command(self, workflow_name: str, schedule_config: Dict[str, Any]) -> str:
        """CLI command to schedule workflow"""
        return self.scheduler.schedule_workflow(workflow_name, schedule_config)