import tomllib
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from dotman.core.config import EXITCODE, InternalFileSystemObject, StrPath, load_config, make_temp_log_file
from dotman.errors.custom_errors import (
    FileDoesNotExistError,
    FileNameCollidingError,
    InvalidPackageNameError,
    IsNotASubPathError,
    SymFileCameInAddFilesLogicError,
    TargetFileIsDotfilesDirError,
    TargetFileIsHomeError,
)


class SymlinkStatus(Enum):
    OK = "ok"
    WARN = "warn"
    ERROR = "error"
    SKIP = "skip"


@dataclass
class SymlinkCheck:
    path: Path
    status: SymlinkStatus
    message: str


class LogBook:
    """It will write a temp logs in form of toml of transfered files so user can easily
    restore the files if something goes wrong."""

    def __init__(self, log_file: StrPath | None = None):
        self.cgf = load_config()
        self.log_file = Path(log_file) if log_file else make_temp_log_file(self.cgf)

    def clear_log(self):
        """Clears the log file."""
        if self.log_file.exists():
            self.log_file.unlink()

    def create_log(self):
        """Creates the log file if it does not exist."""
        if not self.log_file.exists():
            self.log_file.touch()
        else:
            raise FileExistsError(f"Log file '{self.log_file}' already exists.")  # noqa: TRY003

    def show_log(self):
        if self.log_file.exists():
            with self.log_file.open("r") as f:
                return f.read()
        else:
            return "No log entries found."

    def write_log(self, original_path: Path, new_path: Path):
        log_entry = f'[[files]]\noriginal_path = "{original_path}"\nnew_path = "{new_path}"\n\n'
        with self.log_file.open("a") as f:
            f.write(log_entry)

    def restore_files(self):
        with self.log_file.open("rb") as f:
            data = tomllib.load(f)
        _data = data.get("files", [])
        for entry in _data:
            original_path = Path(entry["original_path"])
            new_path = Path(entry["new_path"])
            if new_path.exists():
                new_path.rename(original_path)
        self.clear_log()


class AddFiles:
    """Class to handle adding files to the dotfiles directory.\n
    NOTE: PACKAGE SHOULD NOT BE NAME AS THE INTERNAL DOTMAN DIRECTORY i.e. `packages`"""

    def __init__(
        self,
        profile_name: str,
        home_dir: Path,
        dotfiles_dir: Path,
        file: Path,
        package: str,
        logbook: LogBook,
    ):
        self.profile_name = profile_name
        self.home_dir = home_dir.resolve()
        self.dotfiles_dir = dotfiles_dir.resolve()
        self.file = file.resolve(strict=False)
        self.original_file = file
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
    def profile_root(self):
        return self.dotfiles_dir / "profiles" / self.profile_name

    def is_file_in_package(self):
        """Check name collision."""
        return self.destination.exists() or self.destination.is_symlink()

    def validate(self) -> None:
        """This validates all the senario, and make destination class instance."""
        # Order matters for user to get a reasonable answer.
        # NOTE: whenever new error added here, need to update the service_add.py file as well.
        if self.file == self.home_dir:
            raise TargetFileIsHomeError(self.file)
        if self.file == self.dotfiles_dir:
            raise TargetFileIsDotfilesDirError(self.file)

        if self.original_file.is_symlink():
            raise SymFileCameInAddFilesLogicError()

        if not self.file.exists():
            raise FileDoesNotExistError(self.file)

        if not self.file.is_relative_to(self.home_dir):
            raise IsNotASubPathError(self.home_dir)

        if self.package == "":
            raise InvalidPackageNameError(self.package.__str__(), False)

        if str(self.package) in InternalFileSystemObject.values():
            raise InvalidPackageNameError(self.package.__str__(), True)

        rel_path = self.file.relative_to(self.home_dir)
        self.destination = self.profile_root / self.package / rel_path

        if self.is_file_in_package():
            raise FileNameCollidingError(self.file)

    def create_package(self):
        """Creates the directory inside dotfiles"""
        pkg_to_create = self.profile_root / self.package
        pkg_to_create.mkdir(parents=True, exist_ok=False)

    def delete_empty_package(self) -> EXITCODE:
        """Deletes empty package in the dotfiles directory."""
        current = self.destination.parent

        while current != self.dotfiles_dir:
            if any(item.is_dir() for item in current.iterdir()):
                break

            current.rmdir()
            current = current.parent
        else:
            return 0
        return 1

    def move_dir_to_dotfiles(self) -> EXITCODE:
        """Moves the specified directory to the dotfiles directory.
        by creating a dir into dotfiles named as package"""
        # since we are moving the whole directory, we will move it to the package directory directly
        return self.move_file_to_dotfiles()

    def move_file_to_dotfiles(self) -> EXITCODE:
        """Moves the specified file to the dotfiles directory.
        by creating a dir into dotfiles named as package"""

        # Writes log for backup
        self.log_book.write_log(self.file, self.destination)

        # Ensure the parent directory of the destination exists before moving the file
        self.destination.parent.mkdir(parents=True, exist_ok=True)

        # Move the file to the destination
        self.file.rename(self.destination)
        return 0

    def file_exists_in_package(self) -> bool:
        """Checks if the file exists in the package directory."""
        return (self.profile_root / self.package / self.file.relative_to(self.home_dir)).exists()

    def has_files_in_package(self, pkg: str | None = None) -> bool:
        """Checks if the log file has any entries for files in the package."""
        path = Path(self.profile_root / pkg) if pkg else Path(self.profile_root / self.package)

        # Returns True if at least one item inside is a regular file
        return any(item.is_file() for item in path.iterdir())

    def validate_directory_symlinks(self) -> list[SymlinkCheck]:
        """
        Scans the file or directory for symlinks and returns a list of SymlinkCheck objects.
        """
        checks: list[SymlinkCheck] = []
        if self.file.is_symlink():
            paths = [self.file]
            root = self.file.parent.resolve()
        elif self.file.is_dir():
            paths = self.file.rglob("*")
            root = self.file.resolve()
        else:
            return checks

        for path in paths:
            if not path.is_symlink():
                continue

            if not path.exists():
                checks.append(SymlinkCheck(path, SymlinkStatus.ERROR, "broken symlink"))
                continue

            try:
                target = path.resolve()
            except RuntimeError:
                checks.append(SymlinkCheck(path, SymlinkStatus.ERROR, "symlink loop"))
                continue

            if not target.is_relative_to(root):
                checks.append(SymlinkCheck(path, SymlinkStatus.ERROR, f"points outside added path: {target}"))
            else:
                checks.append(SymlinkCheck(path, SymlinkStatus.OK, f"points inside added path: {target}"))

        return checks
