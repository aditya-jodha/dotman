import typer
from rich.console import Console

from dotman.cli.common_func import handle_errors
from dotman.cli.completion import complete_profiles
from dotman.core.service.profile_service import ProfileSwitcher
from dotman.core.validator import require_initialized, require_profile

profile = typer.Typer(help="Manage profiles")

console = Console()


@profile.command()
@handle_errors
@require_initialized
@require_profile
def use(
    name: str | None = typer.Argument(
        None,
        help="Name of the profile to use",
        autocompletion=complete_profiles,
    ),
):
    from .use import use  # noqa: PLC0415

    use(name)


@profile.command(help="Create a new profile")
@handle_errors
@require_initialized
def create(
    name: str | None = typer.Argument(
        None,
        help="Name of the profile to create",
    ),
):
    service = ProfileSwitcher()
    if name is None:
        console.print("Profile name is required")
        return

    service.create_profile(name)
    console.print(f"[bold green]Created profile: {name}[/bold green]\n")


@profile.command(help="Delete a profile")
@handle_errors
@require_initialized
def delete(
    name: str | None = typer.Argument(
        None,
        help="Name of the profile to delete",
        autocompletion=complete_profiles,
    ),
):
    service = ProfileSwitcher()
    if name is None:
        console.print("Profile name is required")
        return

    service.delete_profile(name)
    console.print(f"[bold green]Deleted profile: {name}[/bold green]\n")


@profile.command(help="List all profiles")
@handle_errors
@require_initialized
def ls():
    service = ProfileSwitcher()
    profiles = service.list_profiles()
    if not profiles:
        console.print("[bold green]No profiles found.[/bold green]")
        return

    console.print("[bold green]Profile list:[/bold green]")
    for profile in profiles:
        console.print(f"\t- [bold green]{profile}[/bold green]")
