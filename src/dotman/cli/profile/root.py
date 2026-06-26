import typer
from rich.console import Console

from dotman.core.service.profile_service import ProfileSwitcher
from dotman.errors.profile_errors import (
    DirNotEmptyError,
    ProfileAlreadyExistsError,
    ProfileMetaDataFileCorruptedError,
    ProfileNotFoundError,
)

profile = typer.Typer(help="Manage profiles")

console = Console()


@profile.command()
def use(name: str | None = typer.Argument(None, help="Name of the profile to use")):
    from .use import use  # noqa: PLC0415

    use(name)


@profile.command(help="Create a new profile")
def create(
    name: str | None = typer.Argument(None, help="Name of the profile to create"),
):
    service = ProfileSwitcher()
    if name is None:
        console.print("Profile name is required")
        return

    try:
        service.create_profile(name)
    except ProfileAlreadyExistsError as e:
        console.print(e.error, style="red")
        return
    else:
        console.print(f"[bold green]Created profile: {name}[/bold green]\n")


@profile.command(help="Delete a profile")
def delete(
    name: str | None = typer.Argument(None, help="Name of the profile to delete"),
):
    service = ProfileSwitcher()
    if name is None:
        console.print("Profile name is required")
        return
    try:
        service.delete_profile(name)
    except ProfileNotFoundError as e:
        console.print(e.error, style="red")
        return
    except ProfileMetaDataFileCorruptedError as e:
        console.print(e.error, style="red")
        return
    except DirNotEmptyError as e:
        console.print(e.error, style="red")
        return
    else:
        console.print(f"[bold green]Deleted profile: {name}[/bold green]\n")


@profile.command(help="List all profiles")
def list(name: str | None = typer.Argument(None, help="Name of the profile to list")):
    service = ProfileSwitcher()
    if name is None:
        console.print(service.list_profiles())
        return

    console.print(service.list_profiles())
