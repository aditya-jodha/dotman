# ruff: noqa: B008

from pathlib import Path

import typer

from dotman.cli.common_func import handle_errors
from dotman.core.validator import require_initialized, require_profile

app = typer.Typer(help="A CLI tool to manage your dotfiles.", no_args_is_help=True)


@app.command(
    help=(
        "Creates the dotfiles folder. If one already exists, "
        "it is backed up before creating a new one."
    )
)
@handle_errors
def init():
    from dotman.cli.app.init import init  # noqa: PLC0415

    init()


@app.command(help="Sync dotfiles package links to the home directory.")
@handle_errors
@require_initialized
@require_profile
def sync(
    package_name: str | None = typer.Option(
        None, "--package", help="Sync only this package. Syncs all packages by default."
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show what would be linked without changing files."
    ),
):
    from dotman.cli.app.sync import sync  # noqa: PLC0415

    sync(package_name=package_name, dry_run=dry_run)


@app.command(help="Give a full diagnostic report.")
@handle_errors
@require_initialized
@require_profile
def doctor(
    detail: bool = typer.Option(False, "-a", "--all", help="Show detailed information."),
):
    from dotman.cli.app.doctor import doctor  # noqa: PLC0415

    doctor(detail=detail)


@app.command(help="Add a file to a package.")
@handle_errors
@require_initialized
@require_profile
def add(
    file: Path = typer.Argument(..., help="The file to be added."),
    package_name: str | None = typer.Option(
        None, "--package", help="The package name to which the file belongs."
    ),
):
    from dotman.cli.app.add import add  # noqa: PLC0415

    add(file=file, package_name=package_name)


@app.command(help="Remove a file from a package.")
@handle_errors
@require_initialized
@require_profile
def remove(
    file: Path | None = typer.Argument(
        None,
        help="The file to be removed.",
    ),
):
    from dotman.cli.app.remove import remove  # noqa: PLC0415

    remove(file=file)
