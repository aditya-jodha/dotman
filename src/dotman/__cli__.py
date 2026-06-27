import sys

from rich.console import Console

from dotman.cli.app.root import app
from dotman.cli.config.root import config_app
from dotman.cli.profile.root import profile
from dotman.core.config import ExitCode

app.add_typer(config_app, name="config", help="Manage dotman configuration.")
app.add_typer(profile, name="profile", help="Manage profiles.")
console = Console()


def main() -> None:
    try:
        app()
    except KeyboardInterrupt:
        console.print("\n[red]Process interrupted. Exiting safely.[/]")
        sys.exit(ExitCode.SUCCESS)


if __name__ == "__main__":
    main()
