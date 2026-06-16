from pathlib import Path

from .dotman_error import DotmanError


class SymlinkNotSupportedError(DotmanError):
    """Raised when a symlink file comes in AddFiles logic. This is a user error."""

    def __init__(self, *args: object) -> None:
        super().__init__(
            *args,
            message=(
                "The selected file path is a symbolic link.\n\n"
                + "Dotman only manages real files and directories.\n"
                + "Add the symlink target instead."
            ),
        )


class FileDoesNotExistError(DotmanError):
    """Raised when a file does not exist. This is a user error"""

    def __init__(self, file: Path) -> None:
        super().__init__(message=f"File {file} does not exist")


class IsNotASubPathError(DotmanError):
    """Raised when a path is not a subpath of the home directory. This is a user error."""

    def __init__(self, file: Path) -> None:
        super().__init__(
            message=f"file `{file}` is not a subpath of the home directory"
        )


class FileOutsideHomeError(DotmanError):
    """Raised when a file is outside the home directory. This is a user error."""

    def __init__(self, file: Path) -> None:
        super().__init__(message=f"File `{file}` is outside the home directory")


class InvalidPackageNameError(DotmanError):
    """Raised when a package name is invalid. This is a user error."""

    def __init__(self, package: str | None, is_internal_package: bool) -> None:
        super().__init__(message=f"Package name `{package}` is invalid")
        self.dotman_internal_package = is_internal_package


class TargetFileIsHomeError(DotmanError):
    """Raised when the target file is the home directory. This is a user error."""

    def __init__(self, file: Path) -> None:
        super().__init__(message=f"Target file `{file}` is the home directory")


class TargetFileIsDotfilesDirError(DotmanError):
    """Raised when the target file is the dotfiles directory. This is a user error."""

    def __init__(self, file: Path) -> None:
        super().__init__(message=f"Target file `{file}` is the dotfiles directory")


class FileNameCollidingError(DotmanError):
    """Raised when the target file name present in dotfiles directory"""

    def __init__(self, file: Path) -> None:
        super().__init__(
            message=f"Target file `{file}` name is colliding inside home directory"
        )


class PackageNotExistsError(DotmanError):
    """"""

    def __init__(self) -> None:
        super().__init__(message="Package not exist.")
