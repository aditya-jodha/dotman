# ruff: noqa: S101, ARG005
# pyright: reportPrivateUsage=false, reportUnknownParameterType=false, reportMissingParameterType=false
from pathlib import Path
from types import SimpleNamespace

import pytest

import dotman.core.get_internal_data as ps2
import dotman.core.service.profile_service as ps
from dotman.core.linker import LinkPair
from dotman.core.profile import ProfileManager, ProfileScanner
from dotman.errors.profile_errors import (
    DirNotEmptyError,
    ProfileAlreadyExistsError,
    ProfileNotFoundError,
)


# --- Base Fakes ------------------------------------------------------------
class BaseFakes:
    class FakeProfileManager:
        def __init__(self, profiles=None):
            self._profiles = set(profiles or [])

        def profile_exists(self, name):
            return name in self._profiles

        def list_profiles(self):
            return sorted(self._profiles)

        def create_profile(self, name):
            self._profiles.add(name)

        def delete_profile(self, name):
            self._profiles.remove(name)

    class FakeScanner:
        def scan_profile(self, name):
            return {"profile": name}

    class FakeUnlinker:
        def unlink(self, linkpair):
            return [("unlinked", linkpair)]

    class FakeLinker:
        def link(self, linkpair):
            return [("linked", linkpair)]

    class FakeMetadata:
        def __init__(self, current):
            self.current_profile = current

        def current_profile_or_raise(self):
            if self.current_profile is None:
                raise RuntimeError("corrupted")
            return self.current_profile

        def with_current_profile(self, profile):
            return BaseFakes.FakeMetadata(profile)

        def save(self):
            return True


# --- Fixtures --------------------------------------------------------------
@pytest.fixture
def tmp_config(tmp_path: Path) -> SimpleNamespace:
    cfg = SimpleNamespace()
    cfg.home_dir = tmp_path / "home"
    cfg.dotfiles_dir = tmp_path / "dotfiles"
    cfg.home_dir.mkdir()
    cfg.dotfiles_dir.mkdir()
    return cfg


@pytest.fixture
def dotfiles_dir(tmp_path: Path) -> Path:
    """Provide a dotfiles directory with the expected structure."""
    d = tmp_path / "dotfiles"
    d.mkdir()
    return d


# --- Test Classes ----------------------------------------------------------
class TestProfileManagerOps(BaseFakes):
    def test_list_profiles(self, monkeypatch, tmp_config):
        monkeypatch.setattr(ps.DotmanConfig, "load", lambda *_: tmp_config)
        monkeypatch.setattr(ps, "ProfileManager", lambda _: self.FakeProfileManager(["a", "b"]))
        switcher = ps.ProfileSwitcher()
        assert switcher.list_profiles() == ["a", "b"]

    def test_create_and_delete_profile(self, monkeypatch, tmp_config):
        pm = self.FakeProfileManager(["exists"])
        monkeypatch.setattr(ps.DotmanConfig, "load", lambda *_: tmp_config)
        monkeypatch.setattr(ps, "ProfileManager", lambda _: pm)
        switcher = ps.ProfileSwitcher()

        with pytest.raises(ProfileAlreadyExistsError):
            switcher.create_profile("exists")

        switcher.create_profile("new")
        assert "new" in pm._profiles

        with pytest.raises(ProfileNotFoundError):
            switcher.delete_profile("missing")

        switcher.delete_profile("new")
        assert "new" not in pm._profiles


class TestSwitchProfile(BaseFakes):
    def setup_switcher(self, monkeypatch, tmp_config, profiles, current):
        monkeypatch.setattr(ps.DotmanConfig, "load", lambda *_: tmp_config)
        monkeypatch.setattr(ps, "ProfileManager", lambda _: self.FakeProfileManager(profiles))
        monkeypatch.setattr(ps, "ProfileScanner", lambda *a, **k: self.FakeScanner())
        monkeypatch.setattr(ps, "Unlinker", lambda: self.FakeUnlinker())
        monkeypatch.setattr(ps, "Linker", lambda *a, **k: self.FakeLinker())
        monkeypatch.setattr(ps2.DotmanMetadata, "load", lambda *_: self.FakeMetadata(current))
        return ps.ProfileSwitcher()

    def test_switch_profile_no_change(self, monkeypatch, tmp_config):
        switcher = self.setup_switcher(monkeypatch, tmp_config, ["one"], "one")
        result = switcher.switch_profile("one")
        assert isinstance(result, ps.ProfileSwitchResult)
        assert result.old_profile == result.new_profile
        assert result.unlink_results == []
        assert result.link_results == []

    def test_switch_profile_changes(self, monkeypatch, tmp_config):
        switcher = self.setup_switcher(monkeypatch, tmp_config, ["one", "two"], "one")
        result = switcher.switch_profile("two")
        assert result.old_profile == "one"
        assert result.new_profile == "two"
        assert all(isinstance(x, tuple) for x in result.unlink_results)
        assert all(isinstance(x, tuple) for x in result.link_results)

    def test_switch_profile_not_found(self, monkeypatch, tmp_config):
        switcher = self.setup_switcher(monkeypatch, tmp_config, ["one"], "one")
        with pytest.raises(ProfileNotFoundError):
            switcher.switch_profile("missing")

    def test_switch_profile_corrupted_metadata(self, monkeypatch, tmp_config):
        switcher = self.setup_switcher(monkeypatch, tmp_config, ["one"], None)
        with pytest.raises(RuntimeError):
            switcher.switch_profile("one")


class TestInternalHelpers(BaseFakes):
    def test_ensure_profile_exists(self, monkeypatch, tmp_config):
        pm = self.FakeProfileManager(["x"])
        monkeypatch.setattr(ps.DotmanConfig, "load", lambda *_: tmp_config)
        monkeypatch.setattr(ps, "ProfileManager", lambda _: pm)
        switcher = ps.ProfileSwitcher()
        switcher._ensure_profile_exists("x")
        with pytest.raises(ProfileNotFoundError):
            switcher._ensure_profile_exists("y")

    def test_deactivate_and_activate(self, monkeypatch, tmp_config):
        monkeypatch.setattr(ps.DotmanConfig, "load", lambda *_: tmp_config)
        monkeypatch.setattr(ps, "ProfileManager", lambda _: self.FakeProfileManager(["x"]))
        monkeypatch.setattr(ps, "ProfileScanner", lambda *a, **k: self.FakeScanner())
        monkeypatch.setattr(ps, "Unlinker", lambda: self.FakeUnlinker())
        monkeypatch.setattr(ps, "Linker", lambda *a, **k: self.FakeLinker())
        switcher = ps.ProfileSwitcher()
        assert switcher._deactivate_profile("x")[0][0] == "unlinked"  # pyright: ignore[reportIndexIssue]
        assert switcher._activate_profile("x")[0][0] == "linked"  # pyright: ignore[reportIndexIssue]


class TestProfileSwitchResult:
    def test_no_change_classmethod(self):
        res = ps.ProfileSwitchResult.no_change("abc")
        assert res.old_profile == "abc"
        assert res.new_profile == "abc"
        assert res.unlink_results == []
        assert res.link_results == []


class TestProfileManager:
    def setup_method(self):
        pass

    def test_create_profile_default_and_duplicate(self, dotfiles_dir):
        pm = ProfileManager(dotfiles_dir)
        pm.create_profile()  # default
        assert pm.profile_exists("default")
        with pytest.raises(ProfileAlreadyExistsError):
            pm.create_profile("default")

    def test_delete_profile_missing_and_nonempty(self, dotfiles_dir):
        pm = ProfileManager(dotfiles_dir)
        pm.create_profile("x")
        # add file to make dir nonempty
        pkg = pm.profile_path("x") / "pkg"
        pkg.mkdir()
        (pkg / "f.txt").write_text("data")
        with pytest.raises(DirNotEmptyError):
            pm.delete_profile("x")
        # missing profile
        with pytest.raises(ProfileNotFoundError):
            pm.delete_profile("nope")

    def test_list_profiles_and_packages(self, dotfiles_dir):
        pm = ProfileManager(dotfiles_dir)
        pm.create_profile("p1")
        pm.create_profile("p2")
        assert set(pm.list_profiles()) == {"p1", "p2"}
        # add packages
        (pm.profile_path("p1") / "pkg1").mkdir()
        (pm.profile_path("p1") / "pkg2").mkdir()
        assert set(pm.list_profile_packages("p1")) == {"pkg1", "pkg2"}
        with pytest.raises(ProfileNotFoundError):
            pm.list_profile_packages("missing")

    def test_profile_exists_and_path(self, dotfiles_dir):
        pm = ProfileManager(dotfiles_dir)
        pm.create_profile("abc")
        assert pm.profile_exists("abc")
        assert pm.profile_path("abc").name == "abc"


class TestProfileScanner:
    def test_scan_profile_builds_linkpairs(self, tmp_path):
        dotfiles_dir = tmp_path / "dotfiles"
        dotfiles_dir.mkdir()
        pm = ProfileManager(dotfiles_dir)
        pm.create_profile("p1")
        pkg = pm.profile_path("p1") / "pkg"
        pkg.mkdir()
        file = pkg / "f.txt"
        file.write_text("hello")

        scanner = ProfileScanner(tmp_path / "home", pm)
        results = scanner.scan_profile("p1")
        assert isinstance(results[0], LinkPair)
        assert results[0].source == file
        assert results[0].target == (tmp_path / "home" / "f.txt")

    def test_scan_profile_missing(self, tmp_path):
        dotfiles_dir = tmp_path / "dotfiles"
        dotfiles_dir.mkdir()
        pm = ProfileManager(dotfiles_dir)
        scanner = ProfileScanner(tmp_path / "home", pm)
        with pytest.raises(ProfileNotFoundError):
            scanner.scan_profile("nope")
