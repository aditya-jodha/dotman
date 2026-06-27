from collections.abc import Callable
from functools import wraps

import typer
from rich.console import Console

from dotman.core.config import ExitCode, StrPath
from dotman.errors.dotman_error import DotmanError

console = Console()


def handle_errors[**P, R](func: Callable[P, R]) -> Callable[P, R]:
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        try:
            return func(*args, **kwargs)
        except DotmanError as e:
            console.print(f"[red]{e.message}[/red]")
            raise typer.Exit(code=ExitCode.DOTFILES_FAILURE) from e
        except KeyboardInterrupt as e:
            console.print(f"[red]Error: {str(e)} Operation cancelled by user.[/red]")
            raise typer.Exit(code=ExitCode.KEYBOARD_INTERRUPT) from e

    return wrapper


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
