# ruff: noqa: S101
from pathlib import Path
from types import SimpleNamespace

import pytest

from dotman.core.config.config import DotmanConfig
from dotman.core.service.sync_service import SyncService
from dotman.errors.custom_errors import InvalidPackageNameError, PackageNotExistsError
from dotman.errors.profile_errors import ProfileMetaDataFileCorruptedError


def make_sync_service(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, current_profile: str | None = "work"
) -> tuple[SyncService, Path, Path]:
    home_dir = tmp_path / "home"
    dotfiles_dir = tmp_path / "dotfiles"
    home_dir.mkdir()
    dotfiles_dir.mkdir()
    config = DotmanConfig(home_dir=home_dir, dotfiles_dir=dotfiles_dir)
    monkeypatch.setattr("dotman.core.service.sync_service.DotmanConfig.load", lambda: config)
    monkeypatch.setattr(
        "dotman.core.service.sync_service.DotmanMetadata.load",
        lambda: SimpleNamespace(current_profile=current_profile),
    )
    return SyncService(dry_run=True), dotfiles_dir, home_dir


def test_sync_named_package_dry_run_preserves_home(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    service, dotfiles_dir, home_dir = make_sync_service(monkeypatch, tmp_path)
    source = dotfiles_dir / "profiles" / "work" / "shell" / ".zshrc"
    source.parent.mkdir(parents=True)
    source.write_text("export PATH")

    service.initilize_package("shell")
    service.load()
    results = service.execute()

    assert len(results) == 1
    assert results[0].status == "dry-run"
    assert results[0].target == home_dir / ".zshrc"
    assert not (home_dir / ".zshrc").exists()


def test_sync_package_selection_errors(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    service, dotfiles_dir, _ = make_sync_service(monkeypatch, tmp_path)
    (dotfiles_dir / "profiles" / "work").mkdir(parents=True)

    with pytest.raises(PackageNotExistsError):
        service.initilize_package(None)
    with pytest.raises(InvalidPackageNameError):
        service.initilize_package("missing")


def test_sync_rejects_missing_active_profile(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    service, _, _ = make_sync_service(monkeypatch, tmp_path, current_profile=None)

    with pytest.raises(ProfileMetaDataFileCorruptedError):
        service.initilize_package(None)
