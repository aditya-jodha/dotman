from pathlib import Path

import typer
from rich.console import Console

from dotman.core.add import sanitize_package_name
from dotman.core.linker import Linker, LinkResult

console = Console()


def iter_package_files(package_dir: Path):
    for path in package_dir.rglob("*"):
        if path.is_file() or path.is_symlink():
            yield path


def sync(dotfiles_dir: Path, home_dir: Path, package_name: str | None, dry_run: bool):
    if not dotfiles_dir.is_dir():
        console.print(f"Dotfiles directory '{dotfiles_dir}' does not exist.", style="red")
        return

    if package_name is None:
        package_dirs = sorted(path for path in dotfiles_dir.iterdir() if path.is_dir())
    else:
        package_dir = dotfiles_dir / sanitize_package_name(package_name)
        if not package_dir.exists() or not package_dir.is_dir():
            console.print(f"Package '{package_name}' does not exist.", style="red")
            return
        package_dirs = [package_dir]

    if not package_dirs:
        console.print("No packages found to sync.", style="yellow")
        return

    linker = Linker(dry_run=dry_run, backup_dir=home_dir / ".dotman_backup")
    results: list[LinkResult] = []

    for package_dir in package_dirs:
        for source in iter_package_files(package_dir):
            target = home_dir / source.relative_to(package_dir)
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
