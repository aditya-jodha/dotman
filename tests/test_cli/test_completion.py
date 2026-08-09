# ruff: noqa: S101
from pathlib import Path
from types import SimpleNamespace

from pytest import MonkeyPatch

import dotman.cli.completion as completion
from dotman.core.config.config import DotmanConfig


def test_complete_plugins_uses_manifest_names(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()
    config = DotmanConfig(home_dir=tmp_path, dotfiles_dir=tmp_path, plugins_dir=plugins_dir)
    monkeypatch.setattr(completion.DotmanConfig, "load", lambda: config)

    class FakePluginManager:
        def __init__(self, _plugins_dir: Path) -> None:
            pass

        def list_plugins(self):
            return [
                SimpleNamespace(manifest=SimpleNamespace(name="example-plugin")),
                SimpleNamespace(manifest=SimpleNamespace(name="other-plugin")),
            ]

    monkeypatch.setattr(completion, "PluginManager", FakePluginManager)

    assert completion.complete_plugins("ex") == ["example-plugin"]


def test_complete_plugins_returns_empty_without_plugin_directory(
    monkeypatch: MonkeyPatch, tmp_path: Path
) -> None:
    config = DotmanConfig(
        home_dir=tmp_path,
        dotfiles_dir=tmp_path,
        plugins_dir=tmp_path / "missing-plugins",
    )
    monkeypatch.setattr(completion.DotmanConfig, "load", lambda: config)

    assert completion.complete_plugins("") == []
