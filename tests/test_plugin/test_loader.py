# ruff: noqa: S101
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import TYPE_CHECKING, cast

import pytest
from pytest import MonkeyPatch

from dotman.errors.plugin_errors import PluginRepositoryError
from dotman.plugin.loader import PluginLoader
from dotman.plugin.manifest import PluginManifest

if TYPE_CHECKING:
    from dotman.plugin.repository import PluginRepository


class ExamplePlugin:
    pass


def manifest(entry_point: str = "example_plugin:ExamplePlugin") -> PluginManifest:
    return PluginManifest(
        name="example",
        version="1.0.0",
        description="Example plugin",
        authors=["Example"],
        entry_point=entry_point,
    )


def loader(tmp_path: Path) -> PluginLoader:
    repository = cast("PluginRepository", SimpleNamespace(path=tmp_path))
    return PluginLoader(repository)


def test_load_manifest_and_plugin(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    (tmp_path / "plugin.toml").write_text(
        """
[plugin]
name = "example"
version = "1.0.0"
description = "Example plugin"
authors = ["Example"]
entry_point = "example_plugin:ExamplePlugin"
"""
    )
    module = ModuleType("example_plugin")
    module.__dict__["ExamplePlugin"] = ExamplePlugin
    monkeypatch.setattr("dotman.plugin.loader.importlib.import_module", lambda _name: module)

    loaded_manifest = loader(tmp_path).load_manifest()
    plugin = loader(tmp_path).load_plugin(loaded_manifest)

    assert loaded_manifest.name == "example"
    assert isinstance(plugin, ExamplePlugin)


@pytest.mark.parametrize("entry_point", ["missing-separator", "module:MissingClass"])
def test_load_entry_point_rejects_invalid_targets(
    monkeypatch: MonkeyPatch, tmp_path: Path, entry_point: str
) -> None:
    if ":" in entry_point:
        monkeypatch.setattr(
            "dotman.plugin.loader.importlib.import_module", lambda _name: ModuleType("module")
        )

    with pytest.raises(PluginRepositoryError):
        loader(tmp_path).load_entry_point(manifest(entry_point))


def test_load_manifest_rejects_missing_file(tmp_path: Path) -> None:
    with pytest.raises(PluginRepositoryError, match="Plugin manifest not found"):
        loader(tmp_path).load_manifest()
