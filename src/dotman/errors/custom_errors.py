from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from dotman.errors.dotman_error import (
    Category,
    DotmanError,
    ErrorContext,
    ExitCode,
    FilesystemError,
)

# ----------------------------------------------------
# Leaf Context Schemas
# ----------------------------------------------------


@dataclass(frozen=True)
class PathErrorContext(ErrorContext):
    """Context payload tracking standard file or directory paths."""

    file_path: Path


@dataclass(frozen=True)
class SubPathErrorContext(ErrorContext):
    """Context payload for verifying structural path bounds."""

    file_path: Path
    boundary_type: Literal["home", "dotfiles"]


@dataclass(frozen=True)
class PackageErrorContext(ErrorContext):
    """Context payload tracking concrete package identifiers."""

    package_name: str | None
    is_internal: bool


# ----------------------------------------------------
# Leaf Concrete Exceptions
# ----------------------------------------------------


class SymlinkNotSupportedError(FilesystemError):
    EXIT_CODE = ExitCode.INVALID_ARGUMENTS

    def __init__(self, *args: object) -> None:
        # Keeps original positional *args processing safe
        if args:
            raise TypeError("SymlinkNotSupportedError does not accept positional arguments")  # noqa: TRY003

        self.message = (
            "The selected file path is a symbolic link.\n\n"
            "Dotman only manages real files and directories.\n"
            "Add the symlink target instead."
        )
        super().__init__(message=self.message)


class FileDoesNotExistError(FilesystemError):
    EXIT_CODE = ExitCode.INVALID_ARGUMENTS

    def __init__(self, file: Path) -> None:
        self.message = f"File {file} does not exist"
        super().__init__(message=self.message, context=PathErrorContext(file_path=file))


class IsNotASubPathError(FilesystemError):
    EXIT_CODE = ExitCode.INVALID_ARGUMENTS

    def __init__(self, file: Path, of: Literal["home", "dotfiles"] = "home") -> None:
        self.message = f"file `{file}` is not a subpath of the {of} directory"
        # Keeps your original explicit instance variable intact
        self.file = file
        super().__init__(
            message=self.message, context=SubPathErrorContext(file_path=file, boundary_type=of)
        )


class FileOutsideHomeError(FilesystemError):
    EXIT_CODE = ExitCode.INVALID_ARGUMENTS

    def __init__(self, file: Path) -> None:
        self.message = f"File `{file}` is outside the home directory"
        super().__init__(message=self.message, context=PathErrorContext(file_path=file))


class InvalidPackageNameError(DotmanError):
    EXIT_CODE = ExitCode.INVALID_ARGUMENTS
    CATEGORY = Category.GENERIC

    def __init__(self, package: str | None, is_internal_package: bool) -> None:
        self.dotman_internal_package = is_internal_package
        pkg_type = "internal" if self.dotman_internal_package else "external"
        self.message = f"Invalid {pkg_type} package name: {package}"
        super().__init__(
            message=self.message,
            context=PackageErrorContext(package_name=package, is_internal=is_internal_package),
        )


class TargetFileIsHomeError(FilesystemError):
    EXIT_CODE = ExitCode.INVALID_ARGUMENTS

    def __init__(self, file: Path) -> None:
        self.message = f"Target file `{file}` can't is the home directory"
        super().__init__(message=self.message, context=PathErrorContext(file_path=file))


class TargetFileIsDotfilesDirError(FilesystemError):
    EXIT_CODE = ExitCode.INVALID_ARGUMENTS

    def __init__(self, file: Path) -> None:
        self.message = f"Target file `{file}` is the dotfiles directory"
        super().__init__(message=self.message, context=PathErrorContext(file_path=file))


class FileNameCollidingError(FilesystemError):
    EXIT_CODE = ExitCode.INVALID_ARGUMENTS

    def __init__(self, file: Path) -> None:
        self.message = f"Target file `{file}` name is colliding"
        super().__init__(message=self.message, context=PathErrorContext(file_path=file))


class PackageNotExistsError(DotmanError):
    EXIT_CODE = ExitCode.INVALID_ARGUMENTS
    CATEGORY = Category.GENERIC

    def __init__(self) -> None:
        self.message = "No packages found."
        super().__init__(message=self.message)
