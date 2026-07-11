from collections.abc import Callable
from functools import wraps

import typer
from rich.console import Console

from dotman.cli.renderer.factory import RuntimeState
from dotman.core.config import StrPath
from dotman.errors.dotman_error import DotmanError, ExitCode

console = Console()


def handle_errors[**P, R](func: Callable[P, R]) -> Callable[P, R]:
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        try:
            return func(*args, **kwargs)
        except DotmanError as e:
            pay_load = e.to_payload()
            RuntimeState.renderer.render(pay_load)

            raise typer.Exit(code=pay_load.exit_code) from e
        except KeyboardInterrupt as e:
            console.print(f"[red]Error: {e!s} Operation cancelled by user.[/red]")
            raise typer.Exit(code=ExitCode.KEYBOARD_INTERRUPT) from e

    return wrapper


def sanitize_package_name(package: StrPath) -> str:
    """
    Replace spaces with underscores and convert the name to lowercase.
    """

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
