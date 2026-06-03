import sys
import termios
import tty
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from dotman.core.add import AddFiles, LogBook
from dotman.core.add import sanitize_package_name as _sanitize_package_name
from dotman.core.config import DOTFILES_DIR, HOME_DIR
from dotman.core.doctor import Doctor, DoctorStatus
from dotman.core.initializer import DotmanPackages, Initializer
from dotman.core.linker import Linker
from dotman.tree_builder import print_beautiful_directory

app = typer.Typer(help="A CLI tool to manage your dotfiles.", no_args_is_help=True)

console = Console()


def _iter_package_files(package_dir: Path):
    for path in package_dir.rglob("*"):
        if path.is_file() or path.is_symlink():
            yield path


def _get_single_key_safe() -> str:
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        char = sys.stdin.read(1)

        # Safely handle Ctrl+C (which passes byte \x03 in raw mode)
        if char == "\x03":
            raise KeyboardInterrupt  # noqa: TRY301

        return char.lower()

    except KeyboardInterrupt:
        # Explicitly restore settings before exiting on Ctrl+C
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        print("\nOperation cancelled by user.")
        sys.exit(0)

    finally:
        # Guarantee restoration for normal executions
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


@app.command(
    help="""Creates dotfile folder and if previous folder exists then makes it as backup then
    creates new dotfile folder."""
)
def init():
    initializer = Initializer(home_dir=DOTFILES_DIR.parent, dotfiles_dir=DOTFILES_DIR)

    if initializer.is_backup_exist:
        console.print("Backup already exists. Please restore it before initializing again.", style="red")
        return

    if initializer.is_old_dotfiles_exist:
        console.print("Existing dotfiles directory found. Creating backup...", style="yellow")
        initializer.convert_to_backup()
        console.print("Backup created successfully.", style="green")
    else:
        console.print("No existing dotfiles directory found. Creating new one...", style="yellow")
        initializer.make_dir()
        console.print("New dotfiles directory created successfully.", style="green")

    initializer.setup()
    console.print("Dotfiles directory setup completed.", style="green")


@app.command(help="Add a file to the dotfiles directory.")
def add(
    file: Path,
    package_name: str | None = typer.Option(None, "--package", help="The package name to which the file belongs."),
):
    if package_name is None:
        console.print("Package name is required to add a file.", style="red")
        return
    if package_name == DotmanPackages.PACKAGES.value:
        console.print("You cannot add a file to the 'packages' package.", style="red")
        console.print("This directory is reserved for `dotman` internal use.", style="red")
        return

    log_book = LogBook()

    addfile = AddFiles(
        home_dir=HOME_DIR,
        dotfiles_dir=DOTFILES_DIR,
        file=file,
        package=package_name,
        logbook=log_book,
    )

    log_book.create_log()

    if not addfile.file.exists():
        console.print(f"File '{addfile.file}' not found.", style="red")
        return

    if addfile.package_exists:
        console.print(
            f"Package '{addfile.package}' already exists. Adding file to the package...",
            style="green",
        )
    else:
        console.print(f"Package '{addfile.package}' does not exist. Creating package...", style="dim yellow")

        addfile.create_package()
        console.print(f"Package '{addfile.package}' created successfully.", style="dim green")

    if addfile.is_dir:
        # As move_dir_to_dotfiles & move_file_to_dotfiles can raise FileNotFoundError but as
        # we check above so no need to put try/except block here

        addfile.move_dir_to_dotfiles()
        console.print(
            f"Directory '{addfile.file}' added to package '{addfile.package}' successfully.",
            style="dim green",
        )

    else:
        addfile.move_file_to_dotfiles()
        console.print(
            f"File '{addfile.file}' added to package '{addfile.package}' successfully.",
            style="dim green",
        )

    # Last confirmation before committing the changes, if user wants to restore the files then
    # we will restore the files from the log
    console.print(
        "Please review the changes and if everything looks good then you can commit the changes.",
        style="yellow",
    )
    created_tree = print_beautiful_directory(str(DOTFILES_DIR))
    console.print(created_tree)

    while True:
        console.print(
            "Press [bold green](y)[/] to commit the changes or [bold red](n)[/] to restore the files: ",
            end="",
        )
        choice = _get_single_key_safe()

        if choice == "y":
            log_book.clear_log()
            console.print("Changes committed successfully.", style="green")
            break

        if choice == "n":
            log_book.restore_files()
            console.print("Files restored successfully.", style="yellow")
            if addfile.package_exists:
                # If the package directory is empty after restoring files, we can remove it
                exit_code = addfile.delete_empty_package()
                if exit_code == 0:
                    console.print(
                        f"Package '{addfile.package}' was empty after restoring files and has been removed.",
                        style="yellow",
                    )
                else:
                    console.print(
                        f"Package '{addfile.package}' was not empty after restoring files.",
                        style="yellow",
                    )
            break

        console.print("Invalid choice. No action taken.", style="red")


@app.command(help="Sync dotfiles package links to the home directory.")
def sync(
    package_name: str | None = typer.Option(
        None, "--package", help="Sync only this package. Syncs all packages by default."
    ),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be linked without changing files."),
):
    if not DOTFILES_DIR.exists():
        console.print(f"Dotfiles directory '{DOTFILES_DIR}' does not exist.", style="red")
        return

    if package_name is None:
        package_dirs = sorted(path for path in DOTFILES_DIR.iterdir() if path.is_dir())
    else:
        package_dir = DOTFILES_DIR / _sanitize_package_name(package_name)
        if not package_dir.exists() or not package_dir.is_dir():
            console.print(f"Package '{package_name}' does not exist.", style="red")
            return
        package_dirs = [package_dir]

    if not package_dirs:
        console.print("No packages found to sync.", style="yellow")
        return

    linker = Linker(dry_run=dry_run, backup_dir=HOME_DIR / ".dotman_backup")
    results = []

    for package_dir in package_dirs:
        for source in _iter_package_files(package_dir):
            target = HOME_DIR / source.relative_to(package_dir)
            results.append(linker.execute(source, target))

    if not results:
        console.print("No files found to sync.", style="yellow")
        return

    for result in results:
        style = "green"
        if result.status == "error":
            style = "red"
        elif result.status == "dry-run":
            style = "cyan"
        elif result.action in {"backup_and_link", "fix"}:
            style = "yellow"

        console.print(
            f"{result.status}: {result.target} -> {result.source} ({result.action})",
            style=style,
        )

    error_count = sum(result.status == "error" for result in results)
    if error_count:
        console.print(f"Sync completed with {error_count} error(s).", style="red")
        raise typer.Exit(code=1)

    console.print(f"Synced {len(results)} file(s).", style="green")


@app.command(help="Give a full diagnostic report.")
def doctor(detail: bool = typer.Option(False, "-a", "--all", help="Show detailed information.")):
    doctor = Doctor(home_dir=HOME_DIR, dotfile_dir=DOTFILES_DIR, detail=detail)
    table = Table(title="System Doctor Status Report", show_lines=True)

    table.add_column("Check Name", justify="left", style="cyan", no_wrap=True)
    table.add_column("Status", justify="center", no_wrap=True)
    table.add_column("Message", justify="left", style="white")

    checks = doctor.run_all()
    for check in checks:
        if check.status == DoctorStatus.OK:
            status_style = f"[bold green]{check.status}[/bold green]"
        elif check.status == DoctorStatus.WARN:
            status_style = f"[bold yellow]{check.status}[/bold yellow]"
        else:
            status_style = f"[bold red]{check.status}[/bold red]"
        table.add_row(check.name, status_style, check.message)

    console.print(table)


def dump():
    pass


if __name__ == "__main__":
    try:
        app()
    except KeyboardInterrupt:
        console.print("\n[red]Process interrupted. Exiting safely.[/]")
        sys.exit(0)
