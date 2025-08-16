import os
import subprocess
import sys

import pytest

EXAMPLE_SCRIPT = os.path.join(os.path.dirname(__file__), "../examples/env_example.py")

ENVIRONMENTS = [
    ("dev", {
        "OIDC_ISSUER": "https://dev-issuer.example.com",
        "OTEL_SERVICE_NAME": "generativejson-api-dev"
    }),
    ("qa", {
        "OIDC_ISSUER": "https://qa-issuer.example.com",
        "OTEL_SERVICE_NAME": "generativejson-api-qa"
    }),
    ("perf", {
        "OIDC_ISSUER": "https://perf-issuer.example.com",
        "OTEL_SERVICE_NAME": "generativejson-api-perf"
    }),
    ("cte", {
        "OIDC_ISSUER": "https://cte-issuer.example.com",
        "OTEL_SERVICE_NAME": "generativejson-api-cte"
    }),
    ("prod", {
        "OIDC_ISSUER": "https://prod-issuer.example.com",
        "OTEL_SERVICE_NAME": "generativejson-api-prod"
    }),
]

@pytest.mark.parametrize("env_name,expected", ENVIRONMENTS)
def test_env_example(monkeypatch, env_name, expected):
    # Set minimal env vars for the test
    monkeypatch.setenv("APP_ENV", env_name)
    monkeypatch.setenv("OIDC_ISSUER", expected["OIDC_ISSUER"])
    monkeypatch.setenv("OTEL_SERVICE_NAME", expected["OTEL_SERVICE_NAME"])
    # Run the example script and capture output
    result = subprocess.run(
        [sys.executable, EXAMPLE_SCRIPT],
        capture_output=True,
        text=True,
        env=os.environ.copy()
    )
    assert expected["OIDC_ISSUER"] in result.stdout
    assert expected["OTEL_SERVICE_NAME"] in result.stdout
    assert f"APP_ENV: {env_name}" in result.stdout
