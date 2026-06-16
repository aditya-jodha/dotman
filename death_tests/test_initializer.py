# ruff: noqa: S101
from pathlib import Path

from dotman.core.config import InternalFileSystemObject
from dotman.core.initializer import Initializer


class TestInitializer:
    def test_is_old_dotfiles_exist_true_and_false(self, tmp_path: Path):
        home = tmp_path / "home"
        home.mkdir()
        dotfiles = tmp_path / "dotfiles"
        init = Initializer(home, dotfiles)
        # initially does not exist
        assert init.is_old_dotfiles_exist is False
        dotfiles.mkdir()
        assert init.is_old_dotfiles_exist is True

    def test_is_backup_exist_true_and_false(self, tmp_path: Path):
        home = tmp_path / "home"
        home.mkdir()
        dotfiles = tmp_path / "dotfiles"
        dotfiles.mkdir()
        init = Initializer(home, dotfiles)
        backup_dir = dotfiles.with_suffix(".backup")
        assert init.is_backup_exist is False
        backup_dir.mkdir()
        assert init.is_backup_exist is True

    def test_convert_to_backup_renames_dir(self, tmp_path: Path):
        home = tmp_path / "home"
        home.mkdir()
        dotfiles = tmp_path / "dotfiles"
        dotfiles.mkdir()
        init = Initializer(home, dotfiles)
        backup_path = init.convert_to_backup()
        assert backup_path.exists()
        assert backup_path.name == "dotfiles.backup"
        assert not dotfiles.exists()

    def test_make_dir_creates_when_missing_and_skips_when_exists(self, tmp_path: Path):
        home = tmp_path / "home"
        home.mkdir()
        dotfiles = tmp_path / "dotfiles"
        init = Initializer(home, dotfiles)
        # should create
        init.make_dir()
        assert dotfiles.exists()
        # should not raise if already exists
        init.make_dir()
        assert dotfiles.exists()

    def test_create_meta_writes_file(self, tmp_path: Path):
        home = tmp_path / "home"
        home.mkdir()
        dotfiles = tmp_path / "dotfiles"
        dotfiles.mkdir()
        init = Initializer(home, dotfiles)
        meta_file = init.create_meta("default")
        assert meta_file.exists()
        content = meta_file.read_text()
        assert "current_profile: default" in content
        assert meta_file.name == InternalFileSystemObject.METADATA.value

    def test_create_profile_creates_nested_dir(self, tmp_path: Path):
        home = tmp_path / "home"
        home.mkdir()
        dotfiles = tmp_path / "dotfiles"
        dotfiles.mkdir()
        init = Initializer(home, dotfiles)
        profile_dir = init.create_profile("work")
        assert profile_dir.exists()
        assert profile_dir.name == "work"
        # should be inside dotfiles/profiles
        assert profile_dir.parent.name == InternalFileSystemObject.PROFILES.value
