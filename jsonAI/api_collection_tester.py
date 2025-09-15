"""
API Collection Testing Framework for JsonAI

This module provides comprehensive API testing capabilities including:
- Postman/Insomnia collection import
- Automated test data generation
- API endpoint testing
- Response validation
- Performance metrics
- Test reporting
"""

import json
import time
import asyncio
import uuid
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
import requests
import aiohttp
from pathlib import Path

from .main import Jsonformer
from .model_backends import DummyBackend
from .schema_validator import SchemaValidator


@dataclass
class APITestRequest:
    """Represents a single API test request"""
    id: str
    name: str
    method: str
    url: str
    headers: Dict[str, str] = field(default_factory=dict)
    body: Optional[Dict[str, Any]] = None
    expected_status: int = 200
    response_schema: Optional[Dict[str, Any]] = None
    test_data_schema: Optional[Dict[str, Any]] = None
    timeout: int = 30


@dataclass
class APITestResult:
    """Represents the result of an API test"""
    request_id: str
    name: str
    success: bool
    status_code: int
    response_time: float
    response_body: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    validation_errors: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class APICollection:
    """Represents a collection of API tests"""
    name: str
    description: str
    base_url: str
    requests: List[APITestRequest] = field(default_factory=list)
    variables: Dict[str, str] = field(default_factory=dict)
    auth: Optional[Dict[str, str]] = None


class APICollectionTester:
    """
    Main class for API collection testing with JsonAI integration
    """
    
    def __init__(self, model_backend=None):
        self.collections: Dict[str, APICollection] = {}
        self.test_results: List[APITestResult] = []
        self.model_backend = model_backend or DummyBackend()
        self.schema_validator = SchemaValidator()
        
    def import_postman_collection(self, collection_path: str) -> str:
        """
        Import a Postman collection file
        
        Args:
            collection_path: Path to Postman collection JSON file
            
        Returns:
            Collection ID for reference
        """
        with open(collection_path, 'r') as f:
            postman_data = json.load(f)
        
        collection = self._parse_postman_collection(postman_data)
        collection_id = str(uuid.uuid4())
        self.collections[collection_id] = collection
        
        return collection_id
    
    def import_openapi_spec(self, spec_path: str) -> str:
        """
        Import an OpenAPI specification file
        
        Args:
            spec_path: Path to OpenAPI spec file (JSON or YAML)
            
        Returns:
            Collection ID for reference
        """
        with open(spec_path, 'r') as f:
            if spec_path.endswith('.yaml') or spec_path.endswith('.yml'):
                import yaml
                openapi_data = yaml.safe_load(f)
            else:
                openapi_data = json.load(f)
        
        collection = self._parse_openapi_spec(openapi_data)
        collection_id = str(uuid.uuid4())
        self.collections[collection_id] = collection
        
        return collection_id
    
    def generate_test_data_for_collection(self, collection_id: str, 
                                        prompt_template: str = None) -> Dict[str, Any]:
        """
        Generate test data for all requests in a collection
        
        Args:
            collection_id: ID of the collection
            prompt_template: Template for generating prompts
            
        Returns:
            Dictionary mapping request IDs to generated test data
        """
        if collection_id not in self.collections:
            raise ValueError(f"Collection {collection_id} not found")
        
        collection = self.collections[collection_id]
        test_data = {}
        
        for request in collection.requests:
            if request.test_data_schema:
                prompt = prompt_template or f"Generate test data for {request.name} API endpoint"
                
                jsonformer = Jsonformer(
                    model_backend=self.model_backend,
                    json_schema=request.test_data_schema,
                    prompt=prompt
                )
                
                generated_data = jsonformer.generate_data()
                test_data[request.id] = generated_data
        
        return test_data
    
    async def run_collection_tests(self, collection_id: str, 
                                 environment: str = "default",
                                 parallel: bool = True,
                                 max_concurrent: int = 5) -> List[APITestResult]:
        """
        Execute all tests in a collection
        
        Args:
            collection_id: ID of the collection to test
            environment: Environment name for variable substitution
            parallel: Whether to run tests in parallel
            max_concurrent: Maximum concurrent requests when parallel=True
            
        Returns:
            List of test results
        """
        if collection_id not in self.collections:
            raise ValueError(f"Collection {collection_id} not found")
        
        collection = self.collections[collection_id]
        
        # Generate test data for all requests
        test_data = self.generate_test_data_for_collection(collection_id)
        
        if parallel:
            semaphore = asyncio.Semaphore(max_concurrent)
            tasks = []
            
            for request in collection.requests:
                task = self._run_single_test_async(
                    request, collection, test_data.get(request.id), semaphore
                )
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter out exceptions and convert to APITestResult
            test_results = []
            for result in results:
                if isinstance(result, APITestResult):
                    test_results.append(result)
                elif isinstance(result, Exception):
                    # Create error result
                    test_results.append(APITestResult(
                        request_id="unknown",
                        name="Error",
                        success=False,
                        status_code=0,
                        response_time=0,
                        error_message=str(result)
                    ))
        else:
            test_results = []
            for request in collection.requests:
                result = await self._run_single_test_async(
                    request, collection, test_data.get(request.id)
                )
                test_results.append(result)
        
        self.test_results.extend(test_results)
        return test_results
    
    async def _run_single_test_async(self, request: APITestRequest, 
                                   collection: APICollection,
                                   test_data: Optional[Dict[str, Any]],
                                   semaphore: Optional[asyncio.Semaphore] = None) -> APITestResult:
        """Run a single API test asynchronously"""
        if semaphore:
            async with semaphore:
                return await self._execute_request(request, collection, test_data)
        else:
            return await self._execute_request(request, collection, test_data)
    
    async def _execute_request(self, request: APITestRequest, 
                             collection: APICollection,
                             test_data: Optional[Dict[str, Any]]) -> APITestResult:
        """Execute a single API request and validate response"""
        start_time = time.time()
        
        # Prepare URL with variable substitution
        url = self._substitute_variables(request.url, collection.variables)
        if not url.startswith('http'):
            url = collection.base_url.rstrip('/') + '/' + url.lstrip('/')
        
        # Prepare headers
        headers = request.headers.copy()
        if collection.auth:
            headers.update(self._prepare_auth_headers(collection.auth))
        
        # Prepare body with test data
        body = request.body
        if test_data and request.method.upper() in ['POST', 'PUT', 'PATCH']:
            body = test_data
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method=request.method,
                    url=url,
                    headers=headers,
                    json=body,
                    timeout=aiohttp.ClientTimeout(total=request.timeout)
                ) as response:
                    response_time = time.time() - start_time
                    
                    try:
                        response_body = await response.json()
                    except:
                        response_body = await response.text()
                    
                    # Validate response
                    validation_errors = []
                    success = response.status == request.expected_status
                    
                    if request.response_schema and isinstance(response_body, dict):
                        is_valid, errors = self.schema_validator.validate(
                            response_body, request.response_schema
                        )
                        if not is_valid:
                            success = False
                            validation_errors.extend(errors)
                    
                    return APITestResult(
                        request_id=request.id,
                        name=request.name,
                        success=success,
                        status_code=response.status,
                        response_time=response_time,
                        response_body=response_body,
                        validation_errors=validation_errors
                    )
                    
        except Exception as e:
            response_time = time.time() - start_time
            return APITestResult(
                request_id=request.id,
                name=request.name,
                success=False,
                status_code=0,
                response_time=response_time,
                error_message=str(e)
            )
    
    def generate_test_report(self, format: str = "html", 
                           output_file: Optional[str] = None) -> str:
        """
        Generate a comprehensive test report
        
        Args:
            format: Report format ('html', 'json', 'junit')
            output_file: Optional output file path
            
        Returns:
            Report content as string
        """
        if format.lower() == "html":
            report = self._generate_html_report()
        elif format.lower() == "json":
            report = self._generate_json_report()
        elif format.lower() == "junit":
            report = self._generate_junit_report()
        else:
            raise ValueError(f"Unsupported report format: {format}")
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(report)
        
        return report
    
    def _parse_postman_collection(self, postman_data: Dict[str, Any]) -> APICollection:
        """Parse Postman collection format"""
        info = postman_data.get('info', {})
        
        collection = APICollection(
            name=info.get('name', 'Untitled Collection'),
            description=info.get('description', ''),
            base_url=''
        )
        
        # Parse variables
        if 'variable' in postman_data:
            for var in postman_data['variable']:
                collection.variables[var['key']] = var.get('value', '')
        
        # Parse items (requests)
        items = postman_data.get('item', [])
        for item in items:
            request_data = item.get('request', {})
            if isinstance(request_data, dict):
                request = self._parse_postman_request(item, request_data)
                collection.requests.append(request)
        
        return collection
    
    def _parse_postman_request(self, item: Dict[str, Any], 
                             request_data: Dict[str, Any]) -> APITestRequest:
        """Parse a single Postman request"""
        url_data = request_data.get('url', {})
        if isinstance(url_data, str):
            url = url_data
        else:
            url = url_data.get('raw', '')
        
        headers = {}
        if 'header' in request_data:
            for header in request_data['header']:
                if not header.get('disabled', False):
                    headers[header['key']] = header['value']
        
        body = None
        if 'body' in request_data:
            body_data = request_data['body']
            if body_data.get('mode') == 'raw':
                try:
                    body = json.loads(body_data.get('raw', '{}'))
                except:
                    pass
        
        return APITestRequest(
            id=str(uuid.uuid4()),
            name=item.get('name', 'Untitled Request'),
            method=request_data.get('method', 'GET'),
            url=url,
            headers=headers,
            body=body
        )
    
    def _parse_openapi_spec(self, openapi_data: Dict[str, Any]) -> APICollection:
        """Parse OpenAPI specification format"""
        info = openapi_data.get('info', {})
        servers = openapi_data.get('servers', [])
        base_url = servers[0]['url'] if servers else ''
        
        collection = APICollection(
            name=info.get('title', 'OpenAPI Collection'),
            description=info.get('description', ''),
            base_url=base_url
        )
        
        paths = openapi_data.get('paths', {})
        for path, methods in paths.items():
            for method, operation in methods.items():
                if method.lower() in ['get', 'post', 'put', 'delete', 'patch']:
                    request = self._parse_openapi_operation(path, method, operation)
                    collection.requests.append(request)
        
        return collection
    
    def _parse_openapi_operation(self, path: str, method: str, 
                                operation: Dict[str, Any]) -> APITestRequest:
        """Parse a single OpenAPI operation"""
        # Extract request body schema for test data generation
        test_data_schema = None
        request_body = operation.get('requestBody', {})
        if request_body:
            content = request_body.get('content', {})
            json_content = content.get('application/json', {})
            test_data_schema = json_content.get('schema')
        
        # Extract response schema for validation
        response_schema = None
        responses = operation.get('responses', {})
        success_response = responses.get('200') or responses.get('201')
        if success_response:
            content = success_response.get('content', {})
            json_content = content.get('application/json', {})
            response_schema = json_content.get('schema')
        
        return APITestRequest(
            id=str(uuid.uuid4()),
            name=operation.get('operationId', f"{method.upper()} {path}"),
            method=method.upper(),
            url=path,
            test_data_schema=test_data_schema,
            response_schema=response_schema
        )
    
    def _substitute_variables(self, text: str, variables: Dict[str, str]) -> str:
        """Substitute variables in text using {{variable}} format"""
        for key, value in variables.items():
            text = text.replace(f"{{{{{key}}}}}", value)
        return text
    
    def _prepare_auth_headers(self, auth: Dict[str, str]) -> Dict[str, str]:
        """Prepare authentication headers"""
        headers = {}
        auth_type = auth.get('type', '')
        
        if auth_type == 'bearer':
            token = auth.get('token', '')
            headers['Authorization'] = f"Bearer {token}"
        elif auth_type == 'basic':
            import base64
            username = auth.get('username', '')
            password = auth.get('password', '')
            credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
            headers['Authorization'] = f"Basic {credentials}"
        elif auth_type == 'apikey':
            key = auth.get('key', '')
            value = auth.get('value', '')
            headers[key] = value
        
        return headers
    
    def _generate_html_report(self) -> str:
        """Generate HTML test report"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r.success)
        failed_tests = total_tests - passed_tests
        avg_response_time = sum(r.response_time for r in self.test_results) / total_tests if total_tests > 0 else 0
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>JsonAI API Test Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .summary {{ background: #f5f5f5; padding: 15px; margin-bottom: 20px; border-radius: 5px; }}
                .test-result {{ margin-bottom: 15px; padding: 10px; border-radius: 5px; }}
                .success {{ background: #d4edda; border-left: 4px solid #28a745; }}
                .failure {{ background: #f8d7da; border-left: 4px solid #dc3545; }}
                .metrics {{ display: flex; gap: 20px; margin-bottom: 20px; }}
                .metric {{ text-align: center; }}
            </style>
        </head>
        <body>
            <h1>JsonAI API Test Report</h1>
            <div class="summary">
                <h2>Test Summary</h2>
                <div class="metrics">
                    <div class="metric">
                        <h3>{total_tests}</h3>
                        <p>Total Tests</p>
                    </div>
                    <div class="metric">
                        <h3>{passed_tests}</h3>
                        <p>Passed</p>
                    </div>
                    <div class="metric">
                        <h3>{failed_tests}</h3>
                        <p>Failed</p>
                    </div>
                    <div class="metric">
                        <h3>{avg_response_time:.2f}s</h3>
                        <p>Avg Response Time</p>
                    </div>
                </div>
            </div>
            
            <h2>Test Results</h2>
        """
        
        for result in self.test_results:
            status_class = "success" if result.success else "failure"
            status_text = "PASS" if result.success else "FAIL"
            
            html += f"""
            <div class="test-result {status_class}">
                <h3>{result.name} - {status_text}</h3>
                <p><strong>Status Code:</strong> {result.status_code}</p>
                <p><strong>Response Time:</strong> {result.response_time:.2f}s</p>
                <p><strong>Timestamp:</strong> {result.timestamp}</p>
            """
            
            if result.error_message:
                html += f"<p><strong>Error:</strong> {result.error_message}</p>"
            
            if result.validation_errors:
                html += "<p><strong>Validation Errors:</strong></p><ul>"
                for error in result.validation_errors:
                    html += f"<li>{error}</li>"
                html += "</ul>"
            
            html += "</div>"
        
        html += """
        </body>
        </html>
        """
        
        return html
    
    def _generate_json_report(self) -> str:
        """Generate JSON test report"""
        report_data = {
            "summary": {
                "total_tests": len(self.test_results),
                "passed_tests": sum(1 for r in self.test_results if r.success),
                "failed_tests": sum(1 for r in self.test_results if not r.success),
                "avg_response_time": sum(r.response_time for r in self.test_results) / len(self.test_results) if self.test_results else 0
            },
            "results": [
                {
                    "request_id": r.request_id,
                    "name": r.name,
                    "success": r.success,
                    "status_code": r.status_code,
                    "response_time": r.response_time,
                    "error_message": r.error_message,
                    "validation_errors": r.validation_errors,
                    "timestamp": r.timestamp.isoformat()
                } for r in self.test_results
            ]
        }
        
        return json.dumps(report_data, indent=2)
    
    def _generate_junit_report(self) -> str:
        """Generate JUnit XML test report"""
        total_tests = len(self.test_results)
        failed_tests = sum(1 for r in self.test_results if not r.success)
        total_time = sum(r.response_time for r in self.test_results)
        
        xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<testsuite name="JsonAI API Tests" tests="{total_tests}" failures="{failed_tests}" time="{total_time:.2f}">
"""
        
        for result in self.test_results:
            xml += f"""    <testcase classname="APITest" name="{result.name}" time="{result.response_time:.2f}">
"""
            if not result.success:
                error_msg = result.error_message or "Test failed"
                xml += f"""        <failure message="{error_msg}">
Status Code: {result.status_code}
Validation Errors: {', '.join(result.validation_errors)}
        </failure>
"""
            xml += """    </testcase>
"""
        
        xml += """</testsuite>"""
        
        return xml


# CLI Integration
class APITestingCLI:
    """CLI interface for API collection testing"""
    
    def __init__(self):
        self.tester = APICollectionTester()
    
    def import_collection_command(self, source: str, file_path: str) -> str:
        """CLI command to import API collection"""
        if source.lower() == "postman":
            return self.tester.import_postman_collection(file_path)
        elif source.lower() == "openapi":
            return self.tester.import_openapi_spec(file_path)
        else:
            raise ValueError(f"Unsupported collection source: {source}")
    
    async def run_tests_command(self, collection_id: str, environment: str = "default") -> List[APITestResult]:
        """CLI command to run API tests"""
        return await self.tester.run_collection_tests(collection_id, environment)
    
    def generate_report_command(self, format: str = "html", output: str = None) -> str:
        """CLI command to generate test report"""
        return self.tester.generate_test_report(format, output)