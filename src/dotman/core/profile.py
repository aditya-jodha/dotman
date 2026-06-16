from pathlib import Path

from dotman.core.config import InternalFileSystemObject
from dotman.core.get_internal_data import InternalData
from dotman.core.linker import LinkPair
from dotman.errors.profile_errors import (
    DirNotEmptyError,
    ProfileAlreadyExistsError,
    ProfileNotFoundError,
)


class ProfileState:
    @staticmethod
    def get_current_profile(meta_path: Path | None = None) -> str | None:
        load = InternalData.load(file_path=meta_path)
        return load.current_profile

    @staticmethod
    def set_current_profile(name: str, meta_path: Path | None = None) -> None:
        load = InternalData.load(file_path=meta_path)
        load.current_profile = name
        load.save()


class ProfileManager:
    def __init__(self, dotfiles_dir: Path):
        self.dotfiles_dir: Path = dotfiles_dir
        self.profiles_dir: Path = (
            self.dotfiles_dir / InternalFileSystemObject.PROFILES.value
        )

    def create_profile(self, name: str | None = None):
        if name is None:
            name = "default"
        if self.profile_exists(name):
            raise ProfileAlreadyExistsError(name)
        self.profiles_dir.mkdir(exist_ok=True)
        (self.profiles_dir / name).mkdir(exist_ok=True)

    def delete_profile(self, name: str):
        if not self.profile_exists(name):
            raise ProfileNotFoundError(name)
        if any((self.profiles_dir / name).iterdir()):
            raise DirNotEmptyError(self.profiles_dir)
        (self.profiles_dir / name).rmdir()

    def list_profiles(self) -> list[str]:
        return [
            profile.name for profile in self.profiles_dir.iterdir() if profile.is_dir()
        ]

    def profile_exists(self, name: str) -> bool:
        return self.profile_path(name).exists()

    def profile_path(self, name: str) -> Path:
        return self.profiles_dir / name


class ProfileScanner:
    def __init__(self, home_dir: Path, profile_manager: ProfileManager):
        self.profile_manager = profile_manager
        self.home_dir = home_dir

    def scan_profile(self, profile_name: str) -> list[LinkPair]:
        checks: list[LinkPair] = []
        if not self.profile_manager.profile_exists(profile_name):
            raise ProfileNotFoundError(profile_name)

        for package in self.profile_manager.profile_path(profile_name).iterdir():
            for source in package.rglob("*"):
                if not source.is_file():
                    continue

                relative = source.relative_to(package)

                checks.append(
                    LinkPair(
                        source=source,
                        relative_source=relative,
                        target=self.home_dir / relative,
                    )
                )

        return checks
