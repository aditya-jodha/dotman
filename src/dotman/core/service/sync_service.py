from pathlib import Path

from dotman.cli.common_func import check_file_exists
from dotman.core.config import InternalFileSystemObject, load_config
from dotman.core.get_internal_data import InternalData, InternalDataArguments
from dotman.core.linker import Linker, LinkResult
from dotman.errors.custom_errors import InvalidPackageNameError, PackageNotExistsError
from dotman.errors.profile_errors import ProfileMetaDataFileCorruptedError


class SyncService:
    def __init__(self, dry_run: bool = True) -> None:
        self.dry_run = dry_run
        cgf = load_config()
        self.home_dir = cgf.home_dir
        self.dotfiles_dir = cgf.dotfiles_dir
        self.backup_dir = self.home_dir / ".dotman_backup"
        self.internaldata: InternalData = InternalData.load()
        self.profile = self.internaldata.current_profile

    def initilize_package(self, package: str | None):
        if self.profile is None:
            raise ProfileMetaDataFileCorruptedError(
                InternalDataArguments.CURRENT_PROFILE
            )

        if package is None:
            self.packages: list[Path] = sorted(
                path
                for path in (
                    self.dotfiles_dir
                    / InternalFileSystemObject.PROFILES.value
                    / self.profile
                ).iterdir()
                if path.is_dir()
            )
            if not self.packages:
                raise PackageNotExistsError()
            return

        package_dir = (
            self.dotfiles_dir
            / InternalFileSystemObject.PROFILES.value
            / self.profile
            / package
        )
        if not package_dir.exists() or not package_dir.is_dir():
            raise InvalidPackageNameError(package=package, is_internal_package=False)

        self.packages = [package_dir]

    def load(self):
        self.linker = Linker(
            home_dir=self.home_dir, backup_dir=self.backup_dir, dry_run=self.dry_run
        )

    def execute(self) -> list[LinkResult]:
        results: list[LinkResult] = []

        for package_dir in self.packages:
            for source in self.iter_package_files(package_dir):
                target = self.home_dir / source.relative_to(package_dir)
                results.append(self.linker.execute(source, target))

        return results

    @property
    def is_dotfile_home_exits(self):
        return check_file_exists(self.home_dir, self.dotfiles_dir)

    @staticmethod
    def iter_package_files(package_dir: Path):
        for path in package_dir.rglob("*"):
            if path.is_file() or path.is_symlink():
                yield path
