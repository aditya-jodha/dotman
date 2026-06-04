from pathlib import Path

from rich.console import Console

from dotman.core.initializer import Initializer

console = Console()


def init(home_dir: Path, dotfiles_dir: Path):
    initializer = Initializer(home_dir=home_dir, dotfiles_dir=dotfiles_dir)

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
