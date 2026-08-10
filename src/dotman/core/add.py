import sqlite3
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from dotman.core.config.config import (
    DotmanConfig,
    InternalFileSystemObject,
    get_temp_log_file,
)
from dotman.core.config.types import StrPath
from dotman.core.utils.fs import FileSystemUtil
from dotman.errors.custom_errors import (
    FileDoesNotExistError,
    FileNameCollidingError,
    InvalidPackageNameError,
    IsNotASubPathError,
    SymlinkNotSupportedError,
    TargetFileIsDotfilesDirError,
    TargetFileIsHomeError,
)
from dotman.errors.dotman_error import ExitCode


class SymlinkStatus(Enum):
    OK = "ok"
    WARN = "warn"
    ERROR = "error"


@dataclass
class SymlinkCheck:
    path: Path
    status: SymlinkStatus
    message: str


class RollbackJournal:
    """SQLite-backed journal for reversible file operations."""

    def __init__(self, log_file: StrPath | None = None) -> None:
        self.path = Path(log_file) if log_file else get_temp_log_file(DotmanConfig.load())

        self._init_db()

    def _init_db(self) -> None:
        """Initialize the SQLite journal database.

        WAL mode improves durability and crash recovery characteristics
        for journal writes.
        """
        self.path.parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(self.path) as conn:
            conn.execute("PRAGMA journal_mode=WAL")

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS journal (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    original_path TEXT NOT NULL,
                    new_path TEXT NOT NULL
                )
                """
            )

    def add_entry(self, original: Path, new: Path) -> None:
        """Record a file operation."""
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                """
                INSERT INTO journal (original_path, new_path)
                VALUES (?, ?)
                """,
                (str(original), str(new)),
            )

    def clear(self) -> None:
        """Clear the journal."""
        with sqlite3.connect(self.path) as conn:
            conn.execute("DELETE FROM journal")

    def rollback(self) -> None:
        """Rollback all recorded file operations."""
        with sqlite3.connect(self.path) as conn:
            rows = conn.execute(
                """
                SELECT original_path, new_path
                FROM journal
                ORDER BY id DESC
                """
            ).fetchall()

            for original_path, new_path in rows:
                original = Path(original_path)
                new = Path(new_path)

                if new.exists():
                    new.rename(original)

            self.clear()


class AddFiles:
    """Class to handle adding files to the dotfiles directory.\n
    NOTE: PACKAGE SHOULD NOT BE NAME AS THE INTERNAL dotman DIRECTORY i.e. `packages`"""

    def __init__(
        self,
        profile_name: str,
        home_dir: Path,
        dotfiles_dir: Path,
        file: Path,
        package: str,
        logbook: RollbackJournal,
    ):
        self.profile_name = profile_name
        self.home_dir = home_dir.resolve()
        self.dotfiles_dir = dotfiles_dir.resolve()

        self.input_file = file.expanduser()
        self.file = FileSystemUtil.normalize_path(file)

        self.package = package  # Package name is already sanitized by AddService.
        self.log_book = logbook

    @property
    def is_dir(self) -> bool:
        """Checks if the file is a directory."""
        return self.file.is_dir()

    @property
    def package_exists(self) -> bool:
        """Checks if the package directory exists in the dotfiles directory."""
        return (self.profile_root / self.package).exists()

    @property
    def profile_root(self) -> Path:
        return self.dotfiles_dir / InternalFileSystemObject.PROFILES.value / self.profile_name

    @property
    def is_file_in_package(self) -> bool:
        """Check name collision."""
        return self.destination.exists() or self.destination.is_symlink()

    @property
    def destination(self) -> Path:
        rel_path = self.file.relative_to(self.home_dir)
        return self.profile_root / self.package / rel_path

    def validate(self) -> None:
        """This validates all the scenario, and make destination class instance."""
        # Order matters for user to get a reasonable answer.
        # NOTE: whenever new error added here, need to update the service_add.py file as well.
        if self.file == self.home_dir:
            raise TargetFileIsHomeError(self.file)
        if self.file == self.dotfiles_dir:
            raise TargetFileIsDotfilesDirError(self.file)

        if self.input_file.is_symlink():
            raise SymlinkNotSupportedError()

        if not self.file.exists():
            raise FileDoesNotExistError(self.file)

        if not self.file.is_relative_to(self.home_dir):
            raise IsNotASubPathError(self.home_dir)

        if self.package == "":
            raise InvalidPackageNameError(self.package, False)

        if self.package in InternalFileSystemObject.values():
            raise InvalidPackageNameError(self.package, True)

        if self.is_file_in_package:
            raise FileNameCollidingError(self.file)

    def create_package(self):
        """Creates the directory inside dotfiles"""
        pkg_to_create = self.profile_root / self.package
        pkg_to_create.mkdir(parents=True)

    def delete_empty_package(self) -> ExitCode:
        """Deletes empty package in the dotfiles directory."""
        return FileSystemUtil.delete_empty_package(self.profile_root, self.destination)

    def move_file_to_dotfiles(self) -> ExitCode:
        """Moves the specified file to the dotfiles directory.
        by creating a dir into dotfiles named as package"""

        # Writes log for backup
        self.log_book.add_entry(self.file, self.destination)

        # Ensure the parent directory of the destination exists before moving the file
        self.destination.parent.mkdir(parents=True, exist_ok=True)

        # Move the file to the destination
        self.file.rename(self.destination)
        return ExitCode.SUCCESS

    def file_exists_in_package(self) -> bool:
        """Checks if the file exists in the package directory."""
        return (self.profile_root / self.package / self.file.relative_to(self.home_dir)).exists()

    def has_files_in_package(self, pkg: str | None = None) -> bool:
        """Checks is any file exists in the package directory."""
        path = Path(self.profile_root / pkg) if pkg else (self.profile_root / self.package)

        # Returns True if at least one item inside is a regular file
        return FileSystemUtil()(path)

    def validate_directory_symlinks(self) -> list[SymlinkCheck]:
        """
        Scans the file or directory for symlinks and returns a list of SymlinkCheck objects.
        """
        checks: list[SymlinkCheck] = []
        if self.file.is_dir():
            paths = self.file.rglob("*")
            root = self.file.resolve()
        else:
            return checks

        for path in paths:
            if not path.is_symlink():
                continue

            try:
                target = path.resolve(strict=True)
            except FileNotFoundError:
                checks.append(SymlinkCheck(path, SymlinkStatus.ERROR, "broken symlink"))
                continue
            except (RuntimeError, OSError):
                checks.append(SymlinkCheck(path, SymlinkStatus.ERROR, "symlink loop"))
                continue

            if not target.is_relative_to(root):
                checks.append(
                    SymlinkCheck(
                        path,
                        SymlinkStatus.ERROR,
                        f"points outside added path: {target}",
                    )
                )
            else:
                checks.append(
                    SymlinkCheck(path, SymlinkStatus.OK, f"points inside added path: {target}")
                )

        return checks
