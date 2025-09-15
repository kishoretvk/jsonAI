"""
Tests for enhanced workflow automation and API testing features
"""

import asyncio
import json
import pytest
import tempfile
import yaml
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

from jsonAI.enhanced_workflow_engine import (
    WorkflowEngine, WorkflowDefinition, WorkflowStep, 
    WorkflowStepType, WorkflowStatus, WorkflowScheduler
)
from jsonAI.api_collection_tester import (
    APICollectionTester, APITestRequest, APICollection, APITestResult
)
from jsonAI.model_backends import DummyBackend


class TestWorkflowEngine:
    """Test the enhanced workflow engine"""
    
    @pytest.fixture
    def workflow_engine(self):
        return WorkflowEngine(DummyBackend())
    
    @pytest.fixture
    def simple_workflow_data(self):
        return {
            "name": "test_workflow",
            "version": "1.0",
            "description": "Test workflow",
            "variables": {"test_var": "test_value"},
            "steps": [
                {
                    "id": "step1",
                    "name": "Generate Data",
                    "type": "json_generation",
                    "config": {
                        "schema": {"type": "object", "properties": {"name": {"type": "string"}}},
                        "prompt": "Generate test data",
                        "output_variable": "generated_data"
                    }
                },
                {
                    "id": "step2", 
                    "name": "Validate Data",
                    "type": "data_validation",
                    "depends_on": ["step1"],
                    "config": {
                        "data_variable": "generated_data",
                        "schema": {"type": "object", "properties": {"name": {"type": "string"}}}
                    }
                }
            ]
        }
    
    def test_create_workflow(self, workflow_engine, simple_workflow_data):
        """Test workflow creation"""
        workflow_name = workflow_engine.create_workflow(simple_workflow_data)
        assert workflow_name == "test_workflow"
        assert "test_workflow" in workflow_engine.workflows
        
        workflow = workflow_engine.workflows["test_workflow"]
        assert workflow.name == "test_workflow"
        assert workflow.version == "1.0"
        assert len(workflow.steps) == 2
    
    def test_load_workflow_from_file(self, workflow_engine, simple_workflow_data):
        """Test loading workflow from YAML file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(simple_workflow_data, f)
            temp_file = f.name
        
        try:
            workflow_name = workflow_engine.load_workflow_from_file(temp_file)
            assert workflow_name == "test_workflow"
            assert "test_workflow" in workflow_engine.workflows
        finally:
            Path(temp_file).unlink()
    
    @pytest.mark.asyncio
    async def test_execute_workflow(self, workflow_engine, simple_workflow_data):
        """Test workflow execution"""
        workflow_name = workflow_engine.create_workflow(simple_workflow_data)
        execution_id = await workflow_engine.execute_workflow(workflow_name)
        
        assert execution_id is not None
        execution = workflow_engine.get_execution_status(execution_id)
        assert execution is not None
        assert execution.workflow_name == "test_workflow"
        assert execution.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED]
    
    def test_dependency_graph(self, workflow_engine, simple_workflow_data):
        """Test dependency graph building"""
        workflow = workflow_engine._parse_workflow_definition(simple_workflow_data)
        graph = workflow_engine._build_dependency_graph(workflow.steps)
        
        assert "step1" in graph
        assert "step2" in graph
        assert graph["step1"] == []  # No dependencies
        assert graph["step2"] == ["step1"]  # Depends on step1
    
    def test_variable_substitution(self, workflow_engine):
        """Test variable substitution"""
        variables = {"name": "test", "value": 123}
        text = "Hello ${name}, your value is ${value}"
        result = workflow_engine._substitute_variables(text, variables)
        assert result == "Hello test, your value is 123"
    
    def test_condition_evaluation(self, workflow_engine):
        """Test condition evaluation"""
        data = {"status": "active", "count": 5}
        
        # Test equals condition
        condition = {"type": "equals", "field": "status", "value": "active"}
        assert workflow_engine._evaluate_condition(data, condition) is True
        
        # Test greater_than condition
        condition = {"type": "greater_than", "field": "count", "value": 3}
        assert workflow_engine._evaluate_condition(data, condition) is True
        
        # Test contains condition
        condition = {"type": "contains", "field": "status", "value": "act"}
        assert workflow_engine._evaluate_condition(data, condition) is True


class TestAPICollectionTester:
    """Test the API collection testing framework"""
    
    @pytest.fixture
    def api_tester(self):
        return APICollectionTester(DummyBackend())
    
    @pytest.fixture
    def sample_postman_collection(self):
        return {
            "info": {
                "name": "Test Collection",
                "description": "Test API collection"
            },
            "variable": [
                {"key": "baseUrl", "value": "https://api.test.com"}
            ],
            "item": [
                {
                    "name": "Get Users",
                    "request": {
                        "method": "GET",
                        "url": {
                            "raw": "{{baseUrl}}/users",
                            "host": ["{{baseUrl}}"],
                            "path": ["users"]
                        },
                        "header": [
                            {"key": "Accept", "value": "application/json"}
                        ]
                    }
                },
                {
                    "name": "Create User",
                    "request": {
                        "method": "POST",
                        "url": "{{baseUrl}}/users",
                        "header": [
                            {"key": "Content-Type", "value": "application/json"}
                        ],
                        "body": {
                            "mode": "raw",
                            "raw": '{"name": "Test User", "email": "test@example.com"}'
                        }
                    }
                }
            ]
        }
    
    @pytest.fixture
    def sample_openapi_spec(self):
        return {
            "openapi": "3.0.0",
            "info": {
                "title": "Test API",
                "version": "1.0.0"
            },
            "servers": [
                {"url": "https://api.test.com"}
            ],
            "paths": {
                "/users": {
                    "get": {
                        "operationId": "getUsers",
                        "responses": {
                            "200": {
                                "description": "Success",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "id": {"type": "integer"},
                                                    "name": {"type": "string"}
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "post": {
                        "operationId": "createUser",
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "name": {"type": "string"},
                                            "email": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        },
                        "responses": {
                            "201": {
                                "description": "Created"
                            }
                        }
                    }
                }
            }
        }
    
    def test_parse_postman_collection(self, api_tester, sample_postman_collection):
        """Test parsing Postman collection"""
        collection = api_tester._parse_postman_collection(sample_postman_collection)
        
        assert collection.name == "Test Collection"
        assert collection.description == "Test API collection"
        assert "baseUrl" in collection.variables
        assert len(collection.requests) == 2
        
        get_request = collection.requests[0]
        assert get_request.name == "Get Users"
        assert get_request.method == "GET"
        assert "{{baseUrl}}/users" in get_request.url
    
    def test_parse_openapi_spec(self, api_tester, sample_openapi_spec):
        """Test parsing OpenAPI specification"""
        collection = api_tester._parse_openapi_spec(sample_openapi_spec)
        
        assert collection.name == "Test API"
        assert collection.base_url == "https://api.test.com"
        assert len(collection.requests) == 2
        
        # Check that test data schema is extracted for POST request
        post_request = next(r for r in collection.requests if r.method == "POST")
        assert post_request.test_data_schema is not None
        assert "properties" in post_request.test_data_schema
    
    def test_import_postman_collection_from_file(self, api_tester, sample_postman_collection):
        """Test importing Postman collection from file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(sample_postman_collection, f)
            temp_file = f.name
        
        try:
            collection_id = api_tester.import_postman_collection(temp_file)
            assert collection_id is not None
            assert collection_id in api_tester.collections
        finally:
            Path(temp_file).unlink()
    
    def test_import_openapi_spec_from_file(self, api_tester, sample_openapi_spec):
        """Test importing OpenAPI spec from file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(sample_openapi_spec, f)
            temp_file = f.name
        
        try:
            collection_id = api_tester.import_openapi_spec(temp_file)
            assert collection_id is not None
            assert collection_id in api_tester.collections
        finally:
            Path(temp_file).unlink()
    
    def test_generate_test_data_for_collection(self, api_tester, sample_openapi_spec):
        """Test test data generation for collection"""
        collection = api_tester._parse_openapi_spec(sample_openapi_spec)
        collection_id = "test_collection"
        api_tester.collections[collection_id] = collection
        
        test_data = api_tester.generate_test_data_for_collection(collection_id)
        
        # Should generate data for requests with test_data_schema
        post_request = next(r for r in collection.requests if r.method == "POST")
        assert post_request.id in test_data
    
    @pytest.mark.asyncio
    async def test_execute_request(self, api_tester):
        """Test single request execution"""
        request = APITestRequest(
            id="test_request",
            name="Test Request", 
            method="GET",
            url="https://httpbin.org/get",
            expected_status=200
        )
        
        collection = APICollection(
            name="Test Collection",
            description="Test",
            base_url="https://httpbin.org"
        )
        
        # Mock the HTTP request
        with patch('aiohttp.ClientSession.request') as mock_request:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={"success": True})
            mock_request.return_value.__aenter__.return_value = mock_response
            
            result = await api_tester._execute_request(request, collection, None)
            
            assert result.success is True
            assert result.status_code == 200
            assert result.request_id == "test_request"
    
    def test_variable_substitution(self, api_tester):
        """Test variable substitution in URLs and bodies"""
        variables = {"baseUrl": "https://api.test.com", "userId": "123"}
        
        url = "{{baseUrl}}/users/{{userId}}"
        result = api_tester._substitute_variables(url, variables)
        assert result == "https://api.test.com/users/123"
    
    def test_generate_html_report(self, api_tester):
        """Test HTML report generation"""
        # Add some test results
        api_tester.test_results = [
            APITestResult(
                request_id="1",
                name="Test 1",
                success=True,
                status_code=200,
                response_time=1.5
            ),
            APITestResult(
                request_id="2", 
                name="Test 2",
                success=False,
                status_code=500,
                response_time=2.0,
                error_message="Server error"
            )
        ]
        
        report = api_tester._generate_html_report()
        
        assert "JsonAI API Test Report" in report
        assert "Total: 2" in report
        assert "Passed: 1" in report
        assert "Failed: 1" in report
        assert "Test 1 - PASS" in report
        assert "Test 2 - FAIL" in report
    
    def test_generate_json_report(self, api_tester):
        """Test JSON report generation"""
        api_tester.test_results = [
            APITestResult(
                request_id="1",
                name="Test 1", 
                success=True,
                status_code=200,
                response_time=1.5
            )
        ]
        
        report = api_tester._generate_json_report()
        report_data = json.loads(report)
        
        assert "summary" in report_data
        assert "results" in report_data
        assert report_data["summary"]["total_tests"] == 1
        assert report_data["summary"]["passed_tests"] == 1
        assert len(report_data["results"]) == 1


class TestWorkflowScheduler:
    """Test the workflow scheduler"""
    
    @pytest.fixture
    def workflow_engine(self):
        return WorkflowEngine(DummyBackend())
    
    @pytest.fixture
    def scheduler(self, workflow_engine):
        return WorkflowScheduler(workflow_engine)
    
    def test_schedule_workflow(self, scheduler):
        """Test workflow scheduling"""
        schedule_config = {
            "type": "daily",
            "time": "09:00"
        }
        
        schedule_id = scheduler.schedule_workflow("test_workflow", schedule_config)
        
        assert schedule_id is not None
        assert schedule_id in scheduler.scheduled_workflows
        
        scheduled_info = scheduler.scheduled_workflows[schedule_id]
        assert scheduled_info["workflow_name"] == "test_workflow"
        assert scheduled_info["schedule"] == schedule_config
        assert "next_run" in scheduled_info
    
    def test_calculate_next_run_daily(self, scheduler):
        """Test daily schedule calculation"""
        schedule_config = {"type": "daily", "time": "09:00"}
        next_run = scheduler._calculate_next_run(schedule_config)
        
        assert next_run.hour == 9
        assert next_run.minute == 0
    
    def test_calculate_next_run_interval(self, scheduler):
        """Test interval schedule calculation"""
        schedule_config = {"type": "interval", "interval_seconds": 3600}
        next_run = scheduler._calculate_next_run(schedule_config)
        
        # Should be approximately 1 hour from now
        from datetime import datetime, timedelta
        expected = datetime.now() + timedelta(hours=1)
        assert abs((next_run - expected).total_seconds()) < 60  # Within 1 minute


class TestIntegration:
    """Integration tests for workflow and API testing"""
    
    @pytest.mark.asyncio
    async def test_workflow_with_api_testing(self):
        """Test workflow that includes API testing steps"""
        workflow_data = {
            "name": "integration_test_workflow",
            "version": "1.0",
            "steps": [
                {
                    "id": "generate_data",
                    "type": "json_generation",
                    "config": {
                        "schema": {"type": "object", "properties": {"name": {"type": "string"}}},
                        "prompt": "Generate test data",
                        "output_variable": "test_data"
                    }
                },
                {
                    "id": "api_test",
                    "type": "api_request",
                    "depends_on": ["generate_data"],
                    "config": {
                        "method": "POST",
                        "url": "https://httpbin.org/post",
                        "body": "${test_data}",
                        "expected_status": 200
                    }
                }
            ]
        }
        
        engine = WorkflowEngine(DummyBackend())
        workflow_name = engine.create_workflow(workflow_data)
        
        # Mock HTTP request
        with patch('aiohttp.ClientSession.request') as mock_request:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={"success": True})
            mock_request.return_value.__aenter__.return_value = mock_response
            
            execution_id = await engine.execute_workflow(workflow_name)
            execution = engine.get_execution_status(execution_id)
            
            assert execution.status == WorkflowStatus.COMPLETED
            assert len(execution.step_results) == 2
            assert all(result.status == WorkflowStatus.COMPLETED 
                      for result in execution.step_results.values())


if __name__ == "__main__":
    pytest.main([__file__])