"""Module for managing plugin repositories."""

# ruff: noqa: TRY003
from __future__ import annotations

from typing import TYPE_CHECKING

from dulwich import porcelain
from dulwich.errors import NotGitRepository
from dulwich.repo import Repo

from dotman.errors.plugin_errors import (
    PluginRepositoryError,
    PluginRepositoryNotFoundError,
)

if TYPE_CHECKING:
    from pathlib import Path


class PluginRepository:
    """Represents a plugin repository managed by Dotman."""

    def __init__(self, path: Path) -> None:
        self.path = path.resolve()

        try:
            self.repo = Repo(str(path))
        except (NotGitRepository, OSError) as e:
            raise PluginRepositoryNotFoundError(path) from e

    @classmethod
    def clone(cls, url: str, target_dir: Path) -> PluginRepository:
        """Clone a plugin repository from a remote URL."""
        try:
            porcelain.clone(url, str(target_dir))
        except OSError as e:
            raise PluginRepositoryError(f"Failed to clone {url} into {target_dir}: {e}") from e

        return cls(target_dir)

    def fetch(self, remote: str = "origin") -> None:
        """Fetch updates from a remote."""
        try:
            porcelain.fetch(self.repo, remote)
        except OSError as e:
            raise PluginRepositoryError(f"Failed to fetch from {remote}: {e}") from e

    def checkout(self, ref: str = "main") -> None:
        """Checkout a Git reference."""
        try:
            porcelain.update_head(self.repo, ref)
        except OSError as e:
            raise PluginRepositoryError(f"Failed to checkout {ref}: {e}") from e

    def current_commit(self) -> str:
        """Return the current commit hash."""
        try:
            return self.repo.head().decode("utf-8")
        except Exception as e:
            path = getattr(self, "path", None)
            raise PluginRepositoryError(
                "Failed to get current commit: repository not found at path {path}",
                path=path,
            ) from e
