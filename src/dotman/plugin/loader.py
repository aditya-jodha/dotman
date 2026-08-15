"""Module for loading plugins from repositories."""

# ruff: noqa: TRY003

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

from dotman.core.config.constants import SUPPORTED_API_VERSION
from dotman.errors.plugin_errors import PluginRepositoryError
from dotman.plugin.manifest import PluginManifest

if TYPE_CHECKING:
    from importlib.metadata import EntryPoint

    from dotman.plugin.api import DotmanPlugin
    from dotman.plugin.repository import PluginRepository


class PluginLoader:
    """Loads a plugin from a managed repository."""

    def __init__(self, repository: PluginRepository | None = None) -> None:
        self.repository = repository

    def load_plugin(
        self,
        manifest: PluginManifest,
    ) -> tuple[DotmanPlugin, PluginManifest]:
        """Load and instantiate the plugin defined by the manifest."""
        plugin_class = self.load_entry_point(manifest)
        api_version = getattr(plugin_class, "api_version", None)
        if api_version != SUPPORTED_API_VERSION:
            raise PluginRepositoryError(
                f"Plugin {manifest.name!r} requires unsupported API version: {api_version!r}",
                path=self.repository.path if self.repository else None,
            )
        return plugin_class(), manifest.with_api_version(api_version)

    def load_manifest(self, entry_point: EntryPoint) -> PluginManifest:
        """Load primary plugin metadata from an installed distribution."""
        try:
            return PluginManifest.from_entry_point(entry_point)
        except (KeyError, ValueError) as e:
            raise PluginRepositoryError(
                f"Invalid plugin package metadata for entry point: {entry_point.name}",
                path=self.repository.path if self.repository else None,
            ) from e

    def load_entry_point(self, manifest: PluginManifest) -> type[DotmanPlugin]:
        """Load the plugin class specified by the manifest."""
        try:
            module_name, attribute_name = manifest.entry_point.split(
                ":",
                maxsplit=1,
            )
        except ValueError as e:
            raise PluginRepositoryError(
                f"Invalid plugin entry point: {manifest.entry_point}",
                path=self.repository.path if self.repository else None,
            ) from e

        try:
            module = importlib.import_module(module_name)
            plugin_class = getattr(module, attribute_name)
        except (ImportError, AttributeError) as e:
            raise PluginRepositoryError(
                f"Failed to load plugin entry point: {manifest.entry_point}",
                path=self.repository.path if self.repository else None,
            ) from e

        return plugin_class
