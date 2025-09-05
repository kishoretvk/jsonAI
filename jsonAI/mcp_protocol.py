"""
Enhanced MCP protocol handlers for JsonAI.

This module provides comprehensive Model Context Protocol (MCP) 
integration with request/response translation, dynamic tool discovery,
and secure authentication capabilities.
"""

import requests
import aiohttp
from aiohttp import ClientTimeout
from typing import Dict, Any, Optional, List, Union, Callable, cast
import json
import logging
from dataclasses import dataclass, field
from enum import Enum
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)


class MCPMessageType(Enum):
    """Types of MCP messages."""
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    ERROR = "error"


class MCPErrorType(Enum):
    """Types of MCP errors."""
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    SERVER_ERROR = -32000


@dataclass
class MCPMessage:
    """Represents an MCP message."""
    jsonrpc: str = "2.0"
    id: Optional[str] = None
    method: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=datetime.now)


class MCPProtocolHandler:
    """Handles MCP protocol messages with request/response translation."""
    
    def __init__(self, base_url: str, auth_token: Optional[str] = None, timeout: int = 30):
        self.base_url: str = base_url.rstrip('/')
        self.timeout: int = timeout
        self.headers: Dict[str, str] = {"Content-Type": "application/json"}
        if auth_token is not None:
            self.headers["Authorization"] = f"Bearer {auth_token}"
        self.tools: Dict[str, Dict[str, Any]] = {}
        self.servers: List[str] = []
        
    def discover_tools(self, server_name: Optional[str] = None) -> Dict[str, Any]:
        """Discover available tools from MCP servers."""
        if server_name:
            # Discover tools from a specific server
            return self._discover_tools_from_server(server_name)
        else:
            # Discover tools from all known servers
            all_tools = {}
            for server in self.servers:
                try:
                    server_tools = self._discover_tools_from_server(server)
                    all_tools.update(server_tools)
                except Exception as e:
                    logger.warning(f"Failed to discover tools from server {server}: {e}")
            return all_tools
            
    def _discover_tools_from_server(self, server_name: str) -> Dict[str, Any]:
        """Discover tools from a specific server."""
        url = f"{self.base_url}/{server_name}/tools"
        try:
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            tools_data = response.json()
            
            # Register discovered tools
            if isinstance(tools_data, dict) and "tools" in tools_data:
                for tool in tools_data["tools"]:
                    if isinstance(tool, dict) and "name" in tool:
                        tool_name = tool["name"]
                        self.tools[tool_name] = {
                            "server": server_name,
                            "definition": tool
                        }
                        
            # Add server to known servers if not already present
            if server_name not in self.servers:
                self.servers.append(server_name)
                
            return tools_data
        except requests.RequestException as e:
            logger.error(f"Failed to discover tools from server {server_name}: {e}")
            raise ValueError(f"Failed to discover tools from server '{server_name}': {e}")
            
    def register_tool(self, tool_name: str, server_name: str, tool_definition: Dict[str, Any]) -> None:
        """Register a tool manually."""
        self.tools[tool_name] = {
            "server": server_name,
            "definition": tool_definition
        }
        if server_name not in self.servers:
            self.servers.append(server_name)
            
    def get_tool(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get a registered tool."""
        return self.tools.get(tool_name)
        
    def list_tools(self) -> List[str]:
        """List all registered tools."""
        return list(self.tools.keys())
        
    def create_request(self, method: str, params: Optional[Dict[str, Any]] = None) -> MCPMessage:
        """Create an MCP request message."""
        return MCPMessage(
            id=str(uuid.uuid4()),
            method=method,
            params=params or {}
        )
        
    def create_response(self, request_id: str, result: Dict[str, Any]) -> MCPMessage:
        """Create an MCP response message."""
        return MCPMessage(
            id=request_id,
            result=result
        )
        
    def create_error_response(self, request_id: Optional[str], error_type: MCPErrorType,
                              message: str, data: Optional[Any] = None) -> MCPMessage:
        """Create an MCP error response message."""
        error_data = {
            "code": error_type.value,
            "message": message
        }
        if data is not None:
            error_data["data"] = data
            
        return MCPMessage(
            id=request_id,
            error=error_data
        )
        
    def serialize_message(self, message: MCPMessage) -> str:
        """Serialize an MCP message to JSON."""
        message_dict = {
            "jsonrpc": message.jsonrpc
        }
        
        if message.id is not None:
            message_dict["id"] = message.id
            
        if message.method is not None:
            message_dict["method"] = message.method
            
        if message.params is not None:
            message_dict["params"] = message.params
            
        if message.result is not None:
            message_dict["result"] = message.result
            
        if message.error is not None:
            message_dict["error"] = message.error
            
        return json.dumps(message_dict, default=str)
        
    def deserialize_message(self, message_str: str) -> MCPMessage:
        """Deserialize an MCP message from JSON."""
        try:
            data = json.loads(message_str)
            return MCPMessage(
                jsonrpc=data.get("jsonrpc", "2.0"),
                id=data.get("id"),
                method=data.get("method"),
                params=data.get("params"),
                result=data.get("result"),
                error=data.get("error"),
                timestamp=datetime.now()
            )
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse MCP message: {e}")
            
    def translate_request(self, method: str, params: Dict[str, Any]) -> MCPMessage:
        """Translate a method call to an MCP request."""
        return self.create_request(method, params)
        
    def translate_response(self, message: MCPMessage) -> Any:
        """Translate an MCP response to a native response."""
        if message.error is not None:
            error_code = message.error.get("code", MCPErrorType.INTERNAL_ERROR.value)
            error_message = message.error.get("message", "Unknown error")
            raise ValueError(f"MCP Error {error_code}: {error_message}")
            
        if message.result is not None:
            return message.result
            
        return None
        
    def call_tool_sync(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool synchronously with MCP protocol handling."""
        # Get tool information
        tool_info = self.get_tool(tool_name)
        if not tool_info:
            raise ValueError(f"Tool '{tool_name}' not registered")
            
        server_name = tool_info["server"]
        tool_definition = tool_info["definition"]
        
        # Validate arguments against tool definition
        self._validate_tool_args(tool_definition, args)
        
        # Create MCP request
        request = self.create_request(f"tools/{tool_name}", args)
        request_json = self.serialize_message(request)
        
        # Send request
        url = f"{self.base_url}/{server_name}/{tool_name}"
        try:
            response = requests.post(
                url, 
                data=request_json, 
                headers=self.headers, 
                timeout=self.timeout
            )
            response.raise_for_status()
            response_data = response.json()
            
            # Parse response
            if isinstance(response_data, dict):
                response_message = self.deserialize_message(json.dumps(response_data))
                return self.translate_response(response_message) or {}
            else:
                return {"result": response_data}
                
        except requests.RequestException as e:
            error_response = self.create_error_response(
                request.id, 
                MCPErrorType.INTERNAL_ERROR, 
                f"Failed to call tool '{tool_name}': {e}"
            )
            raise ValueError(self.serialize_message(error_response))
            
    async def call_tool_async(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool asynchronously with MCP protocol handling."""
        # Get tool information
        tool_info = self.get_tool(tool_name)
        if not tool_info:
            raise ValueError(f"Tool '{tool_name}' not registered")
            
        server_name = tool_info["server"]
        tool_definition = tool_info["definition"]
        
        # Validate arguments against tool definition
        self._validate_tool_args(tool_definition, args)
        
        # Create MCP request
        request = self.create_request(f"tools/{tool_name}", args)
        request_json = self.serialize_message(request)
        
        # Send request
        url = f"{self.base_url}/{server_name}/{tool_name}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    data=request_json,
                    headers=self.headers,
                    timeout=ClientTimeout(total=float(self.timeout))
                ) as response:
                    response.raise_for_status()
                    response_data = await response.json()
                    
                    # Parse response
                    if isinstance(response_data, dict):
                        response_message = self.deserialize_message(json.dumps(response_data))
                        return self.translate_response(response_message) or {}
                    else:
                        return {"result": response_data}
                        
        except aiohttp.ClientError as e:
            error_response = self.create_error_response(
                request.id, 
                MCPErrorType.INTERNAL_ERROR, 
                f"Failed to call tool '{tool_name}': {e}"
            )
            raise ValueError(self.serialize_message(error_response))
            
    def _validate_tool_args(self, tool_definition: Dict[str, Any], args: Dict[str, Any]) -> None:
        """Validate tool arguments against tool definition."""
        # This is a simplified validation - in a real implementation,
        # this would use JSON Schema validation or similar
        required_params = tool_definition.get("parameters", {}).get("required", [])
        for param in required_params:
            if param not in args:
                raise ValueError(f"Missing required parameter: {param}")
                
    @staticmethod
    def create_default_handler() -> 'MCPProtocolHandler':
        """Create a default MCP protocol handler."""
        return MCPProtocolHandler(
            base_url="http://localhost:8080",
            auth_token=None
        )
