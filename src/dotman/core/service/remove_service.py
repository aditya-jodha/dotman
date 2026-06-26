from __future__ import annotations

from enum import Enum, auto
from pathlib import Path

from dotman.core.config import ExitCode, InternalFileSystemObject, StrPath, load_config
from dotman.core.get_internal_data import InternalData, InternalDataArguments
from dotman.core.utils.fs import FileSystemUtil
from dotman.errors.profile_errors import ProfileMetaDataFileCorruptedError


class RemoveStatus(Enum):
    FileNotFound = auto()
    NotASubPath = auto()
    IsADirectory = auto()
    OK = auto()

    @property
    def message(self):
        return {
            self.FileNotFound: f"File: {self._file_name} not found in dotfiles directory",
            self.NotASubPath: f"File: {self._file_name} is not a managed by dotman",
            self.IsADirectory: f"File: {self._file_name} is a directory",
            self.OK: "Successfully removed",
        }[self]

    def set_file(self, file_name: StrPath) -> RemoveStatus:
        """Bind the file context to the enum instance"""
        self._file_name = file_name
        return self


class RemoveService:
    def __init__(
        self,
        dotfiles_dir: Path | None = None,
        home_dir: Path | None = None,
    ):
        cgf = load_config()

        self.dotfiles_dir = dotfiles_dir or cgf.dotfiles_dir
        self.home_dir = home_dir or cgf.home_dir

        # NOTE: can raise ProfileMetaDataFileCorruptedError
        self.profile_path = self._get_profile_path(self.dotfiles_dir)

    def remove_file(self, file: Path) -> RemoveStatus:
        """Helper function which contains business logic to remove the file.

        Args:
            file (Path): File to be removed.

        Returns:
            RemoveStatus (Enum): Status of the file removal.
        """
        original_file = file
        target = file.expanduser().resolve()
        if not target.exists():
            return RemoveStatus.FileNotFound.set_file(target)

        if not target.is_relative_to(self.profile_path):
            return RemoveStatus.NotASubPath.set_file(target)

        rel_to_profile = target.relative_to(self.profile_path)

        # removes the package name from the path
        _, *derived_file_path = rel_to_profile.parts

        clean_rel_path = Path(*derived_file_path)

        home_path = self.home_dir / clean_rel_path
        if home_path != original_file:
            pass

        if target.is_dir():
            return RemoveStatus.IsADirectory.set_file(target)

        target.unlink()

        if home_path.is_symlink() and not target.exists():
            home_path.unlink()

        self.delete_empty_package(self.profile_path, target)

        return RemoveStatus.OK.set_file(original_file)

    # ======= Helpers ======= #

    @staticmethod
    def _get_profile_path(dotfiles_dir: Path) -> Path:
        current_profile = InternalData.load().current_profile

        if current_profile is None:
            raise ProfileMetaDataFileCorruptedError(InternalDataArguments.CURRENT_PROFILE)

        profile: Path = dotfiles_dir / InternalFileSystemObject.PROFILES.value / current_profile
        if not profile.exists():
            raise ProfileMetaDataFileCorruptedError(InternalDataArguments.CURRENT_PROFILE, False)

        return profile

    @staticmethod
    def delete_empty_package(profile_path: Path, target: Path) -> ExitCode:
        return FileSystemUtil.delete_empty_package(profile_path, target)
