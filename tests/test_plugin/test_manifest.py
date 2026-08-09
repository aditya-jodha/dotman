# ruff: noqa: S101

from pathlib import Path

import pytest

from dotman.errors.config_errors import (
    ConfigFileNotFoundError,
    ConfigParseError,
    InvalidConfigFileError,
)
from dotman.plugin.manifest import PluginManifest


def make_toml(tmp_path: Path, content: str) -> Path:
    """Helper to create a TOML file in tmp_path."""
    file_path = tmp_path / "plugin.toml"
    file_path.write_text(content)
    return file_path


def test_valid_manifest(tmp_path: Path):
    toml_content = """
    [plugin]
    name = "example"
    version = "0.1.0"
    description = "An example plugin"
    authors = ["Aditya", "John"]
    entry_point = "my_plugin:MyPlugin"

    [dotman]
    api_version = "1"
    """
    path = make_toml(tmp_path, toml_content)
    manifest = PluginManifest.from_toml(path)
    assert manifest.name == "example"
    assert manifest.version == "0.1.0"
    assert manifest.description == "An example plugin"
    assert manifest.authors == ["Aditya", "John"]
    assert manifest.entry_point == "my_plugin:MyPlugin"
    assert manifest.api_version == "1"


def test_authors_string_normalized(tmp_path: Path):
    toml_content = """
    [plugin]
    name = "example"
    version = "0.1.0"
    description = "An example plugin"
    authors = "Aditya"
    entry_point = "my_plugin:MyPlugin"
    """
    path = make_toml(tmp_path, toml_content)
    manifest = PluginManifest.from_toml(path)
    assert manifest.authors == ["Aditya"]


def test_missing_required_field(tmp_path: Path):
    toml_content = """
    [plugin]
    version = "0.1.0"
    description = "Missing name"
    authors = ["Aditya"]
    entry_point = "my_plugin:MyPlugin"
    """
    path = make_toml(tmp_path, toml_content)
    with pytest.raises(InvalidConfigFileError):
        PluginManifest.from_toml(path)


def test_wrong_type_for_authors(tmp_path: Path):
    toml_content = """
    [plugin]
    name = "example"
    version = "0.1.0"
    description = "Wrong authors type"
    authors = 123
    entry_point = "my_plugin:MyPlugin"
    """
    path = make_toml(tmp_path, toml_content)
    with pytest.raises(InvalidConfigFileError):
        PluginManifest.from_toml(path)


def test_extra_field_forbidden(tmp_path: Path):
    toml_content = """
    [plugin]
    name = "example"
    version = "0.1.0"
    description = "Extra field"
    authors = ["Aditya"]
    entry_point = "my_plugin:MyPlugin"
    extra_field = "oops"
    """
    path = make_toml(tmp_path, toml_content)
    with pytest.raises(InvalidConfigFileError):
        PluginManifest.from_toml(path)


def test_invalid_toml(tmp_path: Path):
    path = make_toml(tmp_path, "not = valid = toml")
    with pytest.raises(ConfigParseError):
        PluginManifest.from_toml(path)


def test_missing_file(tmp_path: Path):
    path = tmp_path / "does_not_exist.toml"
    with pytest.raises(ConfigFileNotFoundError):
        PluginManifest.from_toml(path)
