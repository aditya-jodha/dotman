from enum import Enum
from pathlib import Path

from dotman.cli.common_func import check_file_exists, sanitize_package_name
from dotman.cli.tree_builder import print_beautiful_directory
from dotman.core.add import AddFiles, LogBook, SymlinkCheck
from dotman.core.config import SUCCESSCODE, InternalFileSystemObject, load_config
from dotman.core.get_internal_data import InternalData, InternalDataArguments
from dotman.errors.custom_errors import (
    FileDoesNotExistError,
    FileNameCollidingError,
    InvalidPackageNameError,
    IsNotASubPathError,
    SymFileCameInAddFilesLogicError,
    TargetFileIsDotfilesDirError,
    TargetFileIsHomeError,
)
from dotman.errors.profile_errors import ProfileMetaDataFileCorruptedError


class AddErrors(Enum):
    FileNotExists = FileDoesNotExistError
    FileIsSymLink = SymFileCameInAddFilesLogicError
    NotASubPath = IsNotASubPathError
    InvalidPackage = InvalidPackageNameError
    TargetIsHome = TargetFileIsHomeError
    TargetIsDotfilesDir = TargetFileIsDotfilesDirError
    FileNameCollidingError = FileNameCollidingError


class AddService:
    def __init__(
        self,
        file: Path,
        package: str,
        home_dir: Path | None = None,
        dotfiles_dir: Path | None = None,
        profile: str | None = None,
    ) -> None:
        self.file = file
        self.package: str = sanitize_package_name(package)

        config = load_config()
        self.home_dir = home_dir or config.home_dir
        self.dotfiles_dir = dotfiles_dir or config.dotfiles_dir
        self.profile = profile

        self.logbook = LogBook()
        self.internal_data: InternalData = InternalData.load()

    def load(self):
        current_profile = self.internal_data.current_profile

        if current_profile is None and self.profile is None:
            raise ProfileMetaDataFileCorruptedError(InternalDataArguments.CURRENT_PROFILE)

        chosen_profile = self.profile if self.profile is not None else current_profile

        self.add_files = AddFiles(
            file=self.file,
            package=self.package,
            profile_name=chosen_profile,  # type: ignore # Already checked for None
            home_dir=self.home_dir,
            dotfiles_dir=self.dotfiles_dir,
            logbook=self.logbook,
        )

    def validate_directory_symlinks(self) -> list[SymlinkCheck]:
        return self.add_files.validate_directory_symlinks()

    def create_reuse_package(self) -> bool:
        """It will return True if package exist else it will create package and return False"""
        if self.add_files.package_exists:
            return True
        self.add_files.create_package()
        return False

    def service_validate(self) -> AddErrors | None:
        try:
            self.add_files.validate()
        except FileDoesNotExistError:
            return AddErrors.FileNotExists
        except SymFileCameInAddFilesLogicError:
            return AddErrors.FileIsSymLink
        except IsNotASubPathError:
            return AddErrors.NotASubPath
        except InvalidPackageNameError:
            return AddErrors.InvalidPackage
        except TargetFileIsHomeError:
            return AddErrors.TargetIsHome
        except TargetFileIsDotfilesDirError:
            return AddErrors.TargetIsDotfilesDir
        except FileNameCollidingError:
            return AddErrors.FileNameCollidingError
        return None

    def service_add_file(self) -> SUCCESSCODE:
        self.add_files.move_file_to_dotfiles()
        return 1

    @property
    def is_dir(self) -> bool:
        return self.add_files.is_dir

    @property
    def package_exists(self):
        return self.add_files.package_exists

    def delete_log(self):
        return self.logbook.clear_log()

    def restore_files(self):
        return self.logbook.restore_files()

    def create_tree(self):
        profile = self.profile or self.internal_data.current_profile
        if profile is None:
            raise ProfileMetaDataFileCorruptedError(InternalDataArguments.CURRENT_PROFILE)

        return print_beautiful_directory(
            self.logbook.log_file,
            self.dotfiles_dir / InternalFileSystemObject.PROFILES.value / profile,
        )

    @property
    def is_dotfile_home_exits(self):
        return check_file_exists(self.home_dir, self.dotfiles_dir)
