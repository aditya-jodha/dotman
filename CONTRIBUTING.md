# Contributing to Dotman

Thanks for contributing. Bug fixes, tests, documentation, platform support, and plugin work are all useful contributions.

## Development setup

Dotman can move files and create symlinks in the configured home directory. Use a disposable test directory or container when exercising commands manually.

```bash
git clone https://github.com/aditya-jodha/dotman.git
cd dotman
uv sync
uv run dotman --help
```

For isolated manual testing, point configuration at a temporary file:

```bash
export DOTMAN_CONFIG="$(mktemp -d)/config.yml"
uv run dotman config show
```

## Checks

Run these before opening a pull request:

```bash
uv run pytest
uv run ruff check src tests
uv run ruff format --check src tests
```

Add a focused regression test for every behavioral bug fix. Changes to the CLI, configuration schema, or plugin manifest must include matching user documentation.

## Project map

```text
src/dotman/
├── __cli__.py        # startup, plugin loading, Typer root app
├── api.py            # public Dotman facade
├── cli/              # commands, error handlers, renderers
├── core/             # dotfile model, linking, profiles, diagnostics
├── errors/           # typed, serializable domain errors
└── plugin/           # plugin repositories, manifests, install lifecycle
tests/
├── test_cli/
├── test_core/
├── test_plugin/
└── test_service/
```

Read [ARCHITECTURE.md](ARCHITECTURE.md) before making cross-layer changes.

## Plugin contributions

Plugins are Git repositories with an installable Python project. Define a `dotman.plugins` entry point in `pyproject.toml`; its entry-point name is the plugin name and its `module:Class` value identifies the plugin class. Package metadata provides the version, description, authors, and distribution name. Plugin classes must declare `api_version = "1"`.

Plugin classes implement `register(api)`. Use `api.add_typer(...)` to expose commands. Do not depend on Dotman's private command wiring; the plugin API is the supported integration boundary.

Test installation failure cleanup, manifest parsing, command registration, and uninstallation behavior when changing the plugin lifecycle.

## Pull requests

Keep each pull request focused. In its description, explain the user-visible behavior, tests run, and any configuration or migration impact. Do not mix unrelated formatting changes with functional changes.
