from pathlib import Path

import typer

from dotman.core.config import DOTFILES_DIR, HOME_DIR

app = typer.Typer(help="A CLI tool to manage your dotfiles.", no_args_is_help=True)


@app.command(
    help="Creates dotfile folder and if previous folder exists then makes it as backup then creates new dotfile folder."
)
def init():
    from dotman.cli.app.init import init  # noqa: PLC0415

    init(home_dir=HOME_DIR, dotfiles_dir=DOTFILES_DIR)


@app.command(help="Sync dotfiles package links to the home directory.")
def sync(
    package_name: str | None = typer.Option(
        None, "--package", help="Sync only this package. Syncs all packages by default."
    ),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be linked without changing files."),
):
    from dotman.cli.app.sync import sync  # noqa: PLC0415

    sync(dotfiles_dir=DOTFILES_DIR, home_dir=HOME_DIR, package_name=package_name, dry_run=dry_run)


@app.command(help="Give a full diagnostic report.")
def doctor(detail: bool = typer.Option(False, "-a", "--all", help="Show detailed information.")):
    from dotman.cli.app.doctor import doctor  # noqa: PLC0415

    doctor(home_dir=HOME_DIR, dotfiles_dir=DOTFILES_DIR, detail=detail)


@app.command(help="Add a file to a package.")
def add(
    file: Path,
    package_name: str | None = typer.Option(None, "--package", help="The package name to which the file belongs."),
):
    from dotman.cli.app.add import add  # noqa: PLC0415

    add(dotfiles_dir=DOTFILES_DIR, home_dir=HOME_DIR, file=file, package_name=package_name)
