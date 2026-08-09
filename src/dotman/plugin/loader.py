"""Module for loading plugins from repositories."""

# ruff: noqa: TRY003

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

from dotman.errors.plugin_errors import PluginRepositoryError
from dotman.plugin.manifest import PluginManifest

if TYPE_CHECKING:
    from dotman.plugin.api import DotmanPlugin
    from dotman.plugin.repository import PluginRepository


class PluginLoader:
    """Loads a plugin from a managed repository."""

    def __init__(self, repository: PluginRepository) -> None:
        self.repository = repository

    def load_plugin(
        self,
        manifest: PluginManifest,
    ) -> DotmanPlugin:
        """Load and instantiate the plugin defined by the manifest."""
        plugin_class = self.load_entry_point(manifest)
        return plugin_class()

    def load_manifest(self) -> PluginManifest:
        """Load the plugin manifest from the repository."""
        manifest_path = self.repository.path / "plugin.toml"

        if not manifest_path.is_file():
            raise PluginRepositoryError(
                f"Plugin manifest not found: {manifest_path}",
                path=self.repository.path,
            )

        return PluginManifest.from_toml(manifest_path)

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
                path=self.repository.path,
            ) from e

        try:
            module = importlib.import_module(module_name)
            plugin_class = getattr(module, attribute_name)
        except (ImportError, AttributeError) as e:
            raise PluginRepositoryError(
                f"Failed to load plugin entry point: {manifest.entry_point}",
                path=self.repository.path,
            ) from e

        return plugin_class
