from typing import TYPE_CHECKING

from dotman.core.config.config import DotmanConfig
from dotman.core.doctor import Doctor
from dotman.core.get_internal_data import DotmanMetadataField
from dotman.errors.profile_errors import ProfileMetaDataFileCorruptedError

if TYPE_CHECKING:
    from pathlib import Path


class DoctorService:
    def __init__(
        self,
        current_profile: str | None,
        detail: bool,
        config: DotmanConfig,
    ):
        self.home_dir: Path = config.home_dir
        self.dotfiles_dir: Path = config.dotfiles_dir
        self.detail = detail
        self.current_profile: str | None = current_profile

    def execute(self):
        """Loads the main core doctor engine.

        Raises:
            ProfileMetaDataFileCorruptedError:
                If no active profile exists in the metadata.
        """
        if self.current_profile is None:
            raise ProfileMetaDataFileCorruptedError(DotmanMetadataField.CURRENT_PROFILE)

        self.doctor = Doctor(
            profile_name=self.current_profile,
            home_dir=self.home_dir,
            dotfile_dir=self.dotfiles_dir,
            detail=self.detail,
        )
        return self.doctor
