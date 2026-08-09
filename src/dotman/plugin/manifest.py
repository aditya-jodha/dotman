from __future__ import annotations

import tomllib
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from pydantic import ConfigDict, ValidationError
from pydantic.dataclasses import dataclass as pydantic_dataclass

from dotman.core.config.constants import DOTMAN, PLUGIN
from dotman.errors.config_errors import (
    ConfigFileNotFoundError,
    ConfigParseError,
    InvalidConfigFileError,
)

if TYPE_CHECKING:
    from pathlib import Path

    from dotman.plugin.repository import PluginRepository


@dataclass(frozen=True, slots=True)
class InstalledPlugin:
    repository: PluginRepository
    manifest: PluginManifest


@pydantic_dataclass(config=ConfigDict(extra="forbid"))
class PluginManifest:
    name: str
    version: str
    description: str
    authors: list[str]
    entry_point: str
    distribution_name: str | None = None
    api_version: str = "1"

    @classmethod
    def from_toml(cls, path: Path) -> PluginManifest:
        """Reads a TOML file and returns a PluginManifest instance.

        If the provided path is a directory, the function appends 'plugin.toml'
        to the path automatically.

        Args:
            path: The path to the plugin manifest file or its parent directory.

        Returns:
            A PluginManifest instance populated with the configuration data.

        Raises:
            ConfigFileNotFoundError: If the manifest file does not exist.
            ConfigParseError: If the file contains invalid TOML syntax.
            InvalidConfigFileError: If the schema or content violates validation rules.
        """
        if path.is_dir():
            path = path / "plugin.toml"

        try:
            with path.open("rb") as f:
                data = tomllib.load(f)
        except FileNotFoundError as e:
            raise ConfigFileNotFoundError(path=path) from e
        except tomllib.TOMLDecodeError as e:
            raise ConfigParseError(path, e) from e

        plugin_data: dict[str, Any] = dict(data.get(PLUGIN, {}))
        dotman_data: dict[str, Any] = dict(data.get(DOTMAN, {}))

        authors = plugin_data.get("authors")
        if isinstance(authors, str):
            plugin_data = {**plugin_data, "authors": [authors]}

        try:
            return cls(**plugin_data, **dotman_data)
        except ValidationError as e:
            raise InvalidConfigFileError(path=path, error=e) from e
