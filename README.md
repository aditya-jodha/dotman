# Dotman

Dotman is a Python CLI for storing dotfiles by profile and package, then linking them back into a home directory. It also provides profile switching, diagnostics, structured error output, and installable command plugins.

https://github.com/user-attachments/assets/e07f0579-8d2d-42e5-bc16-0a537472da9c


<div align="center">

[![CI](https://github.com/aditya-jodha/dotman/actions/workflows/ci.yml/badge.svg)](https://github.com/aditya-jodha/dotman/actions/workflows/ci.yml)
[![Coverage](https://codecov.io/gh/aditya-jodha/dotman/branch/main/graph/badge.svg)](https://codecov.io/gh/aditya-jodha/dotman)
[![LICENSE](https://img.shields.io/badge/license-MIT-green)](./LICENSE)
![Python Version](https://img.shields.io/badge/python-3.12%2B-blue)

<!-- uv badge is shown here becaue this tool uses uv as its installation method -->

![CLI](https://img.shields.io/badge/CLI-yellow?logo=bilibili&logoColor=white)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)

[![Discord](https://img.shields.io/badge/Discord-blue?logo=Discord&logoColor=white)](https://discord.gg/aditya_jodha)
[![Static Badge](https://img.shields.io/badge/Reddit-red?style=plastic&logo=reddit&logoColor=white)](https://www.reddit.com/user/Dry_Developer)
[![Static Badge](https://img.shields.io/badge/GitHub-black?logo=github&logoColor=white)](https://github.com/aditya-jodha)

</div>

## ✨ Features

- **Plugin System**: Extend Dotman with custom commands and functionality.
- **Multiple Profiles**: Manage separate configurations seamlessly.
- **Automatic Symlink Management**: Handles path linking without manual intervention.
- **Safe Rollback**: Revert changes safely if things go wrong.
- **Package Organization**: Keep everything structured and neat.
- **Doctor Diagnostics**: Instantly troubleshoot environmental errors.
- **Rich CLI Output**: Beautiful, readable terminal interfaces.
- **JSON Output for Automation**: Parse and pipe data into other scripts effortlessly.
- **Strongly Typed Configuration**: Validated out-of-the-box via Pydantic models.

---

🧪 **230+ Tests Passing**

---

## Installation

Dotman requires Python 3.12.13 or later and uses [uv](https://docs.astral.sh/uv/).

```bash
uv tool install git+https://github.com/aditya-jodha/dotman.git
dotman --help
```

To work from a checkout instead:

```bash
git clone https://github.com/aditya-jodha/dotman.git
cd dotman
uv sync
uv run dotman --help
```

## Quick start

Initialize Dotman and choose the first profile when prompted:

```bash
dotman init
```

Add a file from the configured home directory to a package. Dotman previews the operation and asks whether to commit it.

```bash
dotman add ~/.zshrc --package shell
dotman sync
```

The managed copy is stored under:

```text
~/.dotfiles/
├── metadata.yml
└── profiles/
    └── <profile>/
        └── <package>/
            └── <path-relative-to-home>
```

For example, adding `~/.config/nvim/init.lua` to the `editor` package creates `~/.dotfiles/profiles/<profile>/editor/.config/nvim/init.lua`. `dotman sync` then links that file to `~/.config/nvim/init.lua`.

## Commands

| Command | Description |
| --- | --- |
| `dotman init` | Create the dotfiles directory and initial profile. An existing directory is renamed to `<dotfiles_dir>.backup`. |
| `dotman add FILE --package NAME` | Move a file or directory from the configured home directory into the active profile; confirm to commit or roll back. |
| `dotman remove FILE` | Remove a managed file from the active profile and clean up empty package directories. |
| `dotman sync [--package NAME] [--dry-run]` | Create, repair, or preview symlinks for the active profile. Existing conflicting targets are backed up under `~/.dotman_backup`. |
| `dotman doctor [-a|--all]` | Report dotfiles-directory, package, permission, and symlink health. `--all` includes healthy links. |
| `dotman profile create NAME` | Create an empty profile. |
| `dotman profile use [NAME]` | Switch profiles, unlinking the old profile and linking the new one. Without a name, it lists profiles. |
| `dotman profile delete NAME` | Delete an empty profile. |
| `dotman profile ls` | List profiles. |
| `dotman config show` | Print the effective configuration. |
| `dotman config get KEY` | Print one configuration value. |
| `dotman config set KEY VALUE` | Validate and persist one configuration value. |
| `dotman plugin install SOURCE` | Clone a Git plugin repository, validate its manifest, and install its Python package. |
| `dotman plugin uninstall NAME` | Uninstall a plugin by the `name` in its manifest and remove its managed repository. |

Use `--output rich`, `--output plain`, or `--output json` for supported structured-error renderers.

## Configuration

The default configuration file is `~/.config/dotman/config.yml`. Set `DOTMAN_CONFIG` to use another location. Its supported keys are:

```yaml
dotfiles_dir: ~/.dotfiles
home_dir: ~
plugins_dir: ~/.config/dotman/plugins
```

Paths are expanded when Dotman loads the configuration. Existing configuration files that do not contain `plugins_dir` continue to use the default location.

## Plugins

A plugin is a Git/Local repository containing an installable Python project alongside a plugin.toml manifest. On startup, Dotman automatically loads all installed plugins, allowing them to register custom typer sub-applications via the PluginAPI.

- Every plugin must include a plugin.toml file at its root to define its metadata and entry points.
```toml title="plugin.toml"
[plugin]
name = "example-plugin"
version = "0.1.0"
description = "Adds example commands to Dotman"
authors = ["Your Name"]
entry_point = "fake_repo.plugin:ExamplePlugin"
distribution_name = "example-plugin"

[dotman]
api_version = "1"
```

- The plugin must contain a `plugin.toml` file at its root to define its metadata and entry points. The plugin must contain a `pyproject.toml` file at its root to define its dependencies.
```
fake_repo on  main [!] is 📦 v0.1.0 via 🐍 v3.12.13 
❯ tree                                                                      
 .
├── plugin.toml
├── pyproject.toml
├── README.md
├── src
│   └── fake_repo
│       ├── __init__.py
│       └── plugin.py
└── uv.lock
```

- The specified entry_point must point to a Python class exposing a register(api: PluginAPI) method. Use api.add_typer() to attach your custom CLI commands to the main application.

```python
import typer

from dotman.plugin import PluginAPI

app = typer.Typer(help="Example plugin commands.")


@app.command()
def hello(name: str = "world") -> None:
    print(f"Hello, {name}!")


class ExamplePlugin:
    def register(self, api: PluginAPI) -> None:
        api.add_typer(app, name="example")
```

Plugins can be managed directly through the core Dotman CLI using Git repository URLs:

```bash
dotman plugin install https://github.com/example/dotman-example-plugin.git
dotman plugin uninstall example-plugin
```

> [!CAUTION]
> If installation fails after cloning, Dotman removes the newly cloned repository. During uninstallation it first removes the Python distribution, then deletes only the matching repository directly inside `plugins_dir`.

## Development

```bash
uv run pytest
uv run ruff check src tests
uv run ruff format --check src tests
```

## Roadmap

### Completed

- [x] Dotfile management
- [x] Sync command
- [x] Doctor command
- [x] Profile management
- [x] Profile switching
- [x] Automated testing
- [x] Package removal command
- [x] Configuration file support
- [x] Plugin system

### Planned

- [ ] Plugin discovery and search (~ PLUGIN MARKETPLACE)
- [ ] Package management
- [ ] Profile export/import
- [ ] Dry-run mode improvements
- [ ] Windows support

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidance and [ARCHITECTURE.md](ARCHITECTURE.md) for module boundaries and runtime flow.

<div>
    <div align="Right">
    𝕯𝖔𝖙𝖒𝖆𝖓
    </div>
    <div align="center">
    <img src="https://img.shields.io/badge/_MADE_BY_-ADITYA-blue.svg" alt="Made by Aditya">
    </div>
</div>