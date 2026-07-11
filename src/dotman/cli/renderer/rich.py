from rich.console import Console
from rich.panel import Panel

from dotman.errors.dotman_error import ErrorPayload

from .base import OutputRenderer


class RichRenderer(OutputRenderer):
    """Human-friendly high-fidelity terminal UI."""

    def __init__(self):
        self.console: Console = Console(stderr=True)

    def render(self, payload: ErrorPayload) -> None:
        self.console.print(
            Panel(
                f"[bold white]{payload.message}[/bold white]",
                title=f"[bold red]✖ {payload.category} Error[/bold red]",
                title_align="left",
                border_style="red",
                subtitle=f"[dim]Exit Code: {payload.exit_code}[/dim]",
                subtitle_align="right",
            )
        )
