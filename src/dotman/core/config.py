import os
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from secrets import randbelow
from typing import Any

import yaml

DEFAULT_DOTFILES_DIR = Path("/tmp/dotman-lab/dotfiles")  # noqa: S108
DEFAULT_HOME_DIR = Path("/tmp/dotman-lab/home")  # noqa: S108
DEFAULT_CONFIG_PATH = Path.home() / ".config/dotman/config.yml"
CONFIG_ENV_VAR = "DOTMAN_CONFIG"


@dataclass(frozen=True)
class DotmanConfig:
    dotfiles_dir: str
    home_dir: str

    @classmethod
    def defaults(cls) -> "DotmanConfig":
        return cls(
            dotfiles_dir=str(DEFAULT_DOTFILES_DIR),
            home_dir=str(DEFAULT_HOME_DIR),
        )

    @property
    def dotfiles_path(self) -> Path:
        return Path(self.dotfiles_dir).expanduser()

    @property
    def home_path(self) -> Path:
        return Path(self.home_dir).expanduser()

    def as_dict(self) -> dict[str, str]:
        return asdict(self)


ConfigDataClass = DotmanConfig


def get_config_path() -> Path:
    return Path(os.getenv(CONFIG_ENV_VAR, DEFAULT_CONFIG_PATH)).expanduser()


def _parse_config_data(data: Any) -> DotmanConfig:
    if data is None:
        raise ValueError("Config file is empty.")  # noqa: TRY003
    if not isinstance(data, dict):
        raise ValueError("Config file must contain a YAML mapping.")  # noqa: TRY003, TRY004

    try:
        return DotmanConfig(
            dotfiles_dir=str(data["dotfiles_dir"]),
            home_dir=str(data["home_dir"]),
        )
    except KeyError as e:
        raise ValueError(f"Missing config key: {e.args[0]}") from e  # noqa: TRY003


def load_config(config_path: Path | None = None) -> DotmanConfig:
    path = config_path or CONFIG_PATH
    if not path.exists():
        return DotmanConfig.defaults()

    try:
        with path.open("r") as f:
            return _parse_config_data(yaml.safe_load(f))
    except yaml.YAMLError as e:
        raise ValueError(f"Error loading YAML config: {e!s}") from e  # noqa: TRY003


def save_config(config_data: DotmanConfig, config_path: Path | None = None) -> None:
    path = config_path or CONFIG_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        yaml.safe_dump(config_data.as_dict(), f)


def make_temp_log_file(dotfiles_dir: Path) -> Path:
    return dotfiles_dir / f"temp_logbook_{randbelow(9000) + 1000}.toml"


class InternalFileSystemObject(Enum):
    PACKAGES = "packages"
    METADATA = "metadata.json"

    @classmethod
    def values(cls):
        return {obj.value for obj in cls}


@dataclass
class LogBookData:
    original_path: Path
    new_path: Path


CONFIG_PATH = get_config_path()
config = load_config(CONFIG_PATH)

HOME_DIR = config.home_path
DOTFILES_DIR = config.dotfiles_path
TEMP_LOG_FILE = make_temp_log_file(DOTFILES_DIR)

type EXITCODE = int
type StrPath = str | Path
