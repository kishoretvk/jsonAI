"""
Test cases for Plugin System.

Tests plugin loading, registration, and extensibility.
"""

import unittest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch

from jsonAI.plugin_system import (
    PluginManager,
    PluginRegistry,
    BackendPlugin,
    FormatterPlugin,
    ToolPlugin,
    AgentPlugin,
    register_plugin,
    get_plugin,
    get_plugins_by_type
)


class MockBackendPlugin(BackendPlugin):
    """Mock backend plugin for testing."""

    @property
    def name(self) -> str:
        return "mock_backend"

    @property
    def version(self) -> str:
        return "1.0.0"

    def initialize(self, config: dict) -> None:
        self.config = config

    def create_backend(self, config: dict):
        return Mock()


class MockFormatterPlugin(FormatterPlugin):
    """Mock formatter plugin for testing."""

    @property
    def name(self) -> str:
        return "mock_formatter"

    @property
    def version(self) -> str:
        return "1.0.0"

    def initialize(self, config: dict) -> None:
        self.config = config

    def format_output(self, data, config: dict) -> str:
        return f"mock_formatted: {data}"

    def get_supported_formats(self) -> list:
        return ["mock"]


class TestPluginManager(unittest.TestCase):
    """Test cases for plugin manager."""

    def setUp(self):
        """Set up test fixtures."""
        self.manager = PluginManager()

    def test_plugin_registration(self):
        """Test plugin registration."""
        plugin = MockBackendPlugin()

        self.manager.register_plugin(plugin)

        self.assertIn("mock_backend", self.manager.plugins)
        self.assertEqual(self.manager.plugins["mock_backend"], plugin)

    def test_duplicate_plugin_registration(self):
        """Test duplicate plugin registration raises error."""
        plugin1 = MockBackendPlugin()
        plugin2 = MockBackendPlugin()

        self.manager.register_plugin(plugin1)

        with self.assertRaises(ValueError):
            self.manager.register_plugin(plugin2)

    def test_plugin_unregistration(self):
        """Test plugin unregistration."""
        plugin = MockBackendPlugin()
        self.manager.register_plugin(plugin)

        self.assertIn("mock_backend", self.manager.plugins)

        self.manager.unregister_plugin("mock_backend")

        self.assertNotIn("mock_backend", self.manager.plugins)

    def test_get_plugin(self):
        """Test getting registered plugin."""
        plugin = MockBackendPlugin()
        self.manager.register_plugin(plugin)

        retrieved = self.manager.get_plugin("mock_backend")
        self.assertEqual(retrieved, plugin)

        # Test non-existent plugin
        self.assertIsNone(self.manager.get_plugin("non_existent"))

    def test_get_plugins_by_type(self):
        """Test getting plugins by type."""
        backend_plugin = MockBackendPlugin()
        formatter_plugin = MockFormatterPlugin()

        self.manager.register_plugin(backend_plugin)
        self.manager.register_plugin(formatter_plugin)

        backend_plugins = self.manager.get_plugins_by_type("backend")
        formatter_plugins = self.manager.get_plugins_by_type("formatter")

        self.assertEqual(len(backend_plugins), 1)
        self.assertEqual(len(formatter_plugins), 1)
        self.assertEqual(backend_plugins["mock_backend"], backend_plugin)
        self.assertEqual(formatter_plugins["mock_formatter"], formatter_plugin)

    def test_discovery_path_management(self):
        """Test discovery path management."""
        test_path = Path("/test/path")
        self.manager.add_discovery_path(test_path)

        self.assertIn(test_path, self.manager.discovery_paths)


class TestPluginRegistry(unittest.TestCase):
    """Test cases for plugin registry."""

    def setUp(self):
        """Set up test fixtures."""
        # Reset singleton for testing
        PluginRegistry._instance = None
        self.registry = PluginRegistry()

    def test_singleton_behavior(self):
        """Test singleton behavior of plugin registry."""
        registry2 = PluginRegistry()
        self.assertEqual(self.registry, registry2)

    def test_registry_plugin_operations(self):
        """Test plugin operations through registry."""
        plugin = MockBackendPlugin()

        self.registry.manager.register_plugin(plugin)

        retrieved = self.registry.manager.get_plugin("mock_backend")
        self.assertEqual(retrieved, plugin)


class TestPluginConvenienceFunctions(unittest.TestCase):
    """Test cases for plugin convenience functions."""

    def setUp(self):
        """Set up test fixtures."""
        # Reset singleton for testing
        PluginRegistry._instance = None

    def test_register_plugin_convenience(self):
        """Test convenience function for plugin registration."""
        plugin = MockBackendPlugin()

        register_plugin(plugin)

        retrieved = get_plugin("mock_backend")
        self.assertEqual(retrieved, plugin)

    def test_get_plugins_by_type_convenience(self):
        """Test convenience function for getting plugins by type."""
        backend_plugin = MockBackendPlugin()
        formatter_plugin = MockFormatterPlugin()

        register_plugin(backend_plugin)
        register_plugin(formatter_plugin)

        backend_plugins = get_plugins_by_type("backend")
        formatter_plugins = get_plugins_by_type("formatter")

        self.assertEqual(len(backend_plugins), 1)
        self.assertEqual(len(formatter_plugins), 1)


class TestPluginInitialization(unittest.TestCase):
    """Test cases for plugin initialization."""

    def test_plugin_initialization(self):
        """Test plugin initialization with config."""
        plugin = MockBackendPlugin()
        config = {"test": "value"}

        plugin.initialize(config)

        self.assertEqual(plugin.config, config)

    def test_plugin_cleanup(self):
        """Test plugin cleanup."""
        plugin = MockBackendPlugin()

        # Should not raise any errors
        plugin.cleanup()


class TestPluginTypes(unittest.TestCase):
    """Test cases for different plugin types."""

    def test_backend_plugin_interface(self):
        """Test backend plugin interface."""
        plugin = MockBackendPlugin()

        self.assertEqual(plugin.name, "mock_backend")
        self.assertEqual(plugin.version, "1.0.0")

        backend = plugin.create_backend({})
        self.assertIsInstance(backend, Mock)

    def test_formatter_plugin_interface(self):
        """Test formatter plugin interface."""
        plugin = MockFormatterPlugin()

        self.assertEqual(plugin.name, "mock_formatter")
        self.assertEqual(plugin.version, "1.0.0")

        formatted = plugin.format_output("test", {})
        self.assertEqual(formatted, "mock_formatted: test")

        formats = plugin.get_supported_formats()
        self.assertEqual(formats, ["mock"])


class TestPluginDiscovery(unittest.TestCase):
    """Test cases for plugin discovery."""

    def setUp(self):
        """Set up test fixtures."""
        self.manager = PluginManager()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_plugin_discovery(self):
        """Test plugin discovery from paths."""
        # Create a mock plugin file
        plugin_content = '''
from jsonAI.plugin_system import BackendPlugin

class TestDiscoveredPlugin(BackendPlugin):
    @property
    def name(self):
        return "discovered_plugin"

    @property
    def version(self):
        return "1.0.0"

    def initialize(self, config):
        pass

    def create_backend(self, config):
        return "mock_backend"
'''

        plugin_file = os.path.join(self.temp_dir, "test_plugin.py")
        with open(plugin_file, 'w') as f:
            f.write(plugin_content)

        # Add path and discover
        self.manager.add_discovery_path(Path(self.temp_dir))

        # Note: Actual discovery would require more complex mocking
        # This tests the path management
        self.assertIn(Path(self.temp_dir), self.manager.discovery_paths)


if __name__ == "__main__":
    unittest.main()
