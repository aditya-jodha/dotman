from pathlib import Path


class DotmanInitializerError(Exception):
    """Base class for all dotman initializer errors."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

    @property
    def error(self) -> str:
        return self.message


class DotmanDotfilesBackupDirExistsError(DotmanInitializerError):
    """Raised when the dotfiles backup directory already exists."""

    def __init__(self, dotfiles_dir: Path) -> None:
        super().__init__(message=f"Dotfiles backup directory already exists at {dotfiles_dir}")
        self.dotfiles_dir = dotfiles_dir


class DotmanDotfilesDirError(DotmanInitializerError):
    """Raised when the dotfiles directory already exists."""

    def __init__(self, dotfiles_dir: Path) -> None:
        super().__init__(message=f"Dotfiles directory already exists at {dotfiles_dir}")
        self.dotfiles_dir = dotfiles_dir
