# ruff: noqa: S101, ARG005, ARG001, TRY003
# pyright: reportMissingParameterType=false
# pyright: reportUnknownParameterType=false

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from pytest import MonkeyPatch

from dotman.core.add import AddFiles, SymlinkStatus
from dotman.core.config import ExitCode, InternalFileSystemObject
from dotman.errors.custom_errors import (
    FileDoesNotExistError,
    FileNameCollidingError,
    InvalidPackageNameError,
    IsNotASubPathError,
    SymlinkNotSupportedError,
    TargetFileIsDotfilesDirError,
    TargetFileIsHomeError,
)

# ============================================================
# Helpers
# ============================================================


def setup_addfiles(tmp_path: Path, file_name: str = "test.txt", package: str = "mypkg"):
    home_dir = tmp_path / "home"
    dotfiles_dir = tmp_path / "dotfiles"
    profile_name = "default"

    home_dir.mkdir()
    dotfiles_dir.mkdir()
    (home_dir / file_name).write_text("hello")

    # Use a MagicMock instead of a real RollbackJournal
    logbook = MagicMock()
    logbook.add_entry = MagicMock()
    logbook.save = MagicMock()

    file = home_dir / file_name

    return AddFiles(
        profile_name=profile_name,
        home_dir=home_dir,
        dotfiles_dir=dotfiles_dir,
        file=file,
        package=package,
        logbook=logbook,
    )


# ============================================================
# Property Tests
# ============================================================


def test_is_dir_property(tmp_path: Path):
    addfiles = setup_addfiles(tmp_path)
    assert not addfiles.is_dir
    dir_file = addfiles.home_dir / "dir"
    dir_file.mkdir()
    addfiles.file = dir_file
    assert addfiles.is_dir


def test_package_exists_property(tmp_path: Path):
    addfiles = setup_addfiles(tmp_path)
    assert not addfiles.package_exists
    (addfiles.profile_root / addfiles.package).mkdir(parents=True)
    assert addfiles.package_exists


def test_profile_root_property(tmp_path: Path):
    addfiles = setup_addfiles(tmp_path)
    expected = (
        addfiles.dotfiles_dir
        / InternalFileSystemObject.PROFILES.value
        / addfiles.profile_name
    )
    assert addfiles.profile_root == expected


def test_is_file_in_package_property(tmp_path: Path):
    addfiles = setup_addfiles(tmp_path)
    assert not addfiles.is_file_in_package
    addfiles.destination.parent.mkdir(parents=True)
    addfiles.destination.write_text("collision")
    assert addfiles.is_file_in_package


def test_destination_property(tmp_path: Path):
    addfiles = setup_addfiles(tmp_path)
    rel_path = addfiles.file.relative_to(addfiles.home_dir)
    expected = addfiles.profile_root / addfiles.package / rel_path
    assert addfiles.destination == expected


# ============================================================
# Validation Tests
# ============================================================


def test_validate_home_dir_error(tmp_path: Path):
    addfiles = setup_addfiles(tmp_path)
    addfiles.file = addfiles.home_dir
    with pytest.raises(TargetFileIsHomeError):
        addfiles.validate()


def test_validate_dotfiles_dir_error(tmp_path: Path):
    addfiles = setup_addfiles(tmp_path)
    addfiles.file = addfiles.dotfiles_dir
    with pytest.raises(TargetFileIsDotfilesDirError):
        addfiles.validate()


def test_validate_symlink_error(tmp_path: Path):
    addfiles = setup_addfiles(tmp_path)
    symlink = addfiles.home_dir / "link.txt"
    symlink.symlink_to(addfiles.file)
    addfiles.input_file = symlink
    with pytest.raises(SymlinkNotSupportedError):
        addfiles.validate()


def test_validate_missing_file_error(tmp_path: Path):
    addfiles = setup_addfiles(tmp_path)
    addfiles.file.unlink()
    with pytest.raises(FileDoesNotExistError):
        addfiles.validate()


def test_validate_not_subpath_error(tmp_path: Path):
    addfiles = setup_addfiles(tmp_path)
    outside = tmp_path / "outside.txt"
    outside.write_text("oops")
    addfiles.file = outside
    with pytest.raises(IsNotASubPathError):
        addfiles.validate()


def test_validate_empty_package_error(tmp_path: Path):
    addfiles = setup_addfiles(tmp_path, package="")
    with pytest.raises(InvalidPackageNameError):
        addfiles.validate()


def test_validate_reserved_package_error(tmp_path: Path):
    reserved = InternalFileSystemObject.PACKAGES.value
    addfiles = setup_addfiles(tmp_path, package=reserved)
    with pytest.raises(InvalidPackageNameError):
        addfiles.validate()


def test_validate_collision_error(tmp_path: Path):
    addfiles = setup_addfiles(tmp_path)
    addfiles.destination.parent.mkdir(parents=True)
    addfiles.destination.write_text("collision")
    with pytest.raises(FileNameCollidingError):
        addfiles.validate()


def test_validate_success(tmp_path: Path):
    addfiles = setup_addfiles(tmp_path)
    addfiles.validate()  # should not raise


# ============================================================
# Package Management Tests
# ============================================================


def test_create_and_delete_package(tmp_path: Path):
    addfiles = setup_addfiles(tmp_path)
    addfiles.create_package()
    pkg_path = addfiles.profile_root / addfiles.package
    assert pkg_path.exists()
    with patch(
        "dotman.core.add.FileSystemUtil.delete_empty_package",
        return_value=ExitCode.SUCCESS,
    ) as mock_delete:
        result = addfiles.delete_empty_package()
        assert result == ExitCode.SUCCESS
        mock_delete.assert_called_once_with(addfiles.profile_root, addfiles.destination)


def test_delete_package_with_files(tmp_path: Path):
    addfiles = setup_addfiles(tmp_path)
    addfiles.create_package()
    pkg_path = addfiles.profile_root / addfiles.package
    (pkg_path / "file.txt").write_text("keep me")

    with patch(
        "dotman.core.add.FileSystemUtil.delete_empty_package",
        return_value=ExitCode.INVALID_ARGUMENTS,
    ) as mock_delete:
        result = addfiles.delete_empty_package()
        assert result == ExitCode.INVALID_ARGUMENTS
        mock_delete.assert_called_once_with(addfiles.profile_root, addfiles.destination)


# ============================================================
# File Move Tests
# ============================================================


def test_move_file_to_dotfiles_calls_logbook(tmp_path: Path):
    addfiles = setup_addfiles(tmp_path)
    with (
        patch.object(addfiles.log_book, "add_entry") as mock_add,
        patch.object(addfiles.log_book, "save") as mock_save,
    ):
        result = addfiles.move_file_to_dotfiles()
        assert result == ExitCode.SUCCESS
        mock_add.assert_called_once_with(addfiles.file, addfiles.destination)
        mock_save.assert_called_once()


def test_file_exists_in_package(tmp_path: Path):
    addfiles = setup_addfiles(tmp_path)
    addfiles.move_file_to_dotfiles()
    assert addfiles.file_exists_in_package()


def test_has_files_in_package(tmp_path: Path, monkeypatch: MonkeyPatch):
    addfiles = setup_addfiles(tmp_path)
    pkg_path = addfiles.profile_root / addfiles.package
    pkg_path.mkdir(parents=True)
    (pkg_path / "file.txt").write_text("data")

    # Monkeypatch FileSystemUtil to return True
    monkeypatch.setattr("dotman.core.utils.fs.FileSystemUtil", lambda: lambda p: True)
    assert addfiles.has_files_in_package()


# ============================================================
# Symlink Validation Tests
# ============================================================


def test_non_directory_returns_empty(tmp_path: Path):
    addfiles = setup_addfiles(tmp_path)
    checks = addfiles.validate_directory_symlinks()
    assert checks == []


def test_directory_no_symlinks(tmp_path: Path):
    addfiles = setup_addfiles(tmp_path)
    dir_path = addfiles.home_dir / "dir"
    dir_path.mkdir()
    (dir_path / "regular.txt").write_text("data")

    addfiles.file = dir_path
    checks = addfiles.validate_directory_symlinks()
    assert checks == []


def test_broken_symlink(tmp_path: Path):
    addfiles = setup_addfiles(tmp_path)
    dir_path = addfiles.home_dir / "dir"
    dir_path.mkdir()
    broken = dir_path / "broken_link.txt"
    broken.symlink_to(dir_path / "missing.txt")

    addfiles.file = dir_path
    checks = addfiles.validate_directory_symlinks()
    assert any(
        c.status == SymlinkStatus.ERROR and "broken symlink" in c.message
        for c in checks
    )


def test_symlink_loop_runtimeerror(tmp_path, monkeypatch):
    addfiles = setup_addfiles(tmp_path)
    dir_path = addfiles.home_dir / "dir"
    dir_path.mkdir()
    symlink = dir_path / "loop.txt"
    symlink.symlink_to(dir_path)

    addfiles.file = dir_path

    # Save original resolve
    orig_resolve = Path.resolve

    def fake_resolve(self, strict=True):
        if self == symlink:
            raise RuntimeError("loop")
        return orig_resolve(self)

    monkeypatch.setattr(Path, "resolve", fake_resolve)

    checks = addfiles.validate_directory_symlinks()
    assert any(c.status == SymlinkStatus.ERROR and "loop" in c.message for c in checks)


def test_symlink_loop_oserror(tmp_path, monkeypatch):
    addfiles = setup_addfiles(tmp_path)
    dir_path = addfiles.home_dir / "dir"
    dir_path.mkdir()
    symlink = dir_path / "loop_os.txt"
    symlink.symlink_to(dir_path)

    addfiles.file = dir_path

    # Save original resolve
    orig_resolve = Path.resolve

    def fake_resolve(self, strict=True):
        if self == symlink:
            raise OSError("bad symlink")
        return orig_resolve(self)

    monkeypatch.setattr(Path, "resolve", fake_resolve)

    checks = addfiles.validate_directory_symlinks()
    assert any(c.status == SymlinkStatus.ERROR and "loop" in c.message for c in checks)


def test_symlink_points_outside_root(tmp_path: Path):
    addfiles = setup_addfiles(tmp_path)
    dir_path = addfiles.home_dir / "dir"
    dir_path.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("data")
    symlink = dir_path / "link_outside.txt"
    symlink.symlink_to(outside)

    addfiles.file = dir_path
    checks = addfiles.validate_directory_symlinks()
    assert any(
        c.status == SymlinkStatus.ERROR and "points outside" in c.message
        for c in checks
    )


def test_symlink_points_inside_root(tmp_path: Path):
    addfiles = setup_addfiles(tmp_path)
    dir_path = addfiles.home_dir / "dir"
    dir_path.mkdir()
    target = dir_path / "target.txt"
    target.write_text("data")
    symlink = dir_path / "link_inside.txt"
    symlink.symlink_to(target)

    addfiles.file = dir_path
    checks = addfiles.validate_directory_symlinks()
    assert any(
        c.status == SymlinkStatus.OK and "points inside" in c.message for c in checks
    )
