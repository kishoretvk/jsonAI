from typing import Callable, Dict, Any, Union

class ToolRegistry:
    """
    A central registry for managing and accessing tools that can be called by Jsonformer.
    This includes standard Python functions and MCP (Model Context Protocol) tools.
    """
    def __init__(self):
        """Initializes the ToolRegistry."""
        self._functions: Dict[str, Callable] = {}
        self._mcp_tools: Dict[str, Dict[str, Any]] = {}

    def register(self, tool: Union[Callable, Dict[str, Any]]):
        """
        Registers a tool. It can be a Python function or an MCP tool configuration.
        
        For a Python function, it's registered by its name.
        For an MCP tool, provide a dictionary with 'name', 'server_name', and 'config'.
        """
        if callable(tool):
            # Register a standard Python function
            tool_name = tool.__name__
            if tool_name in self._functions:
                raise ValueError(f"Tool '{tool_name}' is already registered")
            self._functions[tool_name] = tool
        elif isinstance(tool, dict) and 'name' in tool and 'server_name' in tool:
            # Register an MCP tool
            tool_name = tool['name']
            if tool_name in self._mcp_tools:
                raise ValueError(f"MCP tool '{tool_name}' is already registered")
            self._mcp_tools[tool_name] = tool
        else:
            raise ValueError("Invalid tool type. Must be a callable function or a valid MCP tool dictionary.")

    def get_tool(self, name: str) -> Union[Callable, Dict[str, Any], None]:
        """Retrieves a tool by its registered name."""
        if name in self._functions:
            return self._functions[name]
        if name in self._mcp_tools:
            return self._mcp_tools[name]
        return None
