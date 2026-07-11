# ruff: noqa: S101

from dataclasses import dataclass
from pathlib import Path

import pytest

from dotman.core.config import InternalFileSystemObject
from dotman.core.get_internal_data import InternalData
from dotman.core.profile import ProfileManager, ProfileScanner, ProfileState
from dotman.errors.profile_errors import (
    DirNotEmptyError,
    ProfileAlreadyExistsError,
    ProfileNotFoundError,
)


@dataclass
class LabPaths:
    home: Path
    dotfiles_dir: Path

    profile: str
    profile_root: Path

    meta_path: Path


@pytest.fixture
def lab(tmp_path: Path) -> LabPaths:
    home = tmp_path / "home"
    dotfiles = tmp_path / "dotfiles"
    meta_data = dotfiles / "meta_data.yml"

    profile = "default"
    profile_root = dotfiles / "profiles" / profile

    home.mkdir()
    dotfiles.mkdir()
    meta_data.write_text(f"current_profile: {profile}\n")
    return LabPaths(
        home=home,
        dotfiles_dir=dotfiles,
        profile=profile,
        profile_root=profile_root,
        meta_path=meta_data,
    )


class TestProfileState:
    def test_get_currnent_profile_success(self, lab: LabPaths):
        a = ProfileState.get_current_profile(lab.meta_path)
        assert a == lab.profile

    def test_get_currnent_profile_not_exist_metadata(self, lab: LabPaths):
        lab.meta_path.unlink()
        a = ProfileState.get_current_profile(lab.meta_path)
        assert a is None

    def test_set_currnent_profile_success(self, lab: LabPaths):
        ProfileState.set_current_profile(lab.profile, lab.meta_path)
        assert ProfileState.get_current_profile(lab.meta_path) == lab.profile

    def test_set_currnent_profile_not_exist_metadata(
        self,
        lab: LabPaths,
    ):
        lab.meta_path.unlink()

        ProfileState.set_current_profile(
            lab.profile,
            lab.meta_path,
        )

        assert lab.meta_path.exists()

        assert ProfileState.get_current_profile(lab.meta_path) == lab.profile

    def test_load_creates_missing_metadata(self, tmp_path: Path):
        meta = tmp_path / "meta.yml"

        data = InternalData.load(meta)

        assert meta.exists()
        assert data.current_profile is None

    def test_set_currnent_profile_not_exist_profile(self, lab: LabPaths) -> None:
        lab.meta_path.write_text("")
        ProfileState.set_current_profile("work", lab.meta_path)

        assert lab.meta_path.exists()
        assert ProfileState.get_current_profile(lab.meta_path) == "work"

    def test_set_currnent_profile_not_exist_home(self, lab: LabPaths) -> None:
        lab.home.rmdir()

        ProfileState.set_current_profile("default", lab.meta_path)

        assert lab.meta_path.exists()
        assert ProfileState.get_current_profile(lab.meta_path) == "default"


class TestProfileManager:
    def test_create_profile(self, lab: LabPaths):
        manager = ProfileManager(lab.dotfiles_dir)

        manager.create_profile("personal")

        assert (lab.dotfiles_dir / InternalFileSystemObject.PROFILES.value / "personal").exists()

    def test_create_profile_duplicate(self, lab: LabPaths):
        manager = ProfileManager(lab.dotfiles_dir)

        manager.create_profile("personal")

        with pytest.raises(ProfileAlreadyExistsError):
            manager.create_profile("personal")

    def test_create_default_profile(self, lab: LabPaths):
        manager = ProfileManager(lab.dotfiles_dir)

        manager.create_profile()

        assert manager.profile_exists("default")

    def test_delete_profile(self, lab: LabPaths):
        manager = ProfileManager(lab.dotfiles_dir)

        manager.create_profile("personal")
        manager.delete_profile("personal")

        assert not manager.profile_exists("personal")

    def test_delete_missing_profile(self, lab: LabPaths):
        manager = ProfileManager(lab.dotfiles_dir)

        with pytest.raises(ProfileNotFoundError):
            manager.delete_profile("ghost")

    def test_delete_profile_not_empty(self, lab: LabPaths):
        manager = ProfileManager(lab.dotfiles_dir)
        profile = "ghost"
        manager.create_profile(profile)
        pth = manager.profile_path(profile)

        (pth / "pkg").mkdir(parents=True, exist_ok=False)
        with pytest.raises(DirNotEmptyError):
            manager.delete_profile(profile)

    def test_list_profiles(self, lab: LabPaths):
        manager = ProfileManager(lab.dotfiles_dir)

        manager.create_profile("personal")
        manager.create_profile("work")

        profiles = manager.list_profiles()

        assert "personal" in profiles
        assert "work" in profiles

    def test_profile_exists(self, lab: LabPaths):
        manager = ProfileManager(lab.dotfiles_dir)

        manager.create_profile("personal")

        assert manager.profile_exists("personal") is True
        assert manager.profile_exists("ghost") is False


class TestProfileScanner:
    def test_scan_empty_profile(self, lab: LabPaths):
        manager = ProfileManager(lab.dotfiles_dir)

        manager.create_profile("personal")

        scanner = ProfileScanner(lab.home, manager)

        assert scanner.scan_profile("personal") == []

    def test_scan_single_file(self, lab: LabPaths):
        manager = ProfileManager(lab.dotfiles_dir)
        manager.create_profile("personal")

        file = manager.profile_path("personal") / "bash" / ".bashrc"

        file.parent.mkdir(parents=True)
        file.write_text("hello")

        scanner = ProfileScanner(lab.home, manager)

        result = scanner.scan_profile("personal")

        assert len(result) == 1

    def test_scan_nested_file(self, lab: LabPaths):
        manager = ProfileManager(lab.dotfiles_dir)
        manager.create_profile("personal")

        file = manager.profile_path("personal") / "nvim" / ".config" / "nvim" / "init.lua"

        file.parent.mkdir(parents=True)
        file.write_text("hello")

        scanner = ProfileScanner(lab.home, manager)

        result = scanner.scan_profile("personal")

        assert len(result) == 1

        pair = result[0]

        assert pair.relative_source == Path(".config/nvim/init.lua")

    def test_scan_missing_profile(self, lab: LabPaths):
        manager = ProfileManager(lab.dotfiles_dir)
        scanner = ProfileScanner(lab.home, manager)

        with pytest.raises(ProfileNotFoundError):
            scanner.scan_profile("ghost")
