import typer
import yaml
from rich.console import Console

from dotman.cli.common_func import handle_errors
from dotman.core.config.config import DotmanConfig

config_app = typer.Typer(help="Manage items in the system")

console = Console()


# ==================================================================================
# ------------ Config commands ------------
# ==================================================================================


@config_app.callback(invoke_without_command=True)
@handle_errors
def config_callback(ctx: typer.Context):
    """Config CLI Application."""
    if ctx.invoked_subcommand is None:
        ctx.invoke(show)
    console.print(
        "You can change your config file path via `CONFIG_ENV_VAR environment` variable.",
        "Default is `~/.config/dotman/config.yml`",
    )


@config_app.command(help="View dotman configuration.")
@handle_errors
def show():
    console.print(yaml.dump(DotmanConfig.load().model_dump(mode="json"), default_flow_style=False))


@config_app.command(help="Get a configuration value.")
def get(key: str):
    data = DotmanConfig.load().model_dump(mode="json")
    if key not in data:
        console.print(f"[red]Invalid key: {key}[/]")
        return
    console.print(data[key])


@config_app.command(help="Update dotman configuration.")
@handle_errors
def set(
    key: str | None = typer.Argument(None, help="The key to update."),
    value: str | None = typer.Argument(None, help="The value to update the key with."),
):
    """Update a configuration value."""

    cfg = DotmanConfig.load()

    cfg = cfg.set(key, value)

    cfg.save()

    console.print(f"[green]Updated {key} to {value}[/]")
