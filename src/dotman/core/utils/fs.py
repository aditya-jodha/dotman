from collections.abc import Iterable
from pathlib import Path
from typing import TYPE_CHECKING

from dotman.core.config import ExitCode

if TYPE_CHECKING:
    from os import stat_result

type InodeKey = tuple[int, int]


class FileSystemUtil:
    """A highly optimized collection of advanced, safe filesystem utilities."""

    def __init__(self, ignore_patterns: Iterable[str] | None = None) -> None:
        """Initialize the utility with optional global pattern filters (e.g., ['.git', '.DS_Store'])."""
        self.ignore_patterns: list[str] = list(ignore_patterns) if ignore_patterns else []

    def __call__(self, target_dir: Path) -> bool:
        """Allows instantiating and calling the utility seamlessly like a function."""
        return self.path_has_files(target_dir)

    @staticmethod
    def normalize_path(path: Path) -> Path:
        """Normalizes the path to absolute form."""
        path = path.expanduser()

        if not path.is_absolute():
            path = Path.cwd() / path

        return path.resolve(strict=False)

    @staticmethod
    def delete_empty_package(profile_path: Path, file: Path) -> ExitCode:
        current = file.parent

        while current != profile_path:
            if next(current.iterdir(), None) is not None:
                # If there are any directories/files in the current path, we will not delete the package
                break

            current.rmdir()
            current = current.parent
        else:
            return ExitCode.SUCCESS
        return ExitCode.INVALID_ARGUMENTS

    @staticmethod
    def get_inode_key(item: Path) -> InodeKey | None:
        """Safely fetch the unique hardware identifier for an item without mutating instance state."""
        try:
            stat: stat_result = item.stat(follow_symlinks=False)
        except OSError:
            return None
        else:
            return (stat.st_dev, stat.st_ino)

    @staticmethod
    def is_valid_file_or_link(item: Path) -> bool:
        """Check if the item is a real file or a symlink resolving to a file."""
        if item.is_file():
            return True
        if item.is_symlink():
            try:
                return item.resolve().is_file()
            except OSError:
                return False
        return False

    def _should_ignore(self, item: Path) -> bool:
        """Helper to quickly check if a path falls under predefined ignore rules."""
        return any(pattern in item.parts for pattern in self.ignore_patterns)

    def path_has_files(self, target_dir: Path) -> bool:
        """Recursively check if there are any valid files inside a target directory."""
        visited_inodes: set[InodeKey] = set()

        try:
            for item in target_dir.rglob("*"):
                # 1. Check ignore list first to save compute overhead
                if self._should_ignore(item):
                    continue

                # 2. Extract hardware properties
                inode_key = self.get_inode_key(item)
                if inode_key is None or inode_key in visited_inodes:
                    continue

                visited_inodes.add(inode_key)

                # 3. Short-circuit return on find
                if self.is_valid_file_or_link(item):
                    return True

        except RecursionError:
            return True

        return False
