from pathlib import Path

import typer
import yaml
from rich.console import Console

from dotman.core.config import DotmanConfig, load_config, save_config

config_app = typer.Typer(help="Manage items in the system")

console = Console()


# ==================================================================================
# ------------ Config commands ------------
# ==================================================================================


@config_app.callback(invoke_without_command=True)
def config_callback(ctx: typer.Context):
    """Config CLI Application."""
    if ctx.invoked_subcommand is None:
        ctx.invoke(show)
    console.print(
        "You can change your config file path via `CONFIG_ENV_VAR environment` variable.",
        "Default is `~/.config/dotman/config.yml`",
    )


@config_app.command(help="View dotman configuration.")
def show():
    console.print(yaml.dump(load_config().as_dict(), default_flow_style=False))
    console.print(
        "You can change your config file path via `CONFIG_ENV_VAR environment` variable.",
        "Default is `~/.config/dotman/config.yml`",
    )


@config_app.command(help="Get a configuration value.")
def get(key: str):
    data = load_config().as_dict()
    if key not in data:
        console.print(f"[red]Invalid key: {key}[/]")
        return
    console.print(data[key])


@config_app.command(help="Update dotman configuration.")
def set(
    key: str | None = typer.Argument(None, help="The key to update."),
    value: str | None = typer.Argument(None, help="The value to update the key with."),
):
    """Update a configuration value."""

    if key is None or value is None:
        console.print("[red]Missing key or value.[/]")
        return
    data = load_config().as_dict()
    if key not in data:
        console.print(f"[red]Invalid key: {key}[/]")
        return
    data[key] = value
    save_config(
        DotmanConfig(
            dotfiles_dir=Path(data["dotfiles_dir"]),
            home_dir=Path(data["home_dir"]),
        )
    )
    console.print(f"[green]Updated {key} to {value}[/]")
