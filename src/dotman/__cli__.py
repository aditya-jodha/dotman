import sys

import typer
from rich.console import Console

from dotman.cli.app.root import app
from dotman.cli.config.root import config_app
from dotman.cli.profile.root import profile
from dotman.cli.renderer.base import OutputFormat
from dotman.cli.renderer.factory import RuntimeState
from dotman.errors.dotman_error import ExitCode

app.add_typer(config_app, name="config", help="Manage dotman configuration.")
app.add_typer(profile, name="profile", help="Manage profiles.")
console = Console()


@app.callback()
def _(
    output: OutputFormat = typer.Option(  # noqa: B008
        OutputFormat.RICH,
        "--output",
    ),
):
    RuntimeState.configure(output)


def main() -> None:
    try:
        app()
    except KeyboardInterrupt:
        console.print("\n[red]Process interrupted. Exiting safely.[/]")
        sys.exit(ExitCode.KEYBOARD_INTERRUPT)


if __name__ == "__main__":
    main()
