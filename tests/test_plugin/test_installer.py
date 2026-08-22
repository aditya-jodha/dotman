# ruff: noqa: S101
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, call

import pytest
from pytest import MonkeyPatch

from dotman.errors.plugin_errors import PluginInstallationError
from dotman.plugin.installer import PluginInstaller


def test_install_invokes_uv_from_repository(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> None:
    run = MagicMock()

    monkeypatch.setattr(
        "dotman.plugin.installer.shutil.which",
        lambda _name: "/usr/bin/uv",
    )
    monkeypatch.setattr(
        "dotman.plugin.installer.subprocess.run",
        run,
    )

    repository = SimpleNamespace(path=tmp_path)

    PluginInstaller().install(repository)  # type: ignore[arg-type]  # ty:ignore[invalid-argument-type]

    python = tmp_path / ".venv" / "bin" / "python"

    assert run.call_args_list == [
        call(
            ["/usr/bin/uv", "venv", str(tmp_path / ".venv")],
            cwd=tmp_path,
            check=True,
        ),
        call(
            [
                "/usr/bin/uv",
                "pip",
                "install",
                "--python",
                str(python),
                ".",
            ],
            cwd=tmp_path,
            check=True,
        ),
    ]


def test_uninstall_invokes_uv_for_distribution(monkeypatch: MonkeyPatch) -> None:
    run = MagicMock()
    monkeypatch.setattr("dotman.plugin.installer.shutil.which", lambda _name: "/usr/bin/uv")
    monkeypatch.setattr("dotman.plugin.installer.subprocess.run", run)

    PluginInstaller().uninstall("example-plugin")

    run.assert_called_once_with(["/usr/bin/uv", "pip", "uninstall", "example-plugin"], check=True)


def test_installer_reports_missing_uv(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr("dotman.plugin.installer.shutil.which", lambda _name: None)

    with pytest.raises(PluginInstallationError, match="uv executable not found"):
        PluginInstaller().uninstall("example-plugin")
