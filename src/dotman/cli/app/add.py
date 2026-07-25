import sys
import termios
import tty
from pathlib import Path
from typing import Any

from rich.console import Console

from dotman import Dotman

console = Console()


def get_user_choice() -> bool:
    while True:
        choice = _get_single_key_safe().lower()
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
        char: str | Any = sys.stdin.read(1)

        # Safely handle Ctrl+C (which passes byte \x03 in raw mode)
        if char == "\x03":
            raise KeyboardInterrupt

        return char.lower()
    finally:
        # Guarantee restoration for normal executions
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def add(
    file: Path,
    package_name: str | None,
):
    # Core does not validate CLI argument problems.
    if package_name is None:
        console.print("Package name is required to add a file.", style="red")
        return

    operation = Dotman().add(file, package_name)

    preview = operation.preview()

    for warn in preview.warnings:
        console.print(warn, style="yellow")
        console.print("Do you want to continue? [y/n]: ", style="yellow", end="")
        if not get_user_choice():
            console.print("Operation cancelled by user.", style="red")
            return

    if preview.package_created:
        console.print("Package not found, created new package", style="dim green")
    else:
        console.print("Package exists, reusing it", style="dim green")

    operation.add()
    console.print(operation.tree())

    console.print("Press (y) to commit or (n) to rollback: ", style="yellow", end="")
    try:
        choice = get_user_choice()
    except KeyboardInterrupt:
        choice = False

    if choice:
        operation.commit()
        console.print("Changes committed successfully.", style="green")
    else:
        operation.rollback_changes()
        console.print("Files restored successfully.", style="yellow")
