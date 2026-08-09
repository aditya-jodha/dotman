# ruff: noqa: S101
from pathlib import Path

import pytest

from dotman.core.config.config import DotmanConfig
from dotman.core.service.doctor_service import DoctorService
from dotman.errors.profile_errors import ProfileMetaDataFileCorruptedError


def test_execute_builds_doctor_for_active_profile(tmp_path: Path) -> None:
    home_dir = tmp_path / "home"
    dotfiles_dir = tmp_path / "dotfiles"
    home_dir.mkdir()
    (dotfiles_dir / "profiles" / "work").mkdir(parents=True)
    config = DotmanConfig(home_dir=home_dir, dotfiles_dir=dotfiles_dir)

    doctor = DoctorService("work", detail=True, config=config).execute()

    assert doctor.profile_name == "work"
    assert doctor.home_dir == home_dir
    assert doctor.dotfiles_dir == dotfiles_dir
    assert doctor.detail is True


def test_execute_rejects_missing_active_profile(tmp_path: Path) -> None:
    config = DotmanConfig(home_dir=tmp_path, dotfiles_dir=tmp_path)

    with pytest.raises(ProfileMetaDataFileCorruptedError):
        DoctorService(None, detail=False, config=config).execute()
