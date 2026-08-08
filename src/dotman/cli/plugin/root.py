import typer

from dotman.cli.common_func import handle_errors
from dotman.core.config.config import DotmanConfig
from dotman.plugin.installer import PluginInstaller
from dotman.plugin.manager import PluginManager

plugin_app = typer.Typer()


@plugin_app.command()
@handle_errors
def install(source: str) -> None:
    cgf = DotmanConfig.load()
    manager = PluginManager(
        plugins_dir=cgf.plugins_dir,
        installer=PluginInstaller(),
    )
    manager.install(source)


@plugin_app.command()
@handle_errors
def uninstall(name: str) -> None:
    """Uninstall a plugin by the name in its plugin.toml manifest."""
    cgf = DotmanConfig.load()
    manager = PluginManager(
        plugins_dir=cgf.plugins_dir,
        installer=PluginInstaller(),
    )
    manager.uninstall(name)
