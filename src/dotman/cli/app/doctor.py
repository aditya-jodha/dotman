from rich.console import Console
from rich.progress import Progress
from rich.table import Table

from dotman import Dotman
from dotman.core.doctor import DoctorStatus, SummeryReport

console = Console()


# This is the main connector for the doctor command
def doctor(detail: bool):
    table = Table(title="System Doctor Status Report", show_lines=True)

    table.add_column("Check Name", justify="left", style="cyan", no_wrap=True)
    table.add_column("Status", justify="center", no_wrap=True)
    table.add_column("Message", justify="left", style="white")

    checks, report = Dotman().doctor(detail=detail)

    for check in checks:
        if check.status == DoctorStatus.OK:
            status_style = f"[bold green]{check.status.value}[/bold green]"
        elif check.status == DoctorStatus.WARN:
            status_style = f"[bold yellow]{check.status.value}[/bold yellow]"
        else:
            status_style = f"[bold red]{check.status}[/bold red]"
        table.add_row(check.name, status_style, check.message)

    console.print(table)

    show_summary(report)


def show_summary(report: SummeryReport):
    total = report.ok + report.warn + report.error
    with Progress() as progress:
        task = progress.add_task("[cyan]Doctor Summary...", total=total)

        # Advance for OK
        progress.update(task, advance=report.ok)
        # Advance for WARN
        progress.update(task, advance=report.warn)
        # Advance for ERROR
        progress.update(task, advance=report.error)

    console.print(
        f"[green]OK: {report.ok}[/] |",
        f"[yellow]WARN: {report.warn}[/] |",
        f"[red]ERROR: {report.error}[/]",
    )
