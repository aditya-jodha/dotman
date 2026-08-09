from dotman.core.config.config import DotmanConfig, InternalFileSystemObject
from dotman.errors.dotman_error import DotmanError
from dotman.plugin.manager import PluginManager


def complete_profiles(incomplete: str) -> list[str]:
    cfg = DotmanConfig.load()
    profiles_dir = cfg.dotfiles_dir / InternalFileSystemObject.PROFILES.value

    if not profiles_dir.exists():
        return []

    return [p.name for p in profiles_dir.iterdir() if p.is_dir() and p.name.startswith(incomplete)]


def complete_plugins(incomplete: str) -> list[str]:
    """Suggest installed plugin manifest names for CLI completion."""
    cfg = DotmanConfig.load()

    if not cfg.plugins_dir.exists():
        return []

    try:
        plugins = PluginManager(cfg.plugins_dir).list_plugins()
    except DotmanError:
        return []

    return sorted(
        plugin.manifest.name for plugin in plugins if plugin.manifest.name.startswith(incomplete)
    )
