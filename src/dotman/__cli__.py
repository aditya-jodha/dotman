import typer
from rich.console import Console

from dotman.api import Application
from dotman.cli.app.root import app
from dotman.cli.config.root import config_app
from dotman.cli.plugin.root import plugin_app
from dotman.cli.profile.root import profile
from dotman.cli.renderer.base import OutputFormat
from dotman.cli.renderer.factory import RuntimeState
from dotman.context import AppContext
from dotman.core.config.config import DotmanConfig
from dotman.core.get_internal_data import DotmanMetadata
from dotman.errors.dotman_error import ExitCode
from dotman.plugin import PluginManager
from dotman.plugin.installer import PluginInstaller

app.add_typer(config_app, name="config", help="Manage dotman configuration.")
app.add_typer(profile, name="profile", help="Manage profiles.")
app.add_typer(plugin_app, name="plugin", help="Manage plugins.")

console = Console()


def load_context() -> AppContext:
    config = DotmanConfig.load()

    manager = PluginManager(
        plugins_dir=config.plugins_dir,
        installer=PluginInstaller(),
    )

    registry = manager.load_plugins(app)

    return AppContext(
        validation_registry=registry,
        config=config,
        metadata=DotmanMetadata.load(),
    )


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
        Application.configure(load_context())
        app()
    except KeyboardInterrupt as e:
        console.print("\n[red]Process interrupted. Exiting safely.[/]")
        raise typer.Exit(ExitCode.KEYBOARD_INTERRUPT) from e


if __name__ == "__main__":
    main()
