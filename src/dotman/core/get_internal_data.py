"""
This module is used to get data from internal files.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

import yaml

from dotman.core.config import InternalFileSystemObject, load_config

if TYPE_CHECKING:
    from pathlib import Path


class InternalDataArguments(Enum):
    CURRENT_PROFILE = "current_profile"


@dataclass
class InternalData:
    current_profile: str | None
    file_path: Path

    @classmethod
    def load(cls, file_path: Path | None = None) -> InternalData:
        """Load the metadata file."""
        if file_path is None:
            file_path = (
                load_config().dotfiles_dir / InternalFileSystemObject.METADATA.value
            )

        data: dict[str, str] = {}
        if not file_path.exists():
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.touch()
            return cls(
                current_profile=None,
                file_path=file_path,
            )

        with file_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        return cls(
            current_profile=data.get(InternalDataArguments.CURRENT_PROFILE.value, None),
            file_path=file_path,
        )

    def save(self) -> None:
        """Update the metadata file with the current profile."""
        self.file_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        with self.file_path.open("w", encoding="utf-8") as f:
            yaml.safe_dump(
                {InternalDataArguments.CURRENT_PROFILE.value: self.current_profile}, f
            )

    def write(self, profile: str) -> None:
        """Write a new profile to the metadata file."""
        self.current_profile = profile
        self.save()
