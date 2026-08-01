"""
This module is used to get data from internal files.
"""

from __future__ import annotations

from enum import StrEnum

# if TYPE_CHECKING:
from pathlib import (
    Path,  # noqa: TC003 # When Pydantic builds the model, it has to resolve "Path" into the real pathlib.Path
)
from typing import Self

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from dotman.core.config.config import DotmanConfig, InternalFileSystemObject
from dotman.errors.config_errors import ConfigParseError, InvalidConfigFileError
from dotman.errors.profile_errors import ProfileMetaDataFileCorruptedError


class DotmanMetadataField(StrEnum):
    CURRENT_PROFILE = "current_profile"


def resolve_profile(explicit_profile: str | None, internal_data: DotmanMetadata) -> str:
    """
    Decide which profile to use:
    - If the caller passed a profile, use it.
    - Otherwise, fall back to the current profile in DotmanMetadata.
    - If neither is available, raise ProfileMetaDataFileCorruptedError.
    """
    if explicit_profile is not None:
        return explicit_profile

    if internal_data.current_profile is not None:
        return internal_data.current_profile

    # If we reach here, both are None → corrupted metadata
    raise ProfileMetaDataFileCorruptedError(DotmanMetadataField.CURRENT_PROFILE, False)


class DotmanMetadata(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    file_path: Path = Field(exclude=True)

    current_profile: str | None = None

    @classmethod
    def load(cls, file_path: Path | None = None) -> Self:
        """Load the metadata file."""
        if file_path is None:
            file_path = DotmanConfig.load().dotfiles_dir / InternalFileSystemObject.METADATA.value

        data: dict[str, str] = {}
        if not file_path.exists():
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.touch()

            return cls(
                file_path=file_path,
            )

        try:
            with file_path.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}

            return cls.model_validate(
                {
                    **data,
                    "file_path": file_path,
                },
            )
        except yaml.YAMLError as e:
            raise ConfigParseError(file_path, e) from e
        except ValidationError as e:
            raise InvalidConfigFileError(path=file_path, error=e) from e

    def save(self) -> None:
        """Update the metadata file with the current profile."""
        self.file_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        with self.file_path.open("w", encoding="utf-8") as f:
            yaml.safe_dump(self.model_dump(mode="json"), f)

    def with_current_profile(self, profile: str) -> Self:
        return self.model_copy(update={"current_profile": profile})

    def current_profile_or_raise(self) -> str:
        if self.current_profile is None:
            raise ProfileMetaDataFileCorruptedError(DotmanMetadataField.CURRENT_PROFILE)

        return self.current_profile
