# ruff: noqa: S101,B010
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import TYPE_CHECKING, cast

import pytest
from pytest import MonkeyPatch

from dotman.errors.plugin_errors import PluginRepositoryError
from dotman.plugin.environment import PluginEnvironment
from dotman.plugin.loader import PluginLoader
from dotman.plugin.manifest import PluginManifest

if TYPE_CHECKING:
    from importlib.metadata import EntryPoint


class ExamplePlugin:
    api_version = "1"


class IncompatiblePlugin:
    api_version = "2"


def manifest(entry_point: str = "example_plugin:ExamplePlugin") -> PluginManifest:
    return PluginManifest(
        name="example",
        version="1.0.0",
        description="Example plugin",
        authors=["Example"],
        entry_point=entry_point,
    )


def test_load_plugin_enforces_api_version(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    module = ModuleType("example_plugin")
    setattr(module, "ExamplePlugin", ExamplePlugin)
    monkeypatch.setattr("dotman.plugin.loader.importlib.import_module", lambda _name: module)

    environment = PluginEnvironment(tmp_path / "plugins")

    loader = PluginLoader(environment)

    plugin, loaded_manifest = loader.load_plugin(manifest())

    assert isinstance(plugin, ExamplePlugin)
    assert loaded_manifest.api_version == "1"


def test_load_plugin_rejects_incompatible_api_version(monkeypatch: MonkeyPatch) -> None:
    module = ModuleType("example_plugin")
    setattr(module, "ExamplePlugin", IncompatiblePlugin)
    monkeypatch.setattr("dotman.plugin.loader.importlib.import_module", lambda _name: module)

    with pytest.raises(PluginRepositoryError, match="unsupported API version"):
        PluginLoader().load_plugin(manifest())


@pytest.mark.parametrize("entry_point", ["missing-separator", "module:MissingClass"])
def test_load_entry_point_rejects_invalid_targets(
    monkeypatch: MonkeyPatch, entry_point: str
) -> None:
    if ":" in entry_point:
        monkeypatch.setattr(
            "dotman.plugin.loader.importlib.import_module", lambda _name: ModuleType("module")
        )

    with pytest.raises(PluginRepositoryError):
        PluginLoader().load_entry_point(manifest(entry_point))


def test_load_manifest_rejects_missing_distribution_metadata() -> None:
    entry_point = SimpleNamespace(name="example", value="example:Plugin", dist=None)

    with pytest.raises(PluginRepositoryError, match="Invalid plugin package metadata"):
        PluginLoader().load_manifest(cast("EntryPoint", entry_point))
