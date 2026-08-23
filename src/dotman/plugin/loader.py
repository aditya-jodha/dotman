"""Module for loading plugins from repositories."""

# ruff: noqa: TRY003

from __future__ import annotations

import importlib
import sys
from typing import TYPE_CHECKING

from dotman.core.config.constants import SUPPORTED_API_VERSION
from dotman.errors.plugin_errors import PluginRepositoryError

from .manifest import PluginManifest

if TYPE_CHECKING:
    from importlib.metadata import EntryPoint

    from .api import DotmanPlugin
    from .environment import PluginEnvironment


class PluginLoader:
    """Loads a plugin from a managed repository."""

    def __init__(
        self,
        environment: PluginEnvironment,
    ) -> None:
        self.environment = environment

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
                path=self.environment.repository_path,
            )

        return plugin_class(), manifest.with_api_version(api_version)

    def load_manifest(self, entry_point: EntryPoint) -> PluginManifest:
        """Load primary plugin metadata from an installed distribution."""

        try:
            return PluginManifest.from_entry_point(entry_point)

        except (KeyError, ValueError) as e:
            raise PluginRepositoryError(
                f"Invalid plugin package metadata for entry point: {entry_point.name}",
                path=self.environment.repository_path,
            ) from e

    def load_entry_point(
        self,
        manifest: PluginManifest,
    ) -> type[DotmanPlugin]:
        """Load the plugin class specified by the manifest."""

        self._add_site_packages_to_path()

        try:
            module_name, attribute_name = manifest.entry_point.split(
                ":",
                maxsplit=1,
            )
        except ValueError as e:
            raise PluginRepositoryError(
                f"Invalid plugin entry point: {manifest.entry_point}",
                path=self.environment.repository_path,
            ) from e

        try:
            module = importlib.import_module(module_name)
            plugin_class = getattr(module, attribute_name)

        except (ImportError, AttributeError) as e:
            raise PluginRepositoryError(
                f"Failed to load plugin entry point: {manifest.entry_point}",
                path=self.environment.repository_path,
            ) from e

        return plugin_class

    def _add_site_packages_to_path(self) -> None:
        """Make the plugin environment importable."""
        site_packages = self.environment.site_packages

        if not site_packages.exists():
            raise PluginRepositoryError(
                f"Plugin environment site-packages not found: {site_packages}",
                path=self.environment.repository_path,
            )

        site_packages = site_packages.resolve()

        if str(site_packages) not in sys.path:
            sys.path.insert(0, str(site_packages))
