from pathlib import Path

from rich.console import Console

from dotman.core.service.remove_service import RemoveService, RemoveStatus

console = Console()


def remove(file: Path | None):
    if file is None:
        console.print("Please provide either a file or a package name.", style="red")
        return

    service = RemoveService()

    match service.remove_file(file):
        case RemoveStatus.OK as e:
            console.print(e.message, style="green")
        case _ as e:
            console.print(e.message, style="red")
            return
