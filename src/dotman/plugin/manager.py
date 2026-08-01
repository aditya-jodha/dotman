"""
Module for managing the installation, update, and lifecycle of plugins.

This module provides tools to download plugins from remote Git repositories
or load them from local system directories, handle manifests, and track
available plugin states.
"""

from pathlib import Path
from urllib.parse import urlparse

import typer

from dotman.errors.plugin_errors import InvalidPluginSourceError, PluginRepositoryError
from dotman.plugin.api import PluginAPI

from .installer import PluginInstaller
from .loader import PluginLoader
from .manifest import InstalledPlugin, PluginManifest
from .repository import PluginRepository


class PluginManager:
    """Handles core lifecycles for plugins including discovery, installation, and updates.

    Attributes:
        plugin_dir: A Path object referencing the central workspace directory
            where plugin code repos are installed and stored.
    """

    def __init__(
        self,
        plugin_dir: Path,
        installer: PluginInstaller,
    ) -> None:
        self.installer = installer

        self.plugin_dir = plugin_dir
        self.plugin_dir.mkdir(parents=True, exist_ok=True)

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
            return path.is_dir()

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

        repository = PluginRepository.clone(
            url=source,
            target_dir=self.plugin_dir / repository_name,
        )

        loader = PluginLoader(repository)
        manifest = loader.load_manifest()

        self.installer.install(repository)

        return manifest

    def uninstall(self, name: str):
        """Uninstall a plugin."""
        ...

    def update(self, name: str):
        """Update an installed plugin."""
        ...
        # repository = self._get_repository(name)
        # repository.fetch()

    def list_plugins(self) -> list[InstalledPlugin]:
        plugins: list[InstalledPlugin] = []

        for plugin_dir in self.plugin_dir.iterdir():
            if not plugin_dir.is_dir():
                continue

            try:
                repository = PluginRepository(plugin_dir)
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

    def load_plugins(self, root_app: typer.Typer) -> None:
        for installed_plugin in self.list_plugins():
            loader = PluginLoader(installed_plugin.repository)
            plugin = loader.load_plugin(installed_plugin.manifest)

            api = PluginAPI(
                manifest=installed_plugin.manifest,
                _root_app=root_app,
            )

            plugin.register(api)
