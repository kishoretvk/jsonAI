"""
Plugin System for JsonAI Extensibility.

This module provides a plugin architecture that allows developers to easily
extend JsonAI with custom backends, formatters, tools, and agents.
"""

import importlib
import inspect
from typing import Dict, Any, List, Type, Optional, Callable
from abc import ABC, abstractmethod
import asyncio
import pkgutil
import sys
from pathlib import Path


class PluginBase(ABC):
    """Base class for all JsonAI plugins."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Plugin name."""
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """Plugin version."""
        pass

    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the plugin with configuration."""
        pass

    def cleanup(self) -> None:
        """Cleanup plugin resources."""
        pass


class BackendPlugin(PluginBase):
    """Plugin for custom model backends."""

    @abstractmethod
    def create_backend(self, config: Dict[str, Any]) -> Any:
        """Create and return a model backend instance."""
        pass


class FormatterPlugin(PluginBase):
    """Plugin for custom output formatters."""

    @abstractmethod
    def format_output(self, data: Any, config: Dict[str, Any]) -> str:
        """Format data according to plugin logic."""
        pass

    @abstractmethod
    def get_supported_formats(self) -> List[str]:
        """Return list of supported output formats."""
        pass


class ToolPlugin(PluginBase):
    """Plugin for custom tools."""

    @abstractmethod
    def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        """Execute a tool with given parameters."""
        pass

    @abstractmethod
    def get_available_tools(self) -> List[str]:
        """Return list of available tools."""
        pass


class AgentPlugin(PluginBase):
    """Plugin for custom agents."""

    @abstractmethod
    def create_agent(self, config: Dict[str, Any]) -> Any:
        """Create and return an agent instance."""
        pass


class PluginManager:
    """Manages plugin loading and registration."""

    def __init__(self):
        self.plugins: Dict[str, PluginBase] = {}
        self.plugin_types: Dict[str, Type[PluginBase]] = {
            "backend": BackendPlugin,
            "formatter": FormatterPlugin,
            "tool": ToolPlugin,
            "agent": AgentPlugin,
        }

    def register_plugin(self, plugin: PluginBase) -> None:
        """Register a plugin instance."""
        self.plugins[plugin.name] = plugin

    def get_plugin(self, name: str) -> Optional[PluginBase]:
        """Get a plugin by name."""
        return self.plugins.get(name)

    def get_plugins_by_type(self, plugin_type: str) -> List[PluginBase]:
        """Get all plugins of a specific type."""
        base_class = self.plugin_types.get(plugin_type)
        if not base_class:
            return []
        return [p for p in self.plugins.values() if isinstance(p, base_class)]

    def discover_plugins(self) -> None:
        """Auto-discover plugins from entry points."""
        # Implementation for auto-discovery
        pass


class PluginRegistry:
    """Registry for managing plugin discovery and loading."""

    def __init__(self):
        self.manager = PluginManager()
        self.default_paths: List[Path] = []

    def setup_default_paths(self) -> None:
        """Set up default plugin search paths."""
        self.default_paths = [
            Path.cwd() / "plugins",
            Path.home() / ".jsonai" / "plugins",
        ]
        for path in self.default_paths:
            path.mkdir(parents=True, exist_ok=True)

    def auto_discover(self) -> None:
        """Auto-discover and load plugins."""
        self.manager.discover_plugins()

    def get_backend(self, name: str) -> Optional[BackendPlugin]:
        """Get a backend plugin by name."""
        plugin = self.manager.get_plugin(name)
        return plugin if isinstance(plugin, BackendPlugin) else None

    def get_formatter(self, name: str) -> Optional[FormatterPlugin]:
        """Get a formatter plugin by name."""
        plugin = self.manager.get_plugin(name)
        return plugin if isinstance(plugin, FormatterPlugin) else None


# Example plugin implementations
class ExampleBackendPlugin(BackendPlugin):
    """Example backend plugin implementation."""

    @property
    def name(self) -> str:
        return "example_backend"

    @property
    def version(self) -> str:
        return "1.0.0"

    def initialize(self, config: Dict[str, Any]) -> None:
        self.config = config

    def create_backend(self, config: Dict[str, Any]) -> Any:
        # Return a mock backend for demonstration
        class MockBackend:
            def generate(self, prompt: str, **kwargs):
                return f"Mock response for: {prompt}"
        return MockBackend()


class ExampleFormatterPlugin(FormatterPlugin):
    """Example formatter plugin implementation."""

    @property
    def name(self) -> str:
        return "example_formatter"

    @property
    def version(self) -> str:
        return "1.0.0"

    def initialize(self, config: Dict[str, Any]) -> None:
        self.config = config

    def format_output(self, data: Any, config: Dict[str, Any]) -> str:
        return f"Custom formatted: {data}"

    def get_supported_formats(self) -> List[str]:
        return ["custom"]


# Global registry instance
_registry = None


def get_plugin_registry() -> PluginRegistry:
    """Get the global plugin registry instance."""
    global _registry
    if _registry is None:
        _registry = PluginRegistry()
    return _registry


def register_plugin(plugin: PluginBase) -> None:
    """Register a plugin globally."""
    registry = get_plugin_registry()
    registry.manager.register_plugin(plugin)


def get_plugin(name: str) -> Optional[PluginBase]:
    """Get a plugin by name from the global registry."""
    registry = get_plugin_registry()
    return registry.manager.get_plugin(name)


def get_plugins_by_type(plugin_type: str) -> List[PluginBase]:
    """Get all plugins of a specific type from the global registry."""
    registry = get_plugin_registry()
    return registry.manager.get_plugins_by_type(plugin_type)
