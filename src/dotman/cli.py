import sys
import termios
import tty
from pathlib import Path

import typer
from rich.console import Console

from core.config import DOTFILES_DIR, HOME_DIR
from dotman.add import AddFiles, LogBook
from dotman.tree_builder import print_beautiful_directory

from .initializer import Initializer

app = typer.Typer(help="A CLI tool to manage your dotfiles.", no_args_is_help=True)

console = Console()


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
        console.print(
            "Backup already exists. Please restore it before initializing again.", style="red"
        )
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


@app.command(help="add a file to the dotfiles directory.")
def add(
    file: Path,
    package_name: str | None = typer.Option(
        None, "--package", help="The package name to which the file belongs."
    ),
):
    if package_name is None:
        console.print("Package name is required to add a file.", style="red")
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

    if addfile.package_exists:
        console.print(
            f"Package '{addfile.package}' already exists. Adding file to the package...",
            style="green",
        )
    else:
        console.print(
            f"Package '{addfile.package}' does not exist. Creating package...", style="dim yellow"
        )

        addfile.create_package()
        console.print(f"Package '{addfile.package}' created successfully.", style="dim green")

    if addfile.is_dir:
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

    console.print(
        "Please review the changes and if everything looks good then you can commit the changes.",
        style="yellow",
    )
    created_tree = print_beautiful_directory(str(DOTFILES_DIR))
    console.print(created_tree)

    # Last confirmation before committing the changes, if user wants to restore the files then
    # we will restore the files from the log
    while True:
        console.print(
            "Press [bold green](y)[/] to commit the changes or [bold red](n)[/] to restore the files: ",  # noqa: E501
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
            if addfile.package_exists and not addfile.has_files_in_package():
                # If the package directory is empty after restoring files, we can remove it
                (DOTFILES_DIR / addfile.package).rmdir()
                console.print(
                    f"Package '{addfile.package}' was empty after restoring files and has been removed.",  # noqa: E501
                    style="yellow",
                )
            break

        console.print("Invalid choice. No action taken.", style="red")


@app.command(help="stow the files to the home directory.")
def stow():
    console.print("Stow command is not implemented yet.", style="yellow")


if __name__ == "__main__":
    try:
        app()
    except KeyboardInterrupt:
        console.print("\n[red]Process interrupted. Exiting safely.[/]")
        sys.exit(0)
