from typing import TYPE_CHECKING

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from dotman.core.service.profile_service import ProfileSwitcher, ProfileSwitchResult

console = Console()


def _get_status_style(status: str) -> str:
    """Helper to determine the style color based on the status text."""
    status_lower = status.lower()
    if "success" in status_lower or "done" in status_lower:
        return "green"
    if "fail" in status_lower or "error" in status_lower:
        return "red"
    return "yellow"


def _render_as_table(name: str, result: ProfileSwitchResult) -> Table:
    """Renders the profile action log layout as a Rich Table."""
    table = Table(
        title=f"Profile Action Log ({name})",
        show_header=True,
        header_style="bold magenta",
    )

    table.add_column("Operation", style="bold")
    table.add_column("Source Path", style="blue")
    table.add_column("Target Path", style="magenta")
    table.add_column("Status", justify="center")
    table.add_column("Details", style="italic grey50")

    for unlink in result.unlink_results:
        status_str = getattr(unlink.status, "value", str(unlink.status))
        style = _get_status_style(status_str)
        status_display = f"[{style}]{status_str}[/{style}]"
        details = "Removed Symlink" if unlink.removed else "Not Removed"

        table.add_row("Unlink", str(unlink.source), str(unlink.target), status_display, details)

    for link in result.link_results:
        status_str = link.status or ""
        style = _get_status_style(status_str)
        status_display = f"[{style}]{status_str}[/{style}]"
        details = link.message or (link.action.capitalize() if link.action else "")

        table.add_row("Link", str(link.source), str(link.target), status_display, details)

    return table


def _render_as_panel(name: str, result: ProfileSwitchResult) -> Panel:
    """Renders the profile action log layout as a Rich Panel."""
    log_content = Text()

    for unlink in result.unlink_results:
        status_str = getattr(unlink.status, "value", str(unlink.status))
        style = _get_status_style(status_str)
        details = "Removed Symlink" if unlink.removed else "Not Removed"

        log_content.append("• [Unlink] ", style="bold red")
        log_content.append(f"{unlink.source}", style="blue")
        log_content.append(" ➔ ")
        log_content.append(f"{unlink.target}", style="magenta")
        log_content.append(f" [{status_str.upper()}]", style=style)
        log_content.append(f" ({details})\n", style="italic grey50")

    for link in result.link_results:
        status_str = link.status or ""
        style = _get_status_style(status_str)
        details = link.message or (link.action.capitalize() if link.action else "")

        log_content.append("• [Link]   ", style="bold green")
        log_content.append(f"{link.source}", style="blue")
        log_content.append(" ➔ ")
        log_content.append(f"{link.target}", style="magenta")
        log_content.append(f" [{status_str.upper()}]", style=style)
        log_content.append(f" ({details})\n", style="italic grey50")

    return Panel(
        log_content,
        title=f"[bold magenta]Profile Action Log ({name})[/bold magenta]",
        border_style="bright_blue",
        expand=False,
    )


def use(name: str | None):
    service = ProfileSwitcher()
    if name is None:
        console.print(service.list_profiles())
        return

    result = service.switch_profile(name)

    console.print(f"[bold green]Switched to profile: {result.new_profile}[/bold green]\n")

    if not TYPE_CHECKING:
        # TODO: Not for this update.
        renderable = _render_as_table(name, result)
    else:
        renderable = _render_as_panel(name, result)

    console.print(renderable)
