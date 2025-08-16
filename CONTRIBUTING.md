# Contributing to JsonAI

Thank you for your interest in contributing to JsonAI! We welcome contributions from the community to improve the project.

## How to Contribute

- **Bug Reports:** Open an issue describing the problem and steps to reproduce.
- **Feature Requests:** Open an issue with a clear description of the feature and its motivation.
- **Pull Requests:** Fork the repository, create a new branch, and submit a pull request with a clear description of your changes.

## Code Guidelines

- Follow PEP8 and project linting rules (`flake8`, `black`, `pylint`).
- Write unit and integration tests for new features or bug fixes.
- Ensure all tests pass (`pytest`) and code is type-checked (`mypy`).
- Document new features and update relevant docs.

## Communication

- For questions, open a GitHub Discussion or join the project's issue tracker.
- Be respectful and follow the project's Code of Conduct.

## Getting Started

1. Clone the repository and install dependencies:
   ```bash
   git clone https://github.com/kishoretvk/GenerativeJson.git
   cd GenerativeJson
   poetry install --with dev
   ```

2. Run tests and linters:
   ```bash
   poetry run pytest
   poetry run flake8 jsonAI
   poetry run pylint jsonAI
   poetry run mypy jsonAI
   ```

3. Make your changes and submit a pull request!
