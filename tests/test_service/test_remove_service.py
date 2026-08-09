# ruff: noqa: S101
from pathlib import Path
from types import SimpleNamespace

import pytest

from dotman.core.service.remove_service import RemoveService, RemoveStatus
from dotman.errors.profile_errors import ProfileMetaDataFileCorruptedError


def make_service(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> tuple[RemoveService, Path, Path]:
    dotfiles_dir = tmp_path / "dotfiles"
    home_dir = tmp_path / "home"
    profile_dir = dotfiles_dir / "profiles" / "work"
    home_dir.mkdir()
    profile_dir.mkdir(parents=True)
    monkeypatch.setattr(
        "dotman.core.service.remove_service.DotmanMetadata.load",
        lambda: SimpleNamespace(current_profile="work"),
    )
    return RemoveService(dotfiles_dir=dotfiles_dir, home_dir=home_dir), profile_dir, home_dir


def test_remove_file_removes_managed_file_link_and_empty_package(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    service, profile_dir, home_dir = make_service(monkeypatch, tmp_path)
    target = profile_dir / "shell" / ".zshrc"
    target.parent.mkdir()
    target.write_text("export PATH")
    link = home_dir / ".zshrc"
    link.symlink_to(target)

    status = service.remove_file(target)

    assert status is RemoveStatus.OK
    assert not target.exists()
    assert not link.exists()
    assert not (profile_dir / "shell").exists()


def test_remove_file_reports_missing_unmanaged_and_directory(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    service, profile_dir, home_dir = make_service(monkeypatch, tmp_path)
    unmanaged = home_dir / "unmanaged"
    unmanaged.write_text("content")
    package = profile_dir / "package"
    package.mkdir()

    assert service.remove_file(profile_dir / "missing") is RemoveStatus.FileNotFound
    assert service.remove_file(unmanaged) is RemoveStatus.NotASubPath
    assert service.remove_file(package) is RemoveStatus.IsADirectory


def test_remove_service_rejects_missing_active_profile(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(
        "dotman.core.service.remove_service.DotmanMetadata.load",
        lambda: SimpleNamespace(current_profile=None),
    )

    with pytest.raises(ProfileMetaDataFileCorruptedError):
        RemoveService(dotfiles_dir=tmp_path / "dotfiles", home_dir=tmp_path)
