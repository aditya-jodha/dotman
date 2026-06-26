from typing import TYPE_CHECKING

import typer
from rich.console import Console

from dotman.core.config import ExitCode
from dotman.core.service.sync_service import SyncService

if TYPE_CHECKING:
    from dotman.core.linker import LinkResult

console = Console()


def sync(package_name: str | None, dry_run: bool):
    service = SyncService(dry_run=dry_run)

    service.load()

    service.initilize_package(package=package_name)

    results: list[LinkResult] = service.execute()

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
        raise typer.Exit(code=ExitCode.INVALID_ARGUMENTS)

    console.print(f"Synced {len(results)} file(s).", style="green")
