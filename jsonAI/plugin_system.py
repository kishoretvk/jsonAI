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
    def get_tools(self) -> Dict[str, Callable]:
        """Return dictionary of tool functions."""
        pass

    @abstractmethod
    def get_tool_schemas(self) -> Dict[str, Dict[str, Any]]:
        """Return JSON schemas for tool parameters."""
        pass


class AgentPlugin(PluginBase):
    """Plugin for custom agents."""

    @abstractmethod
    def create_agent(self, config: Dict[str, Any]) -> Any:
        """Create and return an agent instance."""
        pass

    @abstractmethod
    def get_agent_capabilities(self) -> List[str]:
        """Return list of agent capabilities."""
        pass


class PluginManager:
    """Manages JsonAI plugins."""

    def __init__(self):
        self.plugins: Dict[str, PluginBase] = {}
        self.plugin_types: Dict[str, Type[PluginBase]] = {
            "backend": BackendPlugin,
            "formatter": FormatterPlugin,
            "tool": ToolPlugin,
            "agent": AgentPlugin
        }
        self.discovery_paths: List[Path] = []

    def add_discovery_path(self, path: Path):
        """Add a path for plugin discovery."""
        self.discovery_paths.append(path)

    def register_plugin(self, plugin: PluginBase, config: Optional[Dict[str, Any]] = None):
        """Register a plugin instance."""
        if plugin.name in self.plugins:
            raise ValueError(f"Plugin '{plugin.name}' already registered")

        config = config or {}
        plugin.initialize(config)
        self.plugins[plugin.name] = plugin

    def unregister_plugin(self, plugin_name: str):
        """Unregister a plugin."""
        if plugin_name in self.plugins:
            self.plugins[plugin_name].cleanup()
            del self.plugins[plugin_name]

    def get_plugin(self, plugin_name: str) -> Optional[PluginBase]:
        """Get a registered plugin by name."""
        return self.plugins.get(plugin_name)

    def get_plugins_by_type(self, plugin_type: str) -> List[PluginBase]:
        """Get all plugins of a specific type."""
        base_class = self.plugin_types.get(plugin_type)
        if not base_class:
            return []

        return [p for p in self.plugins.values() if isinstance(p, base_class)]

    def discover_plugins(self):
        """Automatically discover and load plugins from discovery paths."""
        for path in self.discovery_paths:
            if not path.exists():
                continue

            # Discover Python modules in the path
            for finder, name, ispkg in pkgutil.iter_modules([str(path)]):
                try:
                    spec = finder.find_spec(name)
                    if spec and spec.origin:
                        module = importlib.util.spec_from_file_location(name, spec.origin)
                        if module:
                            plugin_module = importlib.util.module_from_spec(module)
                            sys.modules[name] = plugin_module
                            module.loader.exec_module(plugin_module)

                            # Look for plugin classes
                            for attr_name in dir(plugin_module):
                                attr = getattr(plugin_module, attr_name)
                                if (inspect.isclass(attr) and
                                    issubclass(attr, PluginBase) and
                                    attr != PluginBase):
                                    # Auto-register the plugin
                                    plugin_instance = attr()
                                    self.register_plugin(plugin_instance)

                except Exception as e:
                    print(f"Failed to load plugin {name}: {e}")

    async def initialize_async_plugins(self):
        """Initialize any plugins that need async setup."""
        for plugin in self.plugins.values():
            if hasattr(plugin, 'initialize_async'):
                await plugin.initialize_async()


class PluginRegistry:
    """Global registry for plugin management."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._manager = PluginManager()
        return cls._instance

    @property
    def manager(self) -> PluginManager:
        """Get the plugin manager instance."""
        return self._manager

    def setup_default_paths(self):
        """Setup default plugin discovery paths."""
        # Add user plugin directory
        user_plugin_dir = Path.home() / ".jsonai" / "plugins"
        user_plugin_dir.mkdir(parents=True, exist_ok=True)
        self._manager.add_discovery_path(user_plugin_dir)

        # Add system plugin directory
        system_plugin_dir = Path("/usr/local/lib/jsonai/plugins")
        if system_plugin_dir.exists():
            self._manager.add_discovery_path(system_plugin_dir)

    def auto_discover(self):
        """Automatically discover and load all available plugins."""
        self.setup_default_paths()
        self._manager.discover_plugins()


# Convenience functions
def register_plugin(plugin: PluginBase, config: Optional[Dict[str, Any]] = None):
    """Convenience function to register a plugin."""
    registry = PluginRegistry()
    registry.manager.register_plugin(plugin, config)


def get_plugin(plugin_name: str) -> Optional[PluginBase]:
    """Convenience function to get a plugin."""
    registry = PluginRegistry()
    return registry.manager.get_plugin(plugin_name)


def get_plugins_by_type(plugin_type: str) -> List[PluginBase]:
    """Convenience function to get plugins by type."""
    registry = PluginRegistry()
    return registry.manager.get_plugins_by_type(plugin_type)


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
        return ["custom"]</content>
<parameter name="filePath">d:\git\GenerativeJson\jsonAI\plugin_system.py
