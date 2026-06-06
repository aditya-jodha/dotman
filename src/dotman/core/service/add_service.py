from enum import Enum
from pathlib import Path

from dotman.cli.common_func import sanitize_package_name
from dotman.cli.tree_builder import print_beautiful_directory
from dotman.core.add import AddFiles, LogBook, SymlinkCheck
from dotman.core.config import SUCCESSCODE
from dotman.errors.custom_errors_of_add import (
    FileDoesNotExistError,
    FileNameCollidingError,
    InvalidPackageNameError,
    IsNotASubPathError,
    SymFileCameInAddFilesLogicError,
    TargetFileIsDotfilesDirError,
    TargetFileIsHomeError,
)


class AddErrors(Enum):
    FileNotExists = FileDoesNotExistError
    FileIsSymLink = SymFileCameInAddFilesLogicError
    NotASubPath = IsNotASubPathError
    InvalidPackage = InvalidPackageNameError
    TargetIsHome = TargetFileIsHomeError
    TargetIsDotfilesDir = TargetFileIsDotfilesDirError
    FileNameCollidingError = FileNameCollidingError


class AddService:
    def __init__(self, file: Path, package: str, home_dir: Path, dotfiles_dir: Path) -> None:
        self.file = file
        self.package: str = sanitize_package_name(package)
        self.home_dir = home_dir
        self.dotfiles_dir = dotfiles_dir

        self.logbook = LogBook()

    def load(self):

        self.add_files = AddFiles(
            file=self.file,
            package=self.package,
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
        return print_beautiful_directory(self.logbook.log_file, str(self.dotfiles_dir))
