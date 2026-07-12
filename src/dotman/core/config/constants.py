from pathlib import Path

DEFAULT_HOME_DIR = Path.home()
DEFAULT_DOTFILES_DIR = DEFAULT_HOME_DIR / ".dotfiles"

DEFAULT_CONFIG_PATH = Path.home() / ".config/dotman/config.yml"
CONFIG_ENV_VAR = "DOTMAN_CONFIG"


DOTMAN_BACKUP_DIR = ".dotman_backup"
