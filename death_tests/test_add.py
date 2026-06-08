# ruff: noqa: S101

from dataclasses import dataclass
from pathlib import Path

import pytest

from dotman.core.add import SymlinkStatus
from dotman.core.service.add_service import AddErrors, AddService

PROFILES = "profiles"


@dataclass
class LabPaths:
    home: Path
    dotfiles_dir: Path
    profile: str


@pytest.fixture
def lab(tmp_path: Path) -> LabPaths:
    home = tmp_path / "home"
    dotfiles = tmp_path / "dotfiles"

    profile = "default"

    home.mkdir()
    dotfiles.mkdir()

    return LabPaths(home=home, dotfiles_dir=dotfiles, profile=profile)


def test_file_not_exists(lab: LabPaths):
    home, dotfiles = lab.home, lab.dotfiles_dir
    fake_file = home / "ghost.txt"
    package = "testpkg"
    service = AddService(
        file=fake_file,
        package=package,
        home_dir=home,
        dotfiles_dir=dotfiles,
        profile=lab.profile,
    )
    service.load()
    assert service.service_validate() == AddErrors.FileNotExists


def test_file_is_symlink(lab: LabPaths):
    home, dotfiles = lab.home, lab.dotfiles_dir
    target = home / "real.txt"
    target.write_text("hello")
    symlink = home / "link.txt"
    symlink.symlink_to(target)
    service = AddService(
        file=symlink,
        package="testpkg",
        home_dir=home,
        dotfiles_dir=dotfiles,
        profile=lab.profile,
    )
    service.load()
    assert service.service_validate() == AddErrors.FileIsSymLink


class TestInvalidPackageName:
    @pytest.mark.parametrize(
        "pkg_name",
        [
            "packages",
            "",
        ],
    )
    def test_invalid_package_name(self, lab: LabPaths, pkg_name: str):
        home, dotfiles = lab.home, lab.dotfiles_dir
        file = home / "file.txt"
        file.write_text("hello")
        service = AddService(
            file=file,
            package=pkg_name,
            home_dir=home,
            dotfiles_dir=dotfiles,
            profile=lab.profile,
        )
        service.load()
        assert service.service_validate() == AddErrors.InvalidPackage

    @pytest.mark.parametrize(
        "pkg_name",
        [
            "../testpkg",
            "../../testpkg",
            "/testpkg",
            "../../../testpkg",
            "     ",
        ],
    )
    def test_suspicious_package_name(self, lab: LabPaths, pkg_name: str):
        home, dotfiles = lab.home, lab.dotfiles_dir
        file = home / "file.txt"
        file.write_text("hello")
        service = AddService(
            file=file,
            package=pkg_name,
            home_dir=home,
            dotfiles_dir=dotfiles,
            profile=lab.profile,
        )
        service.load()
        assert all(char not in str(service.package) for char in (" ", "/", "."))


def test_target_is_home(lab: LabPaths):
    home, dotfiles = lab.home, lab.dotfiles_dir
    service = AddService(
        file=home,
        package="testpkg",
        home_dir=home,
        dotfiles_dir=dotfiles,
        profile=lab.profile,
    )
    service.load()
    assert service.service_validate() == AddErrors.TargetIsHome


def test_target_is_dotfiles_dir(lab: LabPaths):
    home, dotfiles = lab.home, lab.dotfiles_dir
    service = AddService(
        file=dotfiles,
        package="testpkg",
        home_dir=home,
        dotfiles_dir=dotfiles,
        profile=lab.profile,
    )
    service.load()
    assert service.service_validate() == AddErrors.TargetIsDotfilesDir


def test_file_name_collision(lab: LabPaths):
    home, dotfiles = lab.home, lab.dotfiles_dir
    file = home / "file.txt"
    file.write_text("hello")
    service = AddService(
        file=file,
        package="testpkg",
        home_dir=home,
        dotfiles_dir=dotfiles,
        profile=lab.profile,
    )
    service.load()
    assert service.service_validate() is None
    # First add should succeed
    service.service_add_file()
    # Second add should collide
    file.write_text("hello")
    service2 = AddService(
        file=file,
        package="testpkg",
        home_dir=home,
        dotfiles_dir=dotfiles,
        profile=lab.profile,
    )
    service2.load()
    assert service2.service_validate() == AddErrors.FileNameCollidingError


def test_add_file_success(lab: LabPaths):
    home, dotfiles = lab.home, lab.dotfiles_dir
    file = home / "ok.txt"
    file.write_text("hello")
    service = AddService(
        file=file,
        package="testpkg",
        home_dir=home,
        dotfiles_dir=dotfiles,
        profile=lab.profile,
    )
    service.load()
    assert service.service_validate() is None
    result = service.service_add_file()
    assert result == 1
    assert (dotfiles / PROFILES / lab.profile / "testpkg" / "ok.txt").exists()
    assert not file.exists()


def test_add_directory_success(lab: LabPaths):
    home, dotfiles = lab.home, lab.dotfiles_dir
    dirpath = home / "mydir"
    dirpath.mkdir()
    file = dirpath / "nested.txt"
    file.write_text("hello")
    service = AddService(
        file=dirpath,
        package="testpkg",
        home_dir=home,
        dotfiles_dir=dotfiles,
        profile=lab.profile,
    )
    service.load()
    assert service.service_validate() is None
    result = service.service_add_file()
    assert result == 1
    assert (dotfiles / PROFILES / lab.profile / "testpkg" / "mydir" / "nested.txt").exists()
    assert not file.exists()


def test_file_outside_home_is_rejected(lab: LabPaths, tmp_path: Path):
    outside_file = tmp_path / "outside.txt"
    outside_file.write_text("hello")

    service = AddService(
        file=outside_file,
        package="testpkg",
        home_dir=lab.home,
        dotfiles_dir=lab.dotfiles_dir,
        profile=lab.profile,
    )
    service.load()

    assert service.service_validate() == AddErrors.NotASubPath


def test_sanitized_package_name_is_used_for_destination(lab: LabPaths):
    file = lab.home / "settings.toml"
    file.write_text("hello")

    service = AddService(
        file=file,
        package="My Package.Name",
        home_dir=lab.home,
        dotfiles_dir=lab.dotfiles_dir,
        profile=lab.profile,
    )
    service.load()

    assert service.service_validate() is None
    assert service.service_add_file() == 1
    assert (lab.dotfiles_dir / PROFILES / lab.profile / "my_package_name" / "settings.toml").exists()


def test_existing_destination_symlink_is_collision(lab: LabPaths):
    file = lab.home / "link-target.txt"
    file.write_text("hello")
    package_dir = lab.dotfiles_dir / PROFILES / lab.profile / "testpkg"
    package_dir.parent.mkdir(parents=True, exist_ok=True)
    package_dir.mkdir()
    existing_target = lab.home / "existing.txt"
    existing_target.write_text("existing")
    (package_dir / "link-target.txt").symlink_to(existing_target)

    service = AddService(
        file=file,
        package="testpkg",
        home_dir=lab.home,
        dotfiles_dir=lab.dotfiles_dir,
        profile=lab.profile,
    )
    service.load()

    assert service.service_validate() == AddErrors.FileNameCollidingError


def test_existing_destination_directory_is_collision(lab: LabPaths):
    dirpath = lab.home / "config"
    dirpath.mkdir()
    (dirpath / "file.txt").write_text("hello")
    (lab.dotfiles_dir / PROFILES / lab.profile / "testpkg" / "config").mkdir(parents=True)

    service = AddService(
        file=dirpath,
        package="testpkg",
        home_dir=lab.home,
        dotfiles_dir=lab.dotfiles_dir,
        profile=lab.profile,
    )
    service.load()

    assert service.service_validate() == AddErrors.FileNameCollidingError


def test_create_reuse_package_creates_then_reuses(lab: LabPaths):
    file = lab.home / "file.txt"
    file.write_text("hello")
    service = AddService(
        file=file,
        package="testpkg",
        home_dir=lab.home,
        dotfiles_dir=lab.dotfiles_dir,
        profile=lab.profile,
    )
    service.load()

    assert service.create_reuse_package() is False
    assert (lab.dotfiles_dir / PROFILES / lab.profile / "testpkg").is_dir()
    assert service.create_reuse_package() is True


def test_directory_internal_symlink_is_ok(lab: LabPaths):
    dirpath = lab.home / "mydir"
    dirpath.mkdir()
    target = dirpath / "target.txt"
    target.write_text("hello")
    (dirpath / "link.txt").symlink_to(target)

    service = AddService(
        file=dirpath,
        package="testpkg",
        home_dir=lab.home,
        dotfiles_dir=lab.dotfiles_dir,
        profile=lab.profile,
    )
    service.load()
    checks = service.validate_directory_symlinks()

    assert len(checks) == 1
    assert checks[0].status == SymlinkStatus.OK


def test_directory_external_symlink_is_error(lab: LabPaths, tmp_path: Path):
    dirpath = lab.home / "mydir"
    dirpath.mkdir()
    outside_target = tmp_path / "outside.txt"
    outside_target.write_text("hello")
    (dirpath / "link-outside.txt").symlink_to(outside_target)

    service = AddService(
        file=dirpath,
        package="testpkg",
        home_dir=lab.home,
        dotfiles_dir=lab.dotfiles_dir,
        profile=lab.profile,
    )
    service.load()
    checks = service.validate_directory_symlinks()

    assert len(checks) == 1
    assert checks[0].status == SymlinkStatus.ERROR
    assert "points outside added path" in checks[0].message


def test_directory_broken_symlink_is_error(lab: LabPaths):
    dirpath = lab.home / "mydir"
    dirpath.mkdir()
    (dirpath / "broken-link.txt").symlink_to(dirpath / "missing.txt")

    service = AddService(
        file=dirpath,
        package="testpkg",
        home_dir=lab.home,
        dotfiles_dir=lab.dotfiles_dir,
        profile=lab.profile,
    )
    service.load()
    checks = service.validate_directory_symlinks()

    assert len(checks) == 1
    assert checks[0].status == SymlinkStatus.ERROR
    assert checks[0].message == "broken symlink"


def test_nested_path_preserved(lab: LabPaths):
    nested = lab.home / ".config" / "nvim"
    nested.mkdir(parents=True, exist_ok=True)

    file = nested / "init.lua"
    file.write_text("hello")

    service = AddService(
        file=file,
        package="nvim",
        home_dir=lab.home,
        dotfiles_dir=lab.dotfiles_dir,
        profile=lab.profile,
    )
    service.load()

    assert service.service_validate() is None
    service.service_add_file()

    assert (lab.dotfiles_dir / PROFILES / lab.profile / "nvim" / ".config" / "nvim" / "init.lua").exists()


def test_restore_removes_empty_package(lab: LabPaths):
    file = lab.home / "file.txt"
    file.write_text("hello")

    service = AddService(
        file=file,
        package="pkg",
        home_dir=lab.home,
        dotfiles_dir=lab.dotfiles_dir,
        profile=lab.profile,
    )
    service.load()
    assert service.service_validate() is None

    service.create_reuse_package()
    service.service_add_file()

    service.restore_files()

    service.add_files.delete_empty_package()

    assert not (lab.dotfiles_dir / PROFILES / lab.profile / "pkg").exists()


def test_restore_returns_file_to_original_location(lab: LabPaths):
    file = lab.home / "file.txt"
    file.write_text("hello")

    service = AddService(
        file=file,
        package="pkg",
        home_dir=lab.home,
        dotfiles_dir=lab.dotfiles_dir,
        profile=lab.profile,
    )
    service.load()
    assert service.service_validate() is None

    service.create_reuse_package()
    service.service_add_file()

    service.restore_files()

    assert file.exists()
    assert not (lab.dotfiles_dir / PROFILES / lab.profile / "pkg" / "file.txt").exists()

    service.add_files.delete_empty_package()
    # Package should be removed since it's empty
    assert not (lab.dotfiles_dir / PROFILES / lab.profile / "pkg").exists()


def test_multiple_files_same_package(lab: LabPaths):
    f1 = lab.home / "a.txt"
    f2 = lab.home / "b.txt"

    f1.write_text("a")
    f2.write_text("b")

    s1 = AddService(
        file=f1,
        package="pkg",
        home_dir=lab.home,
        dotfiles_dir=lab.dotfiles_dir,
        profile=lab.profile,
    )
    s1.load()
    assert s1.service_validate() is None
    s1.service_add_file()

    s2 = AddService(
        file=f2,
        package="pkg",
        home_dir=lab.home,
        dotfiles_dir=lab.dotfiles_dir,
        profile=lab.profile,
    )
    s2.load()
    assert s2.service_validate() is None
    s2.service_add_file()

    assert (lab.dotfiles_dir / PROFILES / lab.profile / "pkg" / "a.txt").exists()
    assert (lab.dotfiles_dir / PROFILES / lab.profile / "pkg" / "b.txt").exists()


def test_empty_file(lab: LabPaths):
    file = lab.home / "empty.txt"
    file.touch()

    service = AddService(
        file=file,
        package="pkg",
        home_dir=lab.home,
        dotfiles_dir=lab.dotfiles_dir,
        profile=lab.profile,
    )
    service.load()

    assert service.service_validate() is None


def test_directory_with_multiple_files(lab: LabPaths):
    config = lab.home / ".config"
    config.mkdir()

    (config / "a.txt").write_text("a")
    (config / "b.txt").write_text("b")
    (config / "c.txt").write_text("c")

    service = AddService(
        file=config,
        package="config",
        home_dir=lab.home,
        dotfiles_dir=lab.dotfiles_dir,
        profile=lab.profile,
    )
    service.load()

    assert service.service_validate() is None

    service.service_add_file()

    assert (lab.dotfiles_dir / PROFILES / lab.profile / "config" / ".config" / "a.txt").exists()
    assert (lab.dotfiles_dir / PROFILES / lab.profile / "config" / ".config" / "b.txt").exists()
    assert (lab.dotfiles_dir / PROFILES / lab.profile / "config" / ".config" / "c.txt").exists()


def test_dotdot_path_inside_home_is_allowed(
    lab: LabPaths,
):
    file = lab.home / "file.txt"
    file.write_text("hello")

    weird_path = lab.home / ".." / "home" / "file.txt"

    service = AddService(
        file=weird_path,
        package="testpkg",
        home_dir=lab.home,
        dotfiles_dir=lab.dotfiles_dir,
        profile=lab.profile,
    )
    service.load()

    assert service.service_validate() is None
