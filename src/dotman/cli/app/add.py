import sys
import termios
import tty
from pathlib import Path

from rich.console import Console

from dotman.cli.tree_builder import print_beautiful_directory
from dotman.core.add import AddFiles, LogBook, SymlinkStatus
from dotman.core.config import InternalFileSystemObject

console = Console()


def get_user_choice() -> bool:
    while True:
        choice = _get_single_key_safe()
        if choice == "y":
            return True
        if choice == "n":
            return False
        console.print("Invalid choice. Please enter 'y' or 'n'.", style="red")


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


def add(
    home_dir: Path,
    dotfiles_dir: Path,
    file: Path,
    package_name: str | None,
):
    if package_name is None:
        console.print("Package name is required to add a file.", style="red")
        return
    if package_name == InternalFileSystemObject.PACKAGES.value:
        console.print("You cannot add a file to the 'packages' package.", style="red")
        console.print("This directory is reserved for `dotman` internal use.", style="red")
        return

    log_book = LogBook()

    addfile = AddFiles(
        home_dir=home_dir,
        dotfiles_dir=dotfiles_dir,
        file=file,
        package=package_name,
        logbook=log_book,
    )

    sym_chech = addfile.scan_symlinks()

    for check in sym_chech:
        if check.status == SymlinkStatus.WARN.value:
            console.print(check.message, style="yellow")
            console.print("Do you want to continue? [y/n]: ", style="yellow", end="")
            if not get_user_choice():
                console.print("Operation cancelled by user.", style="red")
                return

        elif check.status == SymlinkStatus.ERROR.value:
            console.print(check.message, style="red")
            return

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
    created_tree = print_beautiful_directory(str(dotfiles_dir))
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
