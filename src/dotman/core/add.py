import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from dotman.core.config import (
    ExitCode,
    InternalFileSystemObject,
    StrPath,
    get_temp_log_file,
    load_config,
)
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
    """Rollback journal storing file operations in TOML for recovery."""

    ORIGINAL_PATH = "original_path"
    NEW_PATH = "new_path"

    def __init__(self, log_file: StrPath | None = None):
        self.path = Path(log_file) if log_file else get_temp_log_file(load_config())
        self.entries: list[dict[str, str]] = []

    def clear(self):
        """Clears the log file."""
        if self.path.exists():
            self.path.unlink()

    def add_entry(self, original: Path, new: Path) -> None:
        self.entries.append(
            {
                self.ORIGINAL_PATH: str(original),
                self.NEW_PATH: str(new),
            }
        )

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)

        with self.path.open("w", encoding="utf-8") as f:
            json.dump({"files": self.entries}, f, indent=2)

    def rollback(self):
        with self.path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        # Reverse the entries to restore the files in reverse order (Not matters today)
        for entry in reversed(data.get("files", [])):
            original_path = Path(entry[self.ORIGINAL_PATH])
            new_path = Path(entry[self.NEW_PATH])

            if new_path.exists():
                new_path.rename(original_path)
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

        self.package = package  # Assumed that @src/dotman/core/service/add_service.py sanitizes the package name
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
        return (
            self.dotfiles_dir
            / InternalFileSystemObject.PROFILES.value
            / self.profile_name
        )

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
        self.log_book.save()

        # Ensure the parent directory of the destination exists before moving the file
        self.destination.parent.mkdir(parents=True, exist_ok=True)

        # Move the file to the destination
        self.file.rename(self.destination)
        return ExitCode.SUCCESS

    def file_exists_in_package(self) -> bool:
        """Checks if the file exists in the package directory."""
        return (
            self.profile_root / self.package / self.file.relative_to(self.home_dir)
        ).exists()

    def has_files_in_package(self, pkg: str | None = None) -> bool:
        """Checks is any file exists in the package directory."""
        path = (
            Path(self.profile_root / pkg) if pkg else (self.profile_root / self.package)
        )

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
                    SymlinkCheck(
                        path, SymlinkStatus.OK, f"points inside added path: {target}"
                    )
                )

        return checks
