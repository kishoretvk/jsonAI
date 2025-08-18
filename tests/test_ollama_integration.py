import pytest
import os

skip_ollama = pytest.mark.skipif(
    os.environ.get("CI") == "true" or os.environ.get("GITHUB_ACTIONS") == "true",
    reason="Ollama tests are skipped in CI environments."
)

@skip_ollama
def test_ollama_placeholder():
    # This test is skipped in CI. Replace with real Ollama integration tests for local runs.
    assert True
