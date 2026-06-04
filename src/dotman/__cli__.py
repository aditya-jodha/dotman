import sys

from rich.console import Console

from dotman.cli.app.main import app
from dotman.cli.config.main import config_app

app.add_typer(config_app, name="config", help="Manage dotman configuration.")

console = Console()


if __name__ == "__main__":
    try:
        app()
    except KeyboardInterrupt:
        console.print("\n[red]Process interrupted. Exiting safely.[/]")
        sys.exit(0)
