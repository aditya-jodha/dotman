# ruff: noqa: S101

from importlib.metadata import EntryPoint
from types import SimpleNamespace
from typing import cast

from dotman.plugin.manifest import PluginManifest


def entry_point(**metadata: str) -> EntryPoint:
    values = {
        "Name": "example-distribution",
        "Version": "0.1.0",
        "Summary": "An example plugin",
        "Author": "Aditya",
    }
    values.update(metadata)
    return cast(
        "EntryPoint",
        SimpleNamespace(
            name="example",
            value="example_plugin:ExamplePlugin",
            dist=SimpleNamespace(metadata=values),
        ),
    )


def test_manifest_comes_from_distribution_metadata() -> None:
    manifest = PluginManifest.from_entry_point(entry_point())

    assert manifest.name == "example"
    assert manifest.distribution_name == "example-distribution"
    assert manifest.version == "0.1.0"
    assert manifest.description == "An example plugin"
    assert manifest.authors == ["Aditya"]
    assert manifest.entry_point == "example_plugin:ExamplePlugin"


def test_manifest_records_api_version_after_plugin_validation() -> None:
    manifest = PluginManifest.from_entry_point(entry_point()).with_api_version("1")

    assert manifest.api_version == "1"
