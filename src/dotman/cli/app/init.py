from rich.console import Console

from dotman.core.service.initializer_service import InitializerService

console = Console()


def init():
    service = InitializerService()
    profile = console.input("Enter profile name: ")

    service.setup(profile)
