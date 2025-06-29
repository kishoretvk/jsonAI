from typing import Callable, Dict, Any, Union

class ToolRegistry:
    """
    A central registry for managing and accessing tools that can be called by Jsonformer.
    This includes standard Python functions and MCP (Model Context Protocol) tools.
    """

    def __init__(self):
        """
        Initializes the ToolRegistry.
        """
        self._functions: Dict[str, Callable] = {}
        self._mcp_tools: Dict[str, Dict[str, Any]] = {}

    def register(self, tool: Union[Callable, Dict[str, Any]]) -> None:
        """
        Registers a tool. It can be a Python function or an MCP tool configuration.

        Args:
            tool (Union[Callable, Dict[str, Any]]): The tool to register.

        Raises:
            ValueError: If the tool is invalid or already registered.
        """
        if callable(tool):
            self._register_function(tool)
        elif isinstance(tool, dict):
            self._register_mcp_tool(tool)
        else:
            raise ValueError("Invalid tool type. Must be a callable function or a valid MCP tool dictionary.")

    def _register_function(self, tool: Callable) -> None:
        """
        Registers a standard Python function.

        Args:
            tool (Callable): The function to register.

        Raises:
            ValueError: If the function is already registered.
        """
        tool_name = tool.__name__
        if tool_name in self._functions:
            raise ValueError(f"Tool '{tool_name}' is already registered")
        self._functions[tool_name] = tool

    def _register_mcp_tool(self, tool: Dict[str, Any]) -> None:
        """
        Registers an MCP tool.

        Args:
            tool (Dict[str, Any]): The MCP tool configuration.

        Raises:
            ValueError: If the MCP tool is invalid or already registered.
        """
        if 'name' not in tool or 'server_name' not in tool:
            raise ValueError("Invalid MCP tool configuration. Must include 'name' and 'server_name'.")
        tool_name = tool['name']
        if tool_name in self._mcp_tools:
            raise ValueError(f"MCP tool '{tool_name}' is already registered")
        self._mcp_tools[tool_name] = tool

    def get_tool(self, name: str) -> Union[Callable, Dict[str, Any], None]:
        """
        Retrieves a tool by its registered name.

        Args:
            name (str): The name of the tool to retrieve.

        Returns:
            Union[Callable, Dict[str, Any], None]: The registered tool, or None if not found.
        """
        if name in self._functions:
            return self._functions[name]
        if name in self._mcp_tools:
            return self._mcp_tools[name]
        return None

    def unregister(self, name: str) -> None:
        """
        Unregisters a tool by its name.

        Args:
            name (str): The name of the tool to unregister.

        Raises:
            ValueError: If the tool is not found.
        """
        if name in self._functions:
            del self._functions[name]
        elif name in self._mcp_tools:
            del self._mcp_tools[name]
        else:
            raise ValueError(f"Tool '{name}' is not registered")

    def list_tools(self) -> Dict[str, Union[Callable, Dict[str, Any]]]:
        """
        Lists all registered tools.

        Returns:
            Dict[str, Union[Callable, Dict[str, Any]]]: A dictionary of all registered tools.
        """
        return {**self._functions, **self._mcp_tools}
