from pathlib import Path

from dotman.errors.dotman_error import DotmanError


class DotmanDotfilesBackupDirExistsError(DotmanError):
    """Raised when the dotfiles backup directory already exists."""

    def __init__(self, dotfiles_dir: Path) -> None:
        super().__init__(
            message=f"Dotfiles backup directory already exists at {dotfiles_dir}"
        )
        self.dotfiles_dir = dotfiles_dir


class DotmanDotfilesDirError(DotmanError):
    """Raised when the dotfiles directory already exists."""

    def __init__(self, dotfiles_dir: Path) -> None:
        super().__init__(message=f"Dotfiles directory already exists at {dotfiles_dir}")
        self.dotfiles_dir = dotfiles_dir
