import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Literal
from uuid import uuid4

import yaml

type SUCCESSOR = Literal[0, 1]
type StrPath = str | Path
type HomeDir = Path
type DotfilesDir = Path

DEFAULT_HOME_DIR = Path.home()
DEFAULT_DOTFILES_DIR = DEFAULT_HOME_DIR / ".dotfiles"

DEFAULT_CONFIG_PATH = Path.home() / ".config/dotman/config.yml"
CONFIG_ENV_VAR = "DOTMAN_CONFIG"


class UserDefinedConfig(Enum):
    """Configuration keys that may be overridden by the user."""

    DOTFILES_DIR = "dotfiles_dir"
    HOME_DIR = "home_dir"

    @classmethod
    def values(cls) -> set[str]:
        return {item.value for item in cls}


@dataclass(frozen=True, slots=True)
class DotmanConfig:
    dotfiles_dir: Path
    home_dir: Path

    def as_dict(self) -> dict[str, str]:
        return {
            "dotfiles_dir": str(self.dotfiles_dir),
            "home_dir": str(self.home_dir),
        }


class InternalFileSystemObject(Enum):
    PACKAGES = "packages"
    METADATA = "metadata.yml"
    PROFILES = "profiles"
    LOGBOOK = "logbook"
    TMP_ = "tmp"

    @classmethod
    def values(cls) -> set[str]:
        return {obj.value for obj in cls}


@dataclass
class LogBookData:
    original_path: Path
    new_path: Path


def get_temp_log_file(config_obj: DotmanConfig) -> Path:
    return (
        config_obj.dotfiles_dir
        / InternalFileSystemObject.LOGBOOK.value
        / InternalFileSystemObject.TMP_.value
        / f"dotman_{uuid4()}.log"
    )


def get_config_path() -> Path:
    """Get the path to the config file."""
    return Path(os.getenv(CONFIG_ENV_VAR, DEFAULT_CONFIG_PATH)).expanduser()


def load_config(path: Path | None = None) -> DotmanConfig:
    """Load the config from a file.\n
    _The dotfiles_dir and home_dir values are already ***expanded***._"""

    config_path = path or get_config_path()

    if not config_path.exists():
        return DotmanConfig(
            dotfiles_dir=DEFAULT_DOTFILES_DIR,
            home_dir=DEFAULT_HOME_DIR,
        )

    with config_path.open("r", encoding="utf-8") as f:
        data: dict[str, str] = yaml.safe_load(f) or {}

    # SAFE validation (important)
    for key in UserDefinedConfig.values():
        if key not in data:
            raise ValueError(f"Missing config key: {key}")  # noqa: TRY003

    return DotmanConfig(
        dotfiles_dir=Path(data[UserDefinedConfig.DOTFILES_DIR.value]).expanduser(),
        home_dir=Path(data[UserDefinedConfig.HOME_DIR.value]).expanduser(),
    )


def save_config(cfg: DotmanConfig, path: Path | None = None) -> None:
    """Save the config to a file."""

    config_path = path or get_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)

    with config_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(cfg.as_dict(), f)
