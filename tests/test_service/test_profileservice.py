# ruff: noqa: S101, ARG005
# pyright: reportPrivateUsage=false
from collections.abc import Sequence
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

import dotman.core.service.profile_service as ps
from dotman.errors.profile_errors import (
    ProfileAlreadyExistsError,
    ProfileMetaDataFileCorruptedError,
    ProfileNotFoundError,
)


# --- Typed fakes -----------------------------------------------------------
class FakeProfileManager:
    def __init__(self, profiles: Sequence[str] | None = None) -> None:
        self._profiles: set[str] = set(profiles or [])

    def profile_exists(self, name: str) -> bool:
        return name in self._profiles

    def list_profiles(self) -> list[str]:
        return sorted(self._profiles)

    def create_profile(self, name: str) -> None:
        self._profiles.add(name)

    def delete_profile(self, name: str) -> None:
        self._profiles.remove(name)


class FakeProfileScanner:
    def __init__(
        self,
        profile_manager: FakeProfileManager | None = None,
        home_dir: Path | None = None,
    ) -> None:
        self.profile_manager = profile_manager
        self.home_dir = home_dir

    def scan_profile(self, name: str) -> dict[str, Any]:
        # return a simple "linkpair" object (could be any mapping)
        return {"profile": name}


class FakeUnlinker:
    def __init__(self) -> None:
        self.called_with: dict[str, Any] | None = None

    def unlink(self, linkpair: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
        self.called_with = linkpair
        return [("unlinked", linkpair)]


class FakeLinker:
    def __init__(
        self, home_dir: Path | None = None, backup_dir: Path | None = None
    ) -> None:
        self.home_dir = home_dir
        self.backup_dir = backup_dir
        self.called_with: dict[str, Any] | None = None

    def link(self, linkpair: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
        self.called_with = linkpair
        return [("linked", linkpair)]


class FakeProfileState:
    _current: str | None = None

    @classmethod
    def get_current_profile(cls) -> str | None:
        return cls._current

    @classmethod
    def set_current_profile(cls, name: str) -> None:
        cls._current = name


# --- Fixtures --------------------------------------------------------------
@pytest.fixture
def tmp_config(tmp_path: Path) -> SimpleNamespace:
    cfg = SimpleNamespace()
    cfg.home_dir = tmp_path / "home"
    cfg.dotfiles_dir = tmp_path / "dotfiles"
    cfg.home_dir.mkdir()
    cfg.dotfiles_dir.mkdir()
    return cfg


# --- Tests -----------------------------------------------------------------
def test_list_profiles_delegates_to_profile_manager(
    monkeypatch: pytest.MonkeyPatch, tmp_config: SimpleNamespace
) -> None:
    fake_pm = FakeProfileManager(profiles=["a", "b"])
    monkeypatch.setattr(ps, "load_config", lambda: tmp_config)
    monkeypatch.setattr(ps, "ProfileManager", lambda dotfiles_dir: fake_pm)

    switcher = ps.ProfileSwitcher()
    assert switcher.list_profiles() == ["a", "b"]


def test_create_profile_raises_if_exists_and_creates_when_missing(
    monkeypatch: pytest.MonkeyPatch, tmp_config: SimpleNamespace
) -> None:
    fake_pm = FakeProfileManager(profiles=["exists"])
    monkeypatch.setattr(ps, "load_config", lambda: tmp_config)
    monkeypatch.setattr(ps, "ProfileManager", lambda dotfiles_dir: fake_pm)

    switcher = ps.ProfileSwitcher()

    with pytest.raises(ProfileAlreadyExistsError):
        switcher.create_profile("exists")

    # create a new one
    switcher.create_profile("new")
    assert "new" in fake_pm._profiles


def test_delete_profile_raises_if_missing_and_deletes_when_present(
    monkeypatch: pytest.MonkeyPatch, tmp_config: SimpleNamespace
) -> None:
    fake_pm = FakeProfileManager(profiles=["keep", "remove"])
    monkeypatch.setattr(ps, "load_config", lambda: tmp_config)
    monkeypatch.setattr(ps, "ProfileManager", lambda dotfiles_dir: fake_pm)

    switcher = ps.ProfileSwitcher()

    with pytest.raises(ProfileNotFoundError):
        switcher.delete_profile("missing")

    switcher.delete_profile("remove")
    assert "remove" not in fake_pm._profiles


def test_switch_profile_raises_if_profile_not_found(
    monkeypatch: pytest.MonkeyPatch, tmp_config: SimpleNamespace
) -> None:
    fake_pm = FakeProfileManager(profiles=["one"])
    monkeypatch.setattr(ps, "load_config", lambda: tmp_config)
    monkeypatch.setattr(ps, "ProfileManager", lambda dotfiles_dir: fake_pm)

    switcher = ps.ProfileSwitcher()
    with pytest.raises(ProfileNotFoundError):
        switcher.switch_profile("does_not_exist")


def test_switch_profile_raises_if_current_profile_none(
    monkeypatch: pytest.MonkeyPatch, tmp_config: SimpleNamespace
) -> None:
    # profile exists but ProfileState has no current profile -> metadata corrupted
    fake_pm = FakeProfileManager(profiles=["one", "two"])
    monkeypatch.setattr(ps, "load_config", lambda: tmp_config)
    monkeypatch.setattr(ps, "ProfileManager", lambda dotfiles_dir: fake_pm)
    monkeypatch.setattr(ps, "ProfileState", FakeProfileState)
    FakeProfileState._current = None

    switcher = ps.ProfileSwitcher()
    with pytest.raises(ProfileMetaDataFileCorruptedError):
        switcher.switch_profile("two")


def test_switch_profile_noop_when_same_profile(
    monkeypatch: pytest.MonkeyPatch, tmp_config: SimpleNamespace
) -> None:
    fake_pm = FakeProfileManager(profiles=["one", "two"])
    monkeypatch.setattr(ps, "load_config", lambda: tmp_config)
    monkeypatch.setattr(ps, "ProfileManager", lambda dotfiles_dir: fake_pm)
    monkeypatch.setattr(ps, "ProfileState", FakeProfileState)
    FakeProfileState._current = "one"

    # patch scanner/unlinker/linker but they should not be called for noop
    monkeypatch.setattr(
        ps, "ProfileScanner", lambda profile_manager, home_dir: FakeProfileScanner()
    )
    monkeypatch.setattr(ps, "Unlinker", lambda: FakeUnlinker())
    monkeypatch.setattr(ps, "Linker", lambda home, backup: FakeLinker())

    switcher = ps.ProfileSwitcher()
    result = switcher.switch_profile("one")
    assert result.old_profile == "one"
    assert result.new_profile == "one"
    assert result.unlink_results == []
    assert result.link_results == []


def test_switch_profile_unlink_and_link_called_and_profilestate_set(
    monkeypatch: pytest.MonkeyPatch, tmp_config: SimpleNamespace
) -> None:
    fake_pm = FakeProfileManager(profiles=["one", "two"])
    monkeypatch.setattr(ps, "load_config", lambda: tmp_config)
    monkeypatch.setattr(ps, "ProfileManager", lambda dotfiles_dir: fake_pm)
    monkeypatch.setattr(
        ps, "ProfileScanner", lambda profile_manager, home_dir: FakeProfileScanner()
    )
    monkeypatch.setattr(ps, "Unlinker", lambda: FakeUnlinker())
    monkeypatch.setattr(ps, "Linker", lambda home, backup: FakeLinker())
    monkeypatch.setattr(ps, "ProfileState", FakeProfileState)

    # set current profile to 'one'
    FakeProfileState._current = "one"

    switcher = ps.ProfileSwitcher()
    res = switcher.switch_profile("two")

    # verify unlink/link were called with scanned linkpairs
    assert res.old_profile == "one"
    assert res.new_profile == "two"
    assert res.unlink_results == [("unlinked", {"profile": "one"})]
    assert res.link_results == [("linked", {"profile": "two"})]
    # ProfileState should be updated
    assert FakeProfileState.get_current_profile() == "two"
