from typing import TYPE_CHECKING

from dotman.core.config.config import DotmanConfig
from dotman.core.doctor import Doctor
from dotman.core.get_internal_data import DotmanMetadata, DotmanMetadataField
from dotman.errors.profile_errors import ProfileMetaDataFileCorruptedError

if TYPE_CHECKING:
    from pathlib import Path


class DoctorService:
    def __init__(self, detail: bool):
        config = DotmanConfig.load()
        self.home_dir: Path = config.home_dir
        self.dotfiles_dir: Path = config.dotfiles_dir
        self.detail = detail
        self.internal_data: DotmanMetadata = DotmanMetadata.load()

    def load(self):
        current_profile = self.internal_data.current_profile
        if current_profile is None:
            raise ProfileMetaDataFileCorruptedError(DotmanMetadataField.CURRENT_PROFILE)

        self.doctor = Doctor(
            profile_name=current_profile,
            home_dir=self.home_dir,
            dotfile_dir=self.dotfiles_dir,
            detail=self.detail,
        )

    def run(self):
        return self.doctor.run_all()
