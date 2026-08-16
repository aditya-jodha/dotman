# ruff: noqa: S101
import os
from pathlib import Path

from dotman.plugin.environment import PluginEnvironment


def test_environment_path():
    repository = Path("/plugins/example")

    environment = PluginEnvironment(repository)

    if os.name == "nt":
        assert environment.python == repository / ".venv" / "Scripts" / "python.exe"
    else:
        assert environment.python == repository / ".venv" / "bin" / "python"
