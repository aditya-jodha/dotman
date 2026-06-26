# Contributing to Dotman

Thank you for your interest in contributing to Dotman!

Whether you're fixing a bug, improving documentation, or adding a feature, your help is appreciated.

---

## First Contribution Ideas

Good first issues:

- Documentation improvements
- Additional tests
- Error message improvements
- Platform compatibility fixes
- Edge-case handling

## Development Environment

Dotman manages real user files and symlinks.

> [!WARNING]
> To avoid accidental modification of your host system, development inside Docker is strongly recommended because dotman
> manages real files and symlinks..

### Install Docker

If you don't have Docker installed, you can install it from:

- [![Static Badge](https://img.shields.io/badge/MacOS-Docker-blue?logo=Docker)](https://docs.docker.com/desktop/setup/install/mac-install)
- [![Static Badge](https://img.shields.io/badge/Linux-Docker-blue?logo=Docker)](https://docs.docker.com/desktop/setup/install/linux/)

### Create a Docker Image

Save the following configuration as `Dockerfile` in your root directory:

### Start the container

```bash
docker pull ghcr.io/aditya-jodha/dotman/dotman-dev:latest

docker run --rm -it \
    -v "${PWD}":/home/tester/dotman \
    -w /home/tester/dotman \
    dotman-dev
```

---

## Development Setup

### 1. Fork and Clone

```bash
git clone https://github.com/aditya-jodha/dotman.git
cd dotman
```

### 2. Create a Virtual Environment

This project uses `uv` for dependency management.

```bash
uv sync
source .venv/bin/activate
```

### 3. Verify Installation

```bash
dotman --help
```

or

```bash
python -m dotman --help
```

---

## Running Tests

Run all tests:

```bash
pytest
```

Run with coverage:

```bash
pytest --cov
```

---

## Linting & Formatting

Run Ruff code quality checks:

```bash
ruff check .
```

Format code automatically:

```bash
ruff format .
```

---

## Project Structure

```text
.
├── CONTRIBUTING.md
├── LICENSE
├── pyproject.toml
├── README.md
├── src
│   └── dotman
│       ├── __cli__.py
│       ├── __init__.py
│       ├── cli
│       │   ├── __init__.py
│       │   ├── app
│       │   │   ├── __init__.py
│       │   │   ├── add.py
│       │   │   ├── doctor.py
│       │   │   ├── init.py
│       │   │   ├── root.py
│       │   │   └── sync.py
│       │   ├── common_func.py
│       │   ├── config
│       │   │   ├── __init__.py
│       │   │   └── main.py
│       │   ├── profile
│       │   │   └── root.py
│       │   └── tree_builder.py
│       ├── core
│       │   ├── __init__.py
│       │   ├── add.py
│       │   ├── config.py
│       │   ├── doctor.py
│       │   ├── get_internal_data.py
│       │   ├── initializer.py
│       │   ├── linker.py
│       │   ├── profile.py
│       │   ├── service
│       │   │   ├── __init__.py
│       │   │   ├── add_service.py
│       │   │   ├── doctor_service.py
│       │   │   ├── initializer_service.py
│       │   │   ├── profile_service.py
│       │   │   └── sync_service.py
│       │   └── utils
│       │       └── fs.py
│       └── errors
│           ├── __init__.py
│           ├── custom_errors.py
│           ├── dotman_error.py
│           ├── initializer_errors.py
│           └── profile_errors.py
├── tests
│   ├── test_cli
│   │   └── test_entry_point.py
│   └── test_core
│       ├── test_add.py
│       ├── test_doctor.py
│       ├── test_dotman_confif.py
│       ├── test_get_internal_data.py
│       ├── test_initializer.py
│       ├── test_linker.py
│       ├── test_logbook.py
│       ├── test_profile.py
│       ├── test_unlinker.py
│       └── test_utils
│           └── test_fs.py
└── uv.lock
```

> For a deeper architectural overview including Mermaid diagrams, check out
> the [![Static Badge](https://shields.io/badge/Dotman-Architecture-blue?style=plastic&logo=gumtree)](https://github.com/aditya-jodha/dotman/blob/main/README.md/#Architecture)
> section.

---

## Pull Request Guidelines

Before opening a PR:

- Ensure tests pass.
- Ensure Ruff diagnostics pass without errors.
- Add tests for new functionality.
- Update documentation when making user-facing changes.
- Keep pull requests focused on a single logical change.

---

## Issue Templates

* **Reporting Bugs:** Please read and use
  the [![Static Badge](https://shields.io/badge/Dotman-Report_Bug-blue?style=plastic&logo=gumtree)](https://github.com/aditya-jodha/dotman/blob/main/.github/ISSUE_TEMPLATE/bug_report.md)
  template.
* **Feature Requests:** Suggestions are welcome! Please look over
  the [![Static Badge](https://shields.io/badge/Dotman-Feature_Request-blue?style=plastic&logo=gumtree)](https://github.com/aditya-jodha/dotman/blob/main/.github/ISSUE_TEMPLATE/feature_request.md)
  template.

---

## Code Style

- Enforce Python type hints everywhere.
- Prefer small, single-responsibility functions.
- Write tests for all bug fixes to prevent regressions.
- Avoid adding unnecessary third-party dependencies.

---

## Philosophy

Dotman aims to be:

- **Simple**
- **Predictable**
- **Safe**
- **Easy to recover from mistakes**

Features should always prioritize execution reliability over complexity.

---

Thank you for contributing!
