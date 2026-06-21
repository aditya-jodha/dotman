import sys
import termios
import tty
from pathlib import Path

from rich.console import Console

from dotman.core.add import SymlinkStatus
from dotman.core.service.add_service import AddErrors, AddService

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
    file: Path,
    package_name: str | None,
):
    # Core dose't validate CLI argument problems.
    if package_name is None:
        console.print("Package name is required to add a file.", style="red")
        return
    # Resolve the file path
    resolved_file = file.expanduser()
    if not resolved_file.is_absolute():
        resolved_file = Path.cwd() / resolved_file

    add_service = AddService(
        file=resolved_file,
        package=package_name,
    )
    add_service.load()

    if not add_service.is_dotfile_home_exits:
        # This checks the home directory and dotfiles directory correctly
        return

    match add_service.service_validate():
        case AddErrors.FileNotExists:
            console.print(f"File '{file}' does not exist.", style="red")
            return
        case AddErrors.FileIsSymLink:
            console.print(f"File '{file}' is a symlink.", style="red")
            return
        case AddErrors.NotASubPath:
            console.print(
                f"File '{file}' is not a subpath of '{add_service.home_dir}'.",
                style="red",
            )
            return
        case AddErrors.InvalidPackage:
            console.print(f"Package '{add_service.package}' is invalid.", style="red")
            return
        case AddErrors.TargetIsHome:
            console.print(
                f"Target file `{add_service.file}` is home directory path.", style="Red"
            )
            return
        case AddErrors.TargetIsDotfilesDir:
            console.print(
                f"Target file `{add_service.file}` is dotfiles directory path",
                style="Red",
            )
            return
        case AddErrors.FileNameCollidingError:
            console.print(
                f"File name `{file.name}` exists in dotfiles directory", style="Red"
            )
            return
        case None:
            # None means everything is fine.
            pass

    sym_chech = add_service.validate_directory_symlinks()

    for check in sym_chech:
        if check.status == SymlinkStatus.WARN:
            console.print(check.message, style="yellow")
            console.print("Do you want to continue? [y/n]: ", style="yellow", end="")
            if not get_user_choice():
                console.print("Operation cancelled by user.", style="red")
                return

        elif check.status == SymlinkStatus.ERROR:
            console.print(check.message, style="red")
            return

    if add_service.create_reuse_package():
        console.print(
            f"Package exist transfereing {add_service.add_files.file}",
            style="dim green",
        )
    else:
        console.print("Package not found created new package", style="dim green")
        # As move_file_to_dotfiles can raise FileNotFoundError but as
        # we check above so no need to put try/except block here

    if add_service.service_add_file():
        if add_service.is_dir:
            console.print(
                f"Directory '{add_service.add_files.file}' added to package '{add_service.add_files.package}' successfully.",  # noqa: E501
                style="dim green",
            )

        else:
            console.print(
                f"File '{add_service.add_files.file}' added to package '{add_service.add_files.package}' successfully.",
                style="dim green",
            )
    else:
        console.print("Failed to add file to package.", style="red")
        return

    # Last confirmation before committing the changes, if user wants to restore the files then
    # we will restore the files from the log
    console.print(
        "Please review the changes and if everything looks good then you can commit the changes.",
        style="yellow",
    )
    created_tree = add_service.create_tree()
    console.print(created_tree)

    while True:
        console.print(
            "Press [bold green](y)[/] to commit the changes or [bold red](n)[/] to restore the files: ",
            end="",
        )
        try:
            choice = _get_single_key_safe()
        except KeyboardInterrupt:
            add_service.restore_files()
            return

        if choice == "y":
            add_service.delete_log()
            console.print("Changes committed successfully.", style="green")
            break

        if choice == "n":
            add_service.restore_files()
            console.print("Files restored successfully.", style="yellow")
            if add_service.package_exists:
                # If the package directory is empty after restoring files, we can remove it
                exit_code = add_service.add_files.delete_empty_package()
                if exit_code == 0:
                    console.print(
                        f"Package '{add_service.add_files.package}' was empty after restoring files and has been removed.",  # noqa: E501
                        style="yellow",
                    )
                else:
                    console.print(
                        f"Package '{add_service.add_files.package}' was not empty after restoring files.",
                        style="yellow",
                    )
            break

        console.print("Invalid choice. No action taken.", style="red")
