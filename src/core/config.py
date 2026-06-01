from dataclasses import dataclass
from pathlib import Path
from secrets import randbelow

# HOME_DIR = Path.home()
# DOTFILES_DIR = HOME_DIR / "dotfiles"

HOME_DIR = Path("/tmp/dotman-lab/home")  # noqa: S108
DOTFILES_DIR = Path("/tmp/dotman-lab/dotfiles")  # noqa: S108

TEMP_LOG_FILE = DOTFILES_DIR / f"temp_logbook_{randbelow(9000) + 1000}.toml"


@dataclass
class LogBookData:
    original_path: Path
    new_path: Path


type StrPath = str | Path
