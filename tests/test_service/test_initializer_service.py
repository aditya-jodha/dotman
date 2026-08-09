# ruff: noqa: S101
from pathlib import Path

import pytest

from dotman.core.service.initializer_service import InitializerService
from dotman.errors.initializer_errors import DotmanDotfilesBackupDirExistsError


def test_setup_creates_dotfiles_metadata_and_profile(tmp_path: Path) -> None:
    dotfiles_dir = tmp_path / "dotfiles"
    service = InitializerService(home_dir=tmp_path, dotfiles_dir=dotfiles_dir)

    result = service.setup("work")

    assert result is service.initializer
    assert (dotfiles_dir / "metadata.yml").read_text() == "current_profile: work\n"
    assert (dotfiles_dir / "profiles" / "work").is_dir()


def test_setup_backs_up_existing_dotfiles_directory(tmp_path: Path) -> None:
    dotfiles_dir = tmp_path / "dotfiles"
    dotfiles_dir.mkdir()
    (dotfiles_dir / "old-file").write_text("old")
    service = InitializerService(home_dir=tmp_path, dotfiles_dir=dotfiles_dir)

    service.setup("fresh")

    assert (tmp_path / "dotfiles.backup" / "old-file").read_text() == "old"
    assert (dotfiles_dir / "profiles" / "fresh").is_dir()


def test_setup_rejects_existing_backup(tmp_path: Path) -> None:
    dotfiles_dir = tmp_path / "dotfiles"
    dotfiles_dir.mkdir()
    (tmp_path / "dotfiles.backup").mkdir()
    service = InitializerService(home_dir=tmp_path, dotfiles_dir=dotfiles_dir)

    with pytest.raises(DotmanDotfilesBackupDirExistsError):
        service.setup("work")
