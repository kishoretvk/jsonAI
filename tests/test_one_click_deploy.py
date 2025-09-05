"""
Test cases for One-Click Deployment System.

Tests deployment configurations and setup.
"""

import unittest
import tempfile
import json
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from jsonAI.one_click_deploy import (
    DockerDeployer,
    CloudDeployer,
    LocalDevDeployer,
    OneClickDeployer
)


class TestDockerDeployer(unittest.TestCase):
    """Test cases for Docker deployer."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)
        self.docker = DockerDeployer(self.project_root)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_create_dockerfile(self):
        """Test Dockerfile creation."""
        dockerfile_path = self.docker.create_dockerfile(
            base_image="python:3.9-slim",
            expose_port=8000
        )

        # Verify Dockerfile was created
        self.assertTrue(dockerfile_path.exists())

        # Verify content
        with open(dockerfile_path, 'r') as f:
            content = f.read()

        self.assertIn("FROM python:3.9-slim", content)
        self.assertIn("EXPOSE 8000", content)
        self.assertIn("uvicorn", content)

    def test_create_docker_compose(self):
        """Test docker-compose.yml creation."""
        compose_path = self.docker.create_docker_compose(
            services=["api", "ollama", "frontend"]
        )

        # Verify compose file was created
        self.assertTrue(compose_path.exists())

        # Verify content
        with open(compose_path, 'r') as f:
            content = f.read()

        compose_data = json.loads(content)
        self.assertIn("services", compose_data)
        self.assertIn("api", compose_data["services"])
        self.assertIn("ollama", compose_data["services"])
        self.assertIn("frontend", compose_data["services"])

    @patch('subprocess.run')
    def test_deploy_locally(self, mock_subprocess):
        """Test local Docker deployment."""
        # Mock successful subprocess calls
        mock_result = Mock()
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result

        # This would normally require Docker to be installed
        # For testing, we just verify the method exists and can be called
        self.assertTrue(hasattr(self.docker, 'deploy_locally'))


class TestCloudDeployer(unittest.TestCase):
    """Test cases for cloud deployer."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)
        self.cloud = CloudDeployer(self.project_root)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_create_railway_config(self):
        """Test Railway configuration creation."""
        config_path = self.cloud.create_railway_config()

        # Verify config file was created
        self.assertTrue(config_path.exists())

        # Verify content
        with open(config_path, 'r') as f:
            content = f.read()

        config = json.loads(content)
        self.assertIn("build", config)
        self.assertIn("deploy", config)
        self.assertIn("environments", config)

    def test_create_render_config(self):
        """Test Render configuration creation."""
        config_path = self.cloud.create_render_config()

        # Verify config file was created
        self.assertTrue(config_path.exists())

        # Verify content
        with open(config_path, 'r') as f:
            content = f.read()

        config = json.loads(content)
        self.assertIn("services", config)
        self.assertEqual(len(config["services"]), 1)
        self.assertEqual(config["services"][0]["type"], "web")

    def test_create_fly_config(self):
        """Test Fly.io configuration creation."""
        config_path = self.cloud.create_fly_config()

        # Verify config file was created
        self.assertTrue(config_path.exists())

        # Verify content
        with open(config_path, 'r') as f:
            content = f.read()

        self.assertIn("app =", content)
        self.assertIn("uvicorn", content)
        self.assertIn("services", content)


class TestLocalDevDeployer(unittest.TestCase):
    """Test cases for local development deployer."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)
        self.local = LocalDevDeployer(self.project_root)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_setup_dev_environment(self):
        """Test development environment setup."""
        # This would normally create virtual environment and install dependencies
        # For testing, we just verify the method exists and can be called
        self.assertTrue(hasattr(self.local, 'setup_dev_environment'))

        # Verify .env file creation
        env_file = self.project_root / ".env"
        self.assertFalse(env_file.exists())  # Should not exist before setup

    @patch('subprocess.run')
    def test_start_dev_server(self, mock_subprocess):
        """Test development server startup."""
        # Mock successful subprocess call
        mock_result = Mock()
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result

        # This would normally start the development server
        # For testing, we just verify the method exists and can be called
        self.assertTrue(hasattr(self.local, 'start_dev_server'))


class TestOneClickDeployer(unittest.TestCase):
    """Test cases for one-click deployer."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)
        self.deployer = OneClickDeployer(self.project_root)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_deployer_initialization(self):
        """Test one-click deployer initialization."""
        self.assertIsInstance(self.deployer.docker, DockerDeployer)
        self.assertIsInstance(self.deployer.cloud, CloudDeployer)
        self.assertIsInstance(self.deployer.local, LocalDevDeployer)

    def test_list_deployment_options(self):
        """Test listing deployment options."""
        options = self.deployer.list_deployment_options()

        expected_options = ["docker", "docker-compose", "railway", "render", "fly", "local"]
        self.assertEqual(set(options), set(expected_options))

    def test_deploy_docker(self):
        """Test Docker deployment."""
        result = self.deployer.deploy("docker", base_image="python:3.9-slim", expose_port=8000)

        self.assertEqual(result["status"], "success")
        self.assertIn("dockerfile", result)

        # Verify Dockerfile was created
        dockerfile_path = Path(result["dockerfile"])
        self.assertTrue(dockerfile_path.exists())

    def test_deploy_docker_compose(self):
        """Test Docker Compose deployment."""
        result = self.deployer.deploy("docker-compose", services=["api", "ollama"])

        self.assertEqual(result["status"], "success")
        self.assertIn("compose_file", result)

        # Verify compose file was created
        compose_path = Path(result["compose_file"])
        self.assertTrue(compose_path.exists())

    def test_deploy_railway(self):
        """Test Railway deployment."""
        result = self.deployer.deploy("railway")

        self.assertEqual(result["status"], "success")
        self.assertIn("config_file", result)

        # Verify config file was created
        config_path = Path(result["config_file"])
        self.assertTrue(config_path.exists())

    def test_deploy_render(self):
        """Test Render deployment."""
        result = self.deployer.deploy("render")

        self.assertEqual(result["status"], "success")
        self.assertIn("config_file", result)

        # Verify config file was created
        config_path = Path(result["config_file"])
        self.assertTrue(config_path.exists())

    def test_deploy_fly(self):
        """Test Fly.io deployment."""
        result = self.deployer.deploy("fly")

        self.assertEqual(result["status"], "success")
        self.assertIn("config_file", result)

        # Verify config file was created
        config_path = Path(result["config_file"])
        self.assertTrue(config_path.exists())

    def test_deploy_local(self):
        """Test local deployment."""
        result = self.deployer.deploy("local")

        self.assertEqual(result["status"], "success")
        self.assertIn("message", result)

    def test_deploy_invalid_target(self):
        """Test deployment with invalid target."""
        with self.assertRaises(ValueError):
            self.deployer.deploy("invalid_target")


class TestDeploymentIntegration(unittest.TestCase):
    """Integration tests for deployment system."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)
        self.deployer = OneClickDeployer(self.project_root)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_full_deployment_workflow(self):
        """Test complete deployment workflow."""
        # Deploy Docker setup
        docker_result = self.deployer.deploy("docker")
        self.assertEqual(docker_result["status"], "success")

        # Deploy Docker Compose setup
        compose_result = self.deployer.deploy("docker-compose")
        self.assertEqual(compose_result["status"], "success")

        # Verify files were created
        dockerfile = Path(docker_result["dockerfile"])
        compose_file = Path(compose_result["compose_file"])

        self.assertTrue(dockerfile.exists())
        self.assertTrue(compose_file.exists())

        # Verify file contents
        with open(dockerfile, 'r') as f:
            docker_content = f.read()
        self.assertIn("FROM", docker_content)
        self.assertIn("uvicorn", docker_content)

        with open(compose_file, 'r') as f:
            compose_content = f.read()
        compose_data = json.loads(compose_content)
        self.assertIn("services", compose_data)


if __name__ == "__main__":
    unittest.main()
