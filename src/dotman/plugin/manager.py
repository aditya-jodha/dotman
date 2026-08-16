# ruff: noqa: TRY003
"""
Module for managing the installation, update, and lifecycle of plugins.

This module provides tools to download plugins from remote Git repositories
or load them from local system directories, handle manifests, and track
available plugin states.
"""

import logging
import re
import shutil
import tomllib
from importlib.metadata import EntryPoint, distributions
from pathlib import Path
from urllib.parse import urlparse

import typer

from dotman.errors.plugin_errors import (
    InvalidPluginSourceError,
    PluginNotFoundError,
    PluginRepositoryError,
)
from dotman.plugin.api import PluginAPI

from .environment import PluginEnvironment
from .installer import PluginInstaller
from .loader import PluginLoader
from .manifest import InstalledPlugin, PluginManifest
from .repository import PluginRepository
from .validation import ValidationRegistry


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

    # ==========================================
    # Public Lifecycle Methods
    # ==========================================

    def install(self, source: str) -> PluginManifest:
        """Install a plugin from a Git repository URL."""
        if not self.is_git_source(source):
            raise InvalidPluginSourceError(source)

        repository_name = self._repository_name(source)
        target_dir = self.plugins_dir / repository_name
        repository = PluginRepository.clone(url=source, target_dir=target_dir)

        try:
            self.installer.install(repository)
            manifest = self._get_installed_plugin_by_repository(repository).manifest
        except Exception:
            # shutil.rmtree(target_dir, ignore_errors=True)
            # TODO FIXME : will fix later
            logging.getLogger(__name__).warning(
                "Failed to install the repo WILL NOT DELETE IT AS FOR TESTING PURPOSE: %s",
                target_dir,
                exc_info=True,
            )
            raise

        return manifest

    def uninstall(self, name: str) -> None:
        """Uninstall a plugin."""
        installed_plugin = self._get_installed_plugin(name)
        repository = self._get_managed_repository(installed_plugin.manifest.distribution_name)

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
        """Discover plugins installed in managed plugin environments."""
        plugins: list[InstalledPlugin] = []

        for path in self.plugins_dir.iterdir():
            if not path.is_dir():
                continue

            try:
                repository = PluginRepository(path)
                environment = PluginEnvironment(repository.path)
                loader = PluginLoader(environment)

                for entry_point in self._plugin_entry_points(environment):
                    try:
                        manifest = loader.load_manifest(entry_point)

                    except PluginRepositoryError:
                        logging.getLogger(__name__).warning(
                            "Skipping invalid plugin entry point: %s",
                            entry_point.name,
                            exc_info=True,
                        )
                        continue

                    plugins.append(
                        InstalledPlugin(
                            repository=repository,
                            manifest=manifest,
                        )
                    )

            except (OSError, PluginRepositoryError):
                logging.getLogger(__name__).warning(
                    "Skipping invalid plugin repository: %s",
                    path,
                    exc_info=True,
                )

        return plugins

    def load_plugins(self, root_app: typer.Typer) -> ValidationRegistry:
        """Load installed plugins into the root application and return the validation registry."""
        registry = ValidationRegistry()

        for installed in self.list_plugins():
            try:
                loader = PluginLoader(installed.environment)

                plugin, manifest = loader.load_plugin(installed.manifest)

                api = PluginAPI(
                    manifest=manifest,
                    _root_app=root_app,
                    _validation_registry=registry,
                )

                plugin.register(api)
                api._commit()  # pyright: ignore[reportPrivateUsage]
            except Exception:  # noqa: BLE001 - third-party plugin code must not stop the CLI
                logging.getLogger(__name__).warning(
                    "Skipping plugin %s because it failed to load",
                    installed.manifest.name,
                    exc_info=True,
                )

        return registry

    # ==========================================
    # Public Static Utilities
    # ==========================================

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

    # ==========================================
    # Private Instance Helpers
    # ==========================================

    def _get_installed_plugin(self, name: str) -> InstalledPlugin:
        """Return the unique installed plugin with the given manifest name."""
        matches = [plugin for plugin in self.list_plugins() if plugin.manifest.name == name]

        if not matches:
            raise PluginNotFoundError(name)

        if len(matches) > 1:
            raise PluginRepositoryError(f"Multiple installed plugins are named: {name}")

        return matches[0]

    def _get_installed_plugin_by_repository(
        self,
        repository: PluginRepository,
    ) -> InstalledPlugin:
        """Fetch an installed plugin specifically by its repository."""
        environment = PluginEnvironment(repository.path)

        entry_points = self._plugin_entry_points(environment)

        if len(entry_points) != 1:
            raise PluginRepositoryError(
                "Installed package must expose exactly one dotman.plugins entry point",
                path=repository.path,
            )

        loader = PluginLoader(environment)
        manifest = loader.load_manifest(entry_points[0])

        return InstalledPlugin(
            repository=repository,
            manifest=manifest,
        )

    def _get_managed_repository(self, distribution_name: str | None) -> PluginRepository:
        """Get the managed repository with the given distribution name."""
        if distribution_name is None:
            raise PluginRepositoryError("Plugin has no distribution name")

        for path in self.plugins_dir.iterdir():
            if not path.is_dir():
                continue
            try:
                if self._normalise_distribution_name(
                    self._project_name(path)
                ) == self._normalise_distribution_name(distribution_name):
                    return PluginRepository(path)
            except (OSError, KeyError, tomllib.TOMLDecodeError):
                continue
        raise PluginRepositoryError(
            f"Managed repository not found for plugin distribution: {distribution_name}"
        )

    def _plugin_entry_points(
        self,
        environment: PluginEnvironment,
    ) -> list[EntryPoint]:
        site_packages = environment.site_packages

        if not site_packages.exists():
            return []

        return [
            entry_point
            for distribution in distributions(
                path=[str(site_packages)]
            )  # This is important to avoid importing the wrong environment
            for entry_point in distribution.entry_points
            if entry_point.group == "dotman.plugins"
        ]

    # ==========================================
    # Private Static Utilities
    # ==========================================

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

        return Path(path.rstrip("/")).expanduser().resolve().stem

    @staticmethod
    def _project_name(repository_path: Path) -> str:
        with (repository_path / "pyproject.toml").open("rb") as file:
            data = tomllib.load(file)
        return data["project"]["name"]

    @staticmethod
    def _normalise_distribution_name(name: str) -> str:
        return re.sub(r"[-_.]+", "-", name).lower()
