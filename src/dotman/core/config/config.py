from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any
from uuid import uuid4

import yaml
from pydantic import BaseModel, ConfigDict, DirectoryPath, ValidationError, field_validator

from dotman.errors.config_errors import (
    ConfigParseError,
    InvalidConfigFileError,
    InvalidConfigKeyError,
    InvalidConfigValueError,
)

from .constants import (
    CONFIG_ENV_VAR,
    DEFAULT_CONFIG_PATH,
    DEFAULT_DOTFILES_DIR,
    DEFAULT_HOME_DIR,
    DEFAULT_PLUGINS_DIR,
)

if TYPE_CHECKING:
    from .types import StrPath


class DotmanConfig(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    dotfiles_dir: Path
    home_dir: DirectoryPath

    plugins_dir: Path

    def save(self, path: Path | None = None) -> None:
        """Save the config to a file."""

        config_path = path or type(self).path()
        config_path.parent.mkdir(parents=True, exist_ok=True)

        with config_path.open("w", encoding="utf-8") as f:
            yaml.safe_dump(self.model_dump(mode="json"), f)

    @staticmethod
    def path() -> Path:
        """Get the path to the config file."""
        return Path(os.getenv(CONFIG_ENV_VAR, DEFAULT_CONFIG_PATH)).expanduser()

    @field_validator("dotfiles_dir", "home_dir", "plugins_dir", mode="before")
    @classmethod
    def expand_path(cls, value: StrPath) -> Path:
        return Path(value).expanduser()

    @classmethod
    def default(cls) -> DotmanConfig:
        return DotmanConfig(
            dotfiles_dir=DEFAULT_DOTFILES_DIR,
            home_dir=DEFAULT_HOME_DIR,
            plugins_dir=DEFAULT_PLUGINS_DIR,
        )

    def set(self, key: Any, value: Any) -> DotmanConfig:
        if key not in type(self).model_fields:
            raise InvalidConfigKeyError(key, tuple(type(self).model_fields))

        data = self.model_dump()
        data[key] = value

        try:
            return self.__class__.model_validate(data)
        except ValidationError as e:
            raise InvalidConfigValueError(key, value, e) from e

    @classmethod
    def load(cls, path: Path | None = None) -> DotmanConfig:
        """Load the config from a file.\n
        _The dotfiles_dir and home_dir values are already ***expanded***._"""

        config_path = path or cls.path()

        if not config_path.exists():
            return cls.default()

        try:
            with config_path.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}

            return cls.model_validate(data)

        except yaml.YAMLError as e:
            raise ConfigParseError(config_path, e) from e

        except ValidationError as e:
            raise InvalidConfigFileError(path=config_path, error=e) from e


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
