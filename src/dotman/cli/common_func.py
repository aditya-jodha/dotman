from pathlib import Path

from rich.console import Console

from dotman.core.config import StrPath

console = Console()


def check_file_exists(home_location: Path, dotfiles_location: Path) -> bool:
    """Check if the dotfiles directory and home directory exist."""

    if home_location.exists():
        if not home_location.is_dir():
            console.print(
                f"Home directory '{home_location}' exists but is not a directory.",
                style="red",
            )
            return False
    else:
        console.print(f"Home directory '{home_location}' does not exist.", style="red")
        return False

    if dotfiles_location.exists():
        if not dotfiles_location.is_dir():
            console.print(
                f"Dotfiles directory '{dotfiles_location}' exists but is not a directory.",
                style="red",
            )
            return False
    else:
        console.print(
            f"Dotfiles directory '{dotfiles_location}' does not exist.", style="red"
        )
        return False

    return True


def sanitize_package_name(package: StrPath) -> str:
    """Sanitizes the package name by replacing spaces with underscores and converting to lowercase."""

    return (
        str(package)
        .replace(" ", "_")
        .replace("  ", "_")
        .replace(".", "_")
        .replace("..", "_")
        .replace("/", "_")
        .replace("\\", "_")
        .lower()
        .strip()
    )
