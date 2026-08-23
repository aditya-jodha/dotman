"""Module for installing and managing plugin Python packages."""

# ruff: noqa: TRY003

from __future__ import annotations

import shutil
import subprocess
from typing import TYPE_CHECKING

from dotman.errors.plugin_errors import PluginInstallationError
from dotman.plugin.environment import PluginEnvironment

if TYPE_CHECKING:
    from dotman.plugin.repository import PluginRepository


class PluginInstaller:
    """Installs and manages the Python package of a plugin."""

    def install(self, repository: PluginRepository) -> None:
        """Create an isolated environment and install the plugin package."""
        uv_path = self._find_uv
        environment = PluginEnvironment(repository.path)

        try:
            subprocess.run(  # noqa: S603
                [uv_path, "venv", str(environment.environment_path)],
                cwd=repository.path,
                check=True,
            )

            subprocess.run(  # noqa: S603
                [
                    uv_path,
                    "pip",
                    "install",
                    "--python",
                    str(environment.python),
                    ".",
                ],
                cwd=repository.path,
                check=True,
            )

        except (OSError, subprocess.CalledProcessError) as e:
            raise PluginInstallationError(
                f"Failed to install plugin from {repository.path}",
            ) from e

    def uninstall(self, distribution_name: str) -> None:
        """Uninstall a plugin Python package."""
        uv_path = self._find_uv

        try:
            subprocess.run(  # noqa: S603 - executable resolved via shutil.which()
                [uv_path, "pip", "uninstall", distribution_name],
                check=True,
            )
        except (OSError, subprocess.CalledProcessError) as e:
            raise PluginInstallationError(
                f"Failed to uninstall plugin package {distribution_name}",
            ) from e

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
