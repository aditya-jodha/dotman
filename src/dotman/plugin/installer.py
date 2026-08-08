"""Module for installing and managing plugin Python packages."""

# ruff: noqa: TRY003

from __future__ import annotations

import shutil
import subprocess
from typing import TYPE_CHECKING

from dotman.errors.plugin_errors import PluginInstallationError

if TYPE_CHECKING:
    from dotman.plugin.repository import PluginRepository


class PluginInstaller:
    """Installs and manages the Python package of a plugin."""

    def install(self, repository: PluginRepository) -> None:
        """Install a plugin Python package from its repository."""
        uv_path = self._find_uv

        try:
            subprocess.run(  # noqa: S603 - executable resolved via shutil.which()
                [uv_path, "pip", "install", "."],
                cwd=repository.path,
                check=True,
            )
        except (OSError, subprocess.CalledProcessError) as e:
            raise PluginInstallationError(
                f"Failed to install plugin from {repository.path}",
            ) from e

    def uninstall(self, repository: PluginRepository) -> None:
        """Uninstall a plugin Python package."""
        ...

    def update(self, repository: PluginRepository) -> None:
        """Update a plugin Python package."""
        ...

    # ===== Helper methods =====

    @property
    def _find_uv(self) -> str:
        """Find the uv executable."""
        uv_path = shutil.which("uv")

        if uv_path is None:
            raise PluginInstallationError(
                "uv executable not found",
            )

        return uv_path
