"""
One-Click Deployment System for JsonAI.

This module provides easy deployment options for JsonAI including
Docker, cloud platforms, and local development setups.
"""

import os
import subprocess
import json
from typing import Dict, Any, List, Optional
from pathlib import Path
import shutil

from jsonAI.main import Jsonformer
from jsonAI.model_backends import ModelBackend


class DockerDeployer:
    """Docker deployment for JsonAI."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.docker_dir = project_root / "docker"

    def create_dockerfile(self, base_image: str = "python:3.9-slim",
                          expose_port: int = 8000) -> str:
        """Create a Dockerfile for JsonAI."""

        dockerfile_content = f'''FROM {base_image}

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    build-essential \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY pyproject.toml poetry.lock ./
RUN pip install poetry \\
    && poetry config virtualenvs.create false \\
    && poetry install --no-dev --no-interaction

# Copy source code
COPY jsonAI/ ./jsonAI/
COPY examples/ ./examples/

# Create non-root user
RUN useradd --create-home --shell /bin/bash jsonai
USER jsonai

EXPOSE {expose_port}

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:{expose_port}/health || exit 1

CMD ["uvicorn", "jsonAI.api:app", "--host", "0.0.0.0", "--port", "{expose_port}"]
'''

        dockerfile_path = self.docker_dir / "Dockerfile"
        dockerfile_path.parent.mkdir(parents=True, exist_ok=True)

        with open(dockerfile_path, 'w') as f:
            f.write(dockerfile_content)

        return str(dockerfile_path)

    def create_docker_compose(self, services: List[str] = None) -> str:
        """Create docker-compose.yml for multi-service deployment."""

        services = services or ["api", "frontend", "monitoring"]

        compose_config = {
            "version": "3.8",
            "services": {}
        }

        # API Service
        if "api" in services:
            compose_config["services"]["api"] = {
                "build": {
                    "context": ".",
                    "dockerfile": "./docker/Dockerfile"
                },
                "ports": ["8000:8000"],
                "environment": [
                    "ENVIRONMENT=production",
                    "OLLAMA_HOST=http://ollama:11434"
                ],
                "depends_on": ["ollama"] if "ollama" in services else [],
                "volumes": [
                    "./config:/app/config:ro"
                ]
            }

        # Ollama Service
        if "ollama" in services:
            compose_config["services"]["ollama"] = {
                "image": "ollama/ollama:latest",
                "ports": ["11434:11434"],
                "volumes": [
                    "ollama_data:/root/.ollama"
                ]
            }

        # Frontend Service
        if "frontend" in services:
            compose_config["services"]["frontend"] = {
                "build": {
                    "context": "./frontend",
                    "dockerfile": "./Dockerfile"
                },
                "ports": ["3000:3000"],
                "depends_on": ["api"],
                "environment": [
                    "REACT_APP_API_URL=http://localhost:8000"
                ]
            }

        # Monitoring Service
        if "monitoring" in services:
            compose_config["services"]["monitoring"] = {
                "image": "prom/prometheus:latest",
                "ports": ["9090:9090"],
                "volumes": [
                    "./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro"
                ]
            }

        # Volumes
        if "ollama" in services:
            compose_config["volumes"] = {
                "ollama_data": {}
            }

        compose_path = self.project_root / "docker-compose.yml"
        with open(compose_path, 'w') as f:
            json.dump(compose_config, f, indent=2)

        return str(compose_path)

    def deploy_locally(self):
        """Deploy JsonAI locally using Docker."""
        print("🚀 Deploying JsonAI locally with Docker...")

        # Build and run
        commands = [
            "docker build -t jsonai:latest -f docker/Dockerfile .",
            "docker run -d -p 8000:8000 --name jsonai jsonai:latest"
        ]

        for cmd in commands:
            result = subprocess.run(cmd, shell=True, cwd=self.project_root)
            if result.returncode != 0:
                raise Exception(f"Command failed: {cmd}")

        print("✅ JsonAI deployed successfully!")
        print("🌐 API available at: http://localhost:8000")
        print("📚 Docs available at: http://localhost:8000/docs")


class CloudDeployer:
    """Cloud deployment for JsonAI."""

    def __init__(self, project_root: Path):
        self.project_root = project_root

    def create_railway_config(self) -> str:
        """Create Railway deployment configuration."""

        config = {
            "build": {
                "builder": "NIXPACKS"
            },
            "deploy": {
                "startCommand": "uvicorn jsonAI.api:app --host 0.0.0.0 --port $PORT"
            },
            "environments": {
                "production": {
                    "OLLAMA_HOST": "http://ollama:11434",
                    "ENVIRONMENT": "production"
                }
            }
        }

        config_path = self.project_root / "railway.json"
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)

        return str(config_path)

    def create_render_config(self) -> str:
        """Create Render deployment configuration."""

        config = {
            "services": [
                {
                    "type": "web",
                    "name": "jsonai-api",
                    "runtime": "python3",
                    "buildCommand": "pip install -r requirements.txt",
                    "startCommand": "uvicorn jsonAI.api:app --host 0.0.0.0 --port 10000"
                }
            ]
        }

        config_path = self.project_root / "render.yaml"
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)

        return str(config_path)

    def create_fly_config(self) -> str:
        """Create Fly.io deployment configuration."""

        config = '''app = "jsonai"
primary_region = "iad"

[build]
  builder = "paketobuildpacks/builder:base"
  buildpacks = ["gcr.io/paketo-buildpacks/python"]

[env]
  PORT = "8080"

[processes]
  web = "uvicorn jsonAI.api:app --host 0.0.0.0 --port 8080"

[[services]]
  internal_port = 8080
  protocol = "tcp"

  [[services.ports]]
    handlers = ["http"]
    port = "80"

  [[services.ports]]
    handlers = ["tls", "http"]
    port = "443"
'''

        config_path = self.project_root / "fly.toml"
        with open(config_path, 'w') as f:
            f.write(config)

        return str(config_path)


class LocalDevDeployer:
    """Local development deployment."""

    def __init__(self, project_root: Path):
        self.project_root = project_root

    def setup_dev_environment(self):
        """Setup local development environment."""

        print("🔧 Setting up JsonAI development environment...")

        # Create virtual environment
        venv_path = self.project_root / ".venv"
        if not venv_path.exists():
            subprocess.run(["python", "-m", "venv", ".venv"], cwd=self.project_root)

        # Install dependencies
        pip_path = venv_path / "bin" / "pip" if os.name != 'nt' else venv_path / "Scripts" / "pip"
        requirements_path = self.project_root / "requirements.txt"

        if requirements_path.exists():
            subprocess.run([str(pip_path), "install", "-r", "requirements.txt"],
                          cwd=self.project_root)

        # Create .env file
        env_file = self.project_root / ".env"
        if not env_file.exists():
            env_content = '''# JsonAI Environment Configuration
ENVIRONMENT=development
DEBUG=true
OLLAMA_HOST=http://localhost:11434
PORT=8000
'''
            with open(env_file, 'w') as f:
                f.write(env_content)

        print("✅ Development environment setup complete!")
        print("🚀 Run: source .venv/bin/activate && uvicorn jsonAI.api:app --reload")

    def start_dev_server(self):
        """Start development server."""
        print("🚀 Starting JsonAI development server...")

        cmd = ["uvicorn", "jsonAI.api:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]
        subprocess.run(cmd, cwd=self.project_root)


class OneClickDeployer:
    """One-click deployment system combining all deployment options."""

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
        self.docker = DockerDeployer(self.project_root)
        self.cloud = CloudDeployer(self.project_root)
        self.local = LocalDevDeployer(self.project_root)

    def deploy(self, target: str, **kwargs):
        """One-click deployment to specified target."""

        print(f"🚀 Deploying JsonAI to {target}...")

        if target == "docker":
            return self._deploy_docker(**kwargs)
        elif target == "docker-compose":
            return self._deploy_docker_compose(**kwargs)
        elif target == "railway":
            return self._deploy_railway(**kwargs)
        elif target == "render":
            return self._deploy_render(**kwargs)
        elif target == "fly":
            return self._deploy_fly(**kwargs)
        elif target == "local":
            return self._deploy_local(**kwargs)
        else:
            raise ValueError(f"Unknown deployment target: {target}")

    def _deploy_docker(self, **kwargs):
        """Deploy using Docker."""
        dockerfile = self.docker.create_dockerfile(**kwargs)
        self.docker.deploy_locally()
        return {"status": "success", "dockerfile": dockerfile}

    def _deploy_docker_compose(self, **kwargs):
        """Deploy using Docker Compose."""
        compose_file = self.docker.create_docker_compose(**kwargs)
        return {"status": "success", "compose_file": compose_file}

    def _deploy_railway(self, **kwargs):
        """Deploy to Railway."""
        config_file = self.cloud.create_railway_config()
        return {"status": "success", "config_file": config_file}

    def _deploy_render(self, **kwargs):
        """Deploy to Render."""
        config_file = self.cloud.create_render_config()
        return {"status": "success", "config_file": config_file}

    def _deploy_fly(self, **kwargs):
        """Deploy to Fly.io."""
        config_file = self.cloud.create_fly_config()
        return {"status": "success", "config_file": config_file}

    def _deploy_local(self, **kwargs):
        """Deploy locally for development."""
        self.local.setup_dev_environment()
        return {"status": "success", "message": "Local development environment ready"}

    def list_deployment_options(self) -> List[str]:
        """List all available deployment options."""
        return ["docker", "docker-compose", "railway", "render", "fly", "local"]
