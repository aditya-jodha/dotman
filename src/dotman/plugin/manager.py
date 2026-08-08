# ruff: noqa: TRY003
"""
Module for managing the installation, update, and lifecycle of plugins.

This module provides tools to download plugins from remote Git repositories
or load them from local system directories, handle manifests, and track
available plugin states.
"""

import shutil
from pathlib import Path
from urllib.parse import urlparse

import typer

from dotman.errors.plugin_errors import (
    InvalidPluginSourceError,
    PluginNotFoundError,
    PluginRepositoryError,
)
from dotman.plugin.api import PluginAPI

from .installer import PluginInstaller
from .loader import PluginLoader
from .manifest import InstalledPlugin, PluginManifest
from .repository import PluginRepository


class PluginManager:
    """Handles core lifecycles for plugins including discovery, installation, and updates.

    Attributes:
        plugins_dir: A Path object referencing the central workspace directory
            where plugin code repos are installed and stored.
    """

    def __init__(
        self,
        plugins_dir: Path,
        installer: PluginInstaller | None = None,
    ) -> None:
        self.installer = installer or PluginInstaller()

        self.plugins_dir = plugins_dir.resolve()
        self.plugins_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def is_git_source(source: str) -> bool:
        """Determines if a given source string represents a Git repository or local source directory

        This method validates the source by checking if it exists as a local
        directory or matches common remote Git repository URL formats (HTTP,
        HTTPS, GIT, SSH, or SCP-like syntax).

        Args:
            source: A string representing the file path or remote URL to evaluate.

        Returns:
            True if the source is an existing local directory or a valid remote
            Git URL; False otherwise.

        Examples:
            >>> PluginManager.is_git_source("/path/to/local/repo")
            True
            >>> PluginManager.is_git_source("https://github.com")
            True
            >>> PluginManager.is_git_source("git@github.com:user/repo.git")
            True
            >>> PluginManager.is_git_source("invalid_source_path")
            False
        """
        path = Path(source)

        if path.exists():
            return path.is_dir() and (path / ".git").exists()

        parsed = urlparse(source)

        return parsed.scheme in {"http", "https", "git", "ssh"} or source.startswith("git@")

    @staticmethod
    def _repository_name(source: str) -> str:
        """Extracts the base folder name or project slug from a Git URL or path string.

        Args:
            source: The source path or remote location URL of the repository.

        Returns:
            The plain folder name or stem string (e.g., 'plugin-core' from
            'https://github.com').
        """
        if source.startswith("git@"):
            path = source.rsplit(":", 1)[-1]
        else:
            path = urlparse(source).path or source

        return Path(path.rstrip("/")).stem

    def install(self, source: str) -> PluginManifest:
        """Install a plugin from a Git repository URL."""
        if not self.is_git_source(source):
            raise InvalidPluginSourceError(source)

        repository_name = self._repository_name(source)

        target_dir = self.plugins_dir / repository_name
        repository = PluginRepository.clone(url=source, target_dir=target_dir)

        try:
            loader = PluginLoader(repository)
            manifest = loader.load_manifest()
            self.installer.install(repository)
        except Exception:
            shutil.rmtree(target_dir, ignore_errors=True)
            raise

        return manifest

    def uninstall(self, name: str) -> None:
        """Uninstall a plugin."""
        installed_plugin = self._get_installed_plugin(name)
        repository = installed_plugin.repository

        if repository.path.parent != self.plugins_dir:
            raise PluginRepositoryError(
                f"Refusing to remove unmanaged plugin repository: {repository.path}",
                path=repository.path,
            )

        distribution_name = (
            installed_plugin.manifest.distribution_name or installed_plugin.manifest.name
        )
        self.installer.uninstall(distribution_name)

        try:
            shutil.rmtree(repository.path)
        except OSError as e:
            raise PluginRepositoryError(
                f"Failed to remove plugin repository: {repository.path}",
                path=repository.path,
            ) from e

    def update(self, name: str):
        """Update an installed plugin."""
        ...
        # repository = self._get_repository(name)
        # repository.fetch()

    def list_plugins(self) -> list[InstalledPlugin]:
        plugins: list[InstalledPlugin] = []

        for plugins_dir in self.plugins_dir.iterdir():
            if not plugins_dir.is_dir():
                continue

            try:
                repository = PluginRepository(plugins_dir)
                loader = PluginLoader(repository)
                manifest = loader.load_manifest()
            except PluginRepositoryError:
                # TODO: Log invalid plugin repository.
                continue

            plugins.append(
                InstalledPlugin(
                    repository=repository,
                    manifest=manifest,
                )
            )

        return plugins

    def _get_installed_plugin(self, name: str) -> InstalledPlugin:
        """Return the unique installed plugin with the given manifest name."""
        matches = [plugin for plugin in self.list_plugins() if plugin.manifest.name == name]

        if not matches:
            raise PluginNotFoundError(name)

        if len(matches) > 1:
            raise PluginRepositoryError(f"Multiple installed plugins are named: {name}")

        return matches[0]

    def load_plugins(self, root_app: typer.Typer) -> None:
        for installed_plugin in self.list_plugins():
            loader = PluginLoader(installed_plugin.repository)
            plugin = loader.load_plugin(installed_plugin.manifest)

            api = PluginAPI(
                manifest=installed_plugin.manifest,
                _root_app=root_app,
            )

            plugin.register(api)
