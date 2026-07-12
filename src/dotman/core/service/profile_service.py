# src/dotman/core/service/profile_service.py
from dataclasses import dataclass
from pathlib import Path
from typing import Self

from dotman.core.config.config import DotmanConfig
from dotman.core.config.constants import DOTMAN_BACKUP_DIR
from dotman.core.get_internal_data import DotmanMetadata
from dotman.core.linker import Linker, LinkResult, Unlinker, UnlinkResult
from dotman.core.profile import ProfileManager, ProfileScanner
from dotman.errors.profile_errors import (
    ProfileAlreadyExistsError,
    ProfileNotFoundError,
)


@dataclass(slots=True)
class ProfileSwitchResult:
    old_profile: str
    new_profile: str

    unlink_results: list[UnlinkResult]
    link_results: list[LinkResult]

    @classmethod
    def no_change(cls, name: str) -> Self:
        return cls(
            old_profile=name,
            new_profile=name,
            unlink_results=[],
            link_results=[],
        )


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
        self.linker = Linker(self.home_dir, self.home_dir / DOTMAN_BACKUP_DIR)

    def _ensure_profile_exists(self, name: str) -> None:
        if not self.profile_manager.profile_exists(name):
            raise ProfileNotFoundError(name)

    def _deactivate_profile(self, profile: str):
        link_pair = self.profile_scanner.scan_profile(profile)
        return self.unlinker.unlink(link_pair)

    def _activate_profile(self, profile: str):
        link_pair = self.profile_scanner.scan_profile(profile)
        return self.linker.link(link_pair)

    def switch_profile(self, name: str) -> ProfileSwitchResult:
        self._ensure_profile_exists(name)

        metadata = DotmanMetadata.load()
        current_profile = metadata.current_profile_or_raise()

        if current_profile == name:
            return ProfileSwitchResult.no_change(name)

        unlink_results = self._deactivate_profile(current_profile)
        link_results = self._activate_profile(name)

        metadata.with_current_profile(name).save()

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
