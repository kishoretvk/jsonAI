"""
Test cases for the enhanced MCP protocol handler.
"""

import unittest
import json
from unittest.mock import patch, MagicMock
from jsonAI.mcp_protocol import MCPProtocolHandler, MCPMessage, MCPMessageType, MCPErrorType


class TestMCPProtocolHandler(unittest.TestCase):
    """Test cases for MCPProtocolHandler."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mcp_handler = MCPProtocolHandler(base_url="http://localhost:8080")
        
    def test_init(self):
        """Test initialization of MCPProtocolHandler."""
        self.assertEqual(self.mcp_handler.base_url, "http://localhost:8080")
        self.assertEqual(self.mcp_handler.timeout, 30)
        self.assertEqual(self.mcp_handler.headers["Content-Type"], "application/json")
        
    def test_register_and_get_tool(self):
        """Test registering and getting a tool."""
        tool_definition = {
            "name": "test_tool",
            "description": "A test tool",
            "parameters": {
                "param1": {"type": "string"}
            }
        }
        
        self.mcp_handler.register_tool("test_tool", "test_server", tool_definition)
        self.assertIn("test_tool", self.mcp_handler.tools)
        self.assertIn("test_server", self.mcp_handler.servers)
        
        tool = self.mcp_handler.get_tool("test_tool")
        self.assertIsNotNone(tool)
        self.assertEqual(tool["server"], "test_server")
        self.assertEqual(tool["definition"], tool_definition)
        
    def test_list_tools(self):
        """Test listing registered tools."""
        # Register some tools
        self.mcp_handler.register_tool("tool1", "server1", {"name": "tool1"})
        self.mcp_handler.register_tool("tool2", "server2", {"name": "tool2"})
        
        tools = self.mcp_handler.list_tools()
        self.assertEqual(len(tools), 2)
        self.assertIn("tool1", tools)
        self.assertIn("tool2", tools)
        
    def test_create_request(self):
        """Test creating an MCP request."""
        request = self.mcp_handler.create_request("test_method", {"param": "value"})
        self.assertEqual(request.jsonrpc, "2.0")
        self.assertIsNotNone(request.id)
        self.assertEqual(request.method, "test_method")
        self.assertEqual(request.params, {"param": "value"})
        
    def test_create_response(self):
        """Test creating an MCP response."""
        response = self.mcp_handler.create_response("test_id", {"result": "success"})
        self.assertEqual(response.jsonrpc, "2.0")
        self.assertEqual(response.id, "test_id")
        self.assertEqual(response.result, {"result": "success"})
        self.assertIsNone(response.error)
        
    def test_create_error_response(self):
        """Test creating an MCP error response."""
        error_response = self.mcp_handler.create_error_response(
            "test_id", 
            MCPErrorType.METHOD_NOT_FOUND, 
            "Method not found"
        )
        self.assertEqual(error_response.jsonrpc, "2.0")
        self.assertEqual(error_response.id, "test_id")
        self.assertIsNone(error_response.result)
        self.assertIsNotNone(error_response.error)
        self.assertEqual(error_response.error["code"], -32601)
        self.assertEqual(error_response.error["message"], "Method not found")
        
    def test_serialize_message(self):
        """Test serializing an MCP message."""
        message = MCPMessage(
            id="test_id",
            method="test_method",
            params={"param": "value"}
        )
        
        serialized = self.mcp_handler.serialize_message(message)
        self.assertIsInstance(serialized, str)
        
        # Parse back and verify
        parsed = json.loads(serialized)
        self.assertEqual(parsed["jsonrpc"], "2.0")
        self.assertEqual(parsed["id"], "test_id")
        self.assertEqual(parsed["method"], "test_method")
        self.assertEqual(parsed["params"], {"param": "value"})
        
    def test_deserialize_message(self):
        """Test deserializing an MCP message."""
        message_str = json.dumps({
            "jsonrpc": "2.0",
            "id": "test_id",
            "method": "test_method",
            "params": {"param": "value"}
        })
        
        message = self.mcp_handler.deserialize_message(message_str)
        self.assertEqual(message.jsonrpc, "2.0")
        self.assertEqual(message.id, "test_id")
        self.assertEqual(message.method, "test_method")
        self.assertEqual(message.params, {"param": "value"})
        
    def test_translate_request(self):
        """Test translating a method call to an MCP request."""
        request = self.mcp_handler.translate_request("test_method", {"param": "value"})
        self.assertEqual(request.method, "test_method")
        self.assertEqual(request.params, {"param": "value"})
        
    def test_translate_response(self):
        """Test translating an MCP response to a native response."""
        message = MCPMessage(result={"test": "result"})
        result = self.mcp_handler.translate_response(message)
        self.assertEqual(result, {"test": "result"})
        
    def test_translate_response_with_error(self):
        """Test translating an MCP error response."""
        message = MCPMessage(
            error={
                "code": -32601,
                "message": "Method not found"
            }
        )
        
        with self.assertRaises(ValueError) as context:
            self.mcp_handler.translate_response(message)
        self.assertIn("MCP Error -32601: Method not found", str(context.exception))
        
    @patch('requests.post')
    def test_call_tool_sync_success(self, mock_post):
        """Test calling a tool synchronously with success."""
        # Register a tool
        self.mcp_handler.register_tool("test_tool", "test_server", {
            "name": "test_tool",
            "parameters": {}
        })
        
        # Mock the HTTP response
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "jsonrpc": "2.0",
            "id": "test_id",
            "result": {"output": "test result"}
        }
        mock_post.return_value = mock_response
        
        # Call the tool
        result = self.mcp_handler.call_tool_sync("test_tool", {"input": "test"})
        self.assertEqual(result, {"output": "test result"})
        
    @patch('requests.post')
    def test_call_tool_sync_not_registered(self, mock_post):
        """Test calling a tool that is not registered."""
        with self.assertRaises(ValueError) as context:
            self.mcp_handler.call_tool_sync("nonexistent_tool", {})
        self.assertIn("Tool 'nonexistent_tool' not registered", str(context.exception))
        
    @patch('requests.get')
    def test_discover_tools_from_server(self, mock_get):
        """Test discovering tools from a server."""
        # Mock the HTTP response
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "tools": [
                {
                    "name": "discovered_tool",
                    "description": "A discovered tool"
                }
            ]
        }
        mock_get.return_value = mock_response
        
        # Discover tools
        tools = self.mcp_handler._discover_tools_from_server("test_server")
        self.assertIn("tools", tools)
        self.assertEqual(len(tools["tools"]), 1)
        self.assertEqual(tools["tools"][0]["name"], "discovered_tool")
        
        # Verify the tool was registered
        self.assertIn("discovered_tool", self.mcp_handler.tools)
        self.assertIn("test_server", self.mcp_handler.servers)
        
    def test_validate_tool_args(self):
        """Test validating tool arguments."""
        tool_definition = {
            "parameters": {
                "required": ["required_param"]
            }
        }
        
        # Valid arguments
        try:
            self.mcp_handler._validate_tool_args(tool_definition, {"required_param": "value"})
        except ValueError:
            self.fail("_validate_tool_args() raised ValueError unexpectedly for valid args")
            
        # Invalid arguments (missing required param)
        with self.assertRaises(ValueError) as context:
            self.mcp_handler._validate_tool_args(tool_definition, {"other_param": "value"})
        self.assertIn("Missing required parameter: required_param", str(context.exception))


if __name__ == "__main__":
    unittest.main()