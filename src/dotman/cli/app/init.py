from rich.console import Console

from dotman.core.service.initializer_service import InitializerService
from dotman.errors.initializer_errors import DotmanDotfilesBackupDirExistsError

console = Console()


def init():
    service = InitializerService()
    profile = console.input("Enter profile name: ")
    try:
        service.setup(profile)
    except DotmanDotfilesBackupDirExistsError as e:
        console.print(e.error)
        return
