from pathlib import Path
from typing import Final

DEFAULT_HOME_DIR: Final[Path] = Path.home()
DEFAULT_DOTFILES_DIR: Final[Path] = DEFAULT_HOME_DIR / ".dotfiles"
DEFAULT_PLUGINS_DIR: Final[Path] = DEFAULT_HOME_DIR / ".config/dotman/plugins/"

DEFAULT_CONFIG_PATH: Final[Path] = Path.home() / ".config/dotman/config.yml"
CONFIG_ENV_VAR: Final = "DOTMAN_CONFIG"


DOTMAN_BACKUP_DIR: Final = ".dotman_backup"


# =============================================================================
# Plugins
# =============================================================================

# Keys matching the top-level [table] headers in the manifest TOML file
DOTMAN: Final = "dotman"
PLUGIN: Final = "plugin"
