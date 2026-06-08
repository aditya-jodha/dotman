import typer
import yaml
from rich.console import Console
from rich.table import Table

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
    service = ProfileSwitcher()
    if name is None:
        console.print(service.list_profiles())
        return

    try:
        result = service.switch_profile(name)
    except ProfileNotFoundError as e:
        console.print(e.error, style="red")
        return
    except ProfileMetaDataFileCorruptedError as e:
        console.print(e.error, style="red")
        return
    except OSError as e:
        console.print(str(e), style="red")
        return
    except yaml.YAMLError as e:
        console.print(str(e), style="red")
        return

    else:
        console.print(f"[bold green]Switched to profile: {result.new_profile}[/bold green]\n")

        table = Table(title=f"Profile Action Log ({name})", show_header=True, header_style="bold magenta")

        table.add_column("Operation", style="bold")
        table.add_column("Source Path", style="blue")
        table.add_column("Target Path", style="magenta")
        table.add_column("Status", justify="center")
        # FIX: Changed 'italic gray' to 'italic grey' (Rich uses standard web color naming)
        table.add_column("Details", style="italic grey50")

        # 2. Process Unlink Results
        for unlink in result.unlink_results:
            status_str = getattr(unlink.status, "value", str(unlink.status))
            status_lower = status_str.lower()

            if "success" in status_lower or "done" in status_lower:
                status_display = f"[green]{status_str}[/green]"
            elif "fail" in status_lower or "error" in status_lower:
                status_display = f"[red]{status_str}[/red]"
            else:
                status_display = f"[yellow]{status_str}[/yellow]"

            details = "Removed Symlink" if unlink.removed else "Not Removed"

            table.add_row("Unlink", str(unlink.source), str(unlink.target), status_display, details)

        # 3. Process Link Results
        for link in result.link_results:
            status_lower = link.status.lower() if link.status else ""

            if "success" in status_lower or "done" in status_lower:
                status_display = f"[green]{link.status}[/green]"
            elif "fail" in status_lower or "error" in status_lower:
                status_display = f"[red]{link.status}[/red]"
            else:
                status_display = f"[yellow]{link.status}[/yellow]"

            details = link.message or (link.action.capitalize() if link.action else "")

            table.add_row("Link", str(link.source), str(link.target), status_display, details)

        console.print(table)


@profile.command(help="Create a new profile")
def create(name: str | None = typer.Argument(None, help="Name of the profile to create")):
    service = ProfileSwitcher()
    if name is None:
        console.print("Profile name is required")
        return

    try:
        service.create_profile(name)
    except ProfileAlreadyExistsError as e:
        console.print(e.error, style="red")
        return


@profile.command(help="Delete a profile")
def delete(name: str | None = typer.Argument(None, help="Name of the profile to delete")):
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


@profile.command(help="List all profiles")
def list(name: str | None = typer.Argument(None, help="Name of the profile to list")):
    service = ProfileSwitcher()
    if name is None:
        console.print(service.list_profiles())
        return

    console.print(service.list_profiles())
