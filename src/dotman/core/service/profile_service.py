# src/dotman/core/service/profile_service.py
from dataclasses import dataclass
from pathlib import Path

from dotman.core.config.config import DotmanConfig
from dotman.core.get_internal_data import InternalDataArguments
from dotman.core.linker import Linker, LinkResult, Unlinker, UnlinkResult
from dotman.core.profile import ProfileManager, ProfileScanner, ProfileState
from dotman.errors.profile_errors import (
    ProfileAlreadyExistsError,
    ProfileMetaDataFileCorruptedError,
    ProfileNotFoundError,
)


@dataclass(slots=True)
class ProfileSwitchResult:
    old_profile: str
    new_profile: str

    unlink_results: list[UnlinkResult]
    link_results: list[LinkResult]


class ProfileSwitcher:
    def __init__(self, home_dir: Path | None = None, dotfiles_dir: Path | None = None) -> None:
        cfg = DotmanConfig.load()
        self.home_dir = home_dir or cfg.home_dir
        self.dotfiles_dir = dotfiles_dir or cfg.dotfiles_dir

        self.profile_manager = ProfileManager(self.dotfiles_dir)
        self.profile_scanner = ProfileScanner(
            profile_manager=self.profile_manager, home_dir=self.home_dir
        )
        self.unlinker = Unlinker()
        self.linker = Linker(self.home_dir, self.home_dir / "dotman_backup")

    def switch_profile(self, name: str):
        if not self.profile_manager.profile_exists(name):
            raise ProfileNotFoundError(name)

        current_profile = ProfileState.get_current_profile()
        if current_profile is None:
            raise ProfileMetaDataFileCorruptedError(InternalDataArguments.CURRENT_PROFILE)

        if current_profile == name:
            return ProfileSwitchResult(
                old_profile=current_profile,
                new_profile=name,
                unlink_results=[],
                link_results=[],
            )

        current_linkpair = self.profile_scanner.scan_profile(current_profile)
        unlink_results = self.unlinker.unlink(current_linkpair)

        new_linkpair = self.profile_scanner.scan_profile(name)
        link_results = self.linker.link(new_linkpair)

        ProfileState.set_current_profile(name)

        return ProfileSwitchResult(
            old_profile=current_profile,
            new_profile=name,
            unlink_results=unlink_results,
            link_results=link_results,
        )

    def list_profiles(self) -> list[str]:
        return self.profile_manager.list_profiles()

    def create_profile(self, name: str):
        if self.profile_manager.profile_exists(name):
            raise ProfileAlreadyExistsError(name)
        self.profile_manager.create_profile(name)

    def delete_profile(self, name: str):
        if not self.profile_manager.profile_exists(name):
            raise ProfileNotFoundError(name)
        self.profile_manager.delete_profile(name)
