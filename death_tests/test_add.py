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


class BaseAddServiceTest:
    """Shared setup and helpers for AddService tests."""

    @pytest.fixture(autouse=True)
    def _setup(self, lab: LabPaths):
        self.lab = lab
        self.home = lab.home
        self.dotfiles = lab.dotfiles_dir
        self.profile = lab.profile

    def make_service(self, file: Path, package: str = "testpkg") -> AddService:
        return AddService(
            file=file,
            package=package,
            home_dir=self.home,
            dotfiles_dir=self.dotfiles,
            profile=self.profile,
        )


class TestValidation(BaseAddServiceTest):
    def test_file_not_exists(self):
        fake_file = self.home / "ghost.txt"
        service = self.make_service(fake_file)
        service.load()
        assert service.service_validate() == AddErrors.FileNotExists

    def test_file_is_directory(self):
        target = self.home / "real"
        target.mkdir()
        service = self.make_service(target)
        service.load()
        assert service.is_dir

    def test_has_files_in_package(self):
        file = self.home / "real.txt"
        file.write_text("hello")
        service = self.make_service(file)
        service.load()
        assert service.service_validate() is None
        service.create_reuse_package()
        service.service_add_file()
        assert service.add_files.has_files_in_package()

    def test_file_is_symlink(self):
        target = self.home / "real.txt"
        target.write_text("hello")
        symlink = self.home / "link.txt"
        symlink.symlink_to(target)
        service = self.make_service(symlink)
        service.load()
        assert service.service_validate() == AddErrors.FileIsSymLink

    @pytest.mark.parametrize("pkg_name", ["packages", ""])
    def test_invalid_package_name(self, pkg_name: str):
        file = self.home / "file.txt"
        file.write_text("hello")
        service = self.make_service(file, package=pkg_name)
        service.load()
        assert service.service_validate() == AddErrors.InvalidPackage

    @pytest.mark.parametrize(
        "pkg_name",
        ["../testpkg", "../../testpkg", "/testpkg", "../../../testpkg", "     "],
    )
    def test_suspicious_package_name(self, pkg_name: str):
        file = self.home / "file.txt"
        file.write_text("hello")
        service = self.make_service(file, package=pkg_name)
        service.load()
        assert all(char not in str(service.package) for char in (" ", "/", "."))

    def test_target_is_home(self):
        service = self.make_service(self.home)
        service.load()
        assert service.service_validate() == AddErrors.TargetIsHome

    def test_target_is_dotfiles_dir(self):
        service = self.make_service(self.dotfiles)
        service.load()
        assert service.service_validate() == AddErrors.TargetIsDotfilesDir


class TestAddOperations(BaseAddServiceTest):
    def test_file_name_collision(self):
        file = self.home / "file.txt"
        file.write_text("hello")
        service = self.make_service(file)
        service.load()
        assert service.service_validate() is None

        # First add should succeed
        service.service_add_file()

        # Second add should collide
        file.write_text("hello")
        service2 = self.make_service(file)
        service2.load()
        assert service2.service_validate() == AddErrors.FileNameCollidingError

    def test_add_file_success(self):
        file = self.home / "ok.txt"
        file.write_text("hello")
        service = self.make_service(file)
        service.load()
        assert service.service_validate() is None
        result = service.service_add_file()
        assert result == 1
        assert (self.dotfiles / PROFILES / self.profile / "testpkg" / "ok.txt").exists()
        assert not file.exists()

    def test_add_directory_success(self):
        dirpath = self.home / "mydir"
        dirpath.mkdir()
        nested = dirpath / "nested.txt"
        nested.write_text("hello")
        service = self.make_service(dirpath)
        service.load()
        assert service.service_validate() is None
        result = service.service_add_file()
        assert result == 1
        assert (
            self.dotfiles / PROFILES / self.profile / "testpkg" / "mydir" / "nested.txt"
        ).exists()
        assert not nested.exists()

    def test_file_outside_home_is_rejected(self, tmp_path: Path):
        outside_file = tmp_path / "outside.txt"
        outside_file.write_text("hello")
        service = AddService(
            file=outside_file,
            package="testpkg",
            home_dir=self.home,
            dotfiles_dir=self.dotfiles,
            profile=self.profile,
        )
        service.load()
        assert service.service_validate() == AddErrors.NotASubPath

    def test_file_exists_in_package(self):
        file = self.home / "file.txt"
        file.write_text("hello")
        service = self.make_service(file, package="testpkg")
        service.load()
        assert service.service_validate() is None
        service.service_add_file()

        file.write_text("hello")
        service2 = self.make_service(file, package="testpkg")
        service2.load()
        assert service2.add_files.file_exists_in_package() is True

    def test_sanitized_package_name_is_used_for_destination(self):
        file = self.home / "settings.toml"
        file.write_text("hello")
        service = self.make_service(file, package="My Package.Name")
        service.load()
        assert service.service_validate() is None
        assert service.service_add_file() == 1
        assert (
            self.dotfiles
            / PROFILES
            / self.profile
            / "my_package_name"
            / "settings.toml"
        ).exists()

    def test_existing_destination_symlink_is_collision(self):
        file = self.home / "link-target.txt"
        file.write_text("hello")
        package_dir = self.dotfiles / PROFILES / self.profile / "testpkg"
        package_dir.parent.mkdir(parents=True, exist_ok=True)
        package_dir.mkdir()
        existing_target = self.home / "existing.txt"
        existing_target.write_text("existing")
        (package_dir / "link-target.txt").symlink_to(existing_target)

        service = self.make_service(file)
        service.load()
        assert service.service_validate() == AddErrors.FileNameCollidingError

    def test_existing_destination_directory_is_collision(self):
        dirpath = self.home / "config"
        dirpath.mkdir()
        (dirpath / "file.txt").write_text("hello")
        (self.dotfiles / PROFILES / self.profile / "testpkg" / "config").mkdir(
            parents=True
        )

        service = self.make_service(dirpath)
        service.load()
        assert service.service_validate() == AddErrors.FileNameCollidingError

    def test_create_reuse_package_creates_then_reuses(self):
        file = self.home / "file.txt"
        file.write_text("hello")
        service = self.make_service(file)
        service.load()

        assert service.create_reuse_package() is False
        assert (self.dotfiles / PROFILES / self.profile / "testpkg").is_dir()
        assert service.create_reuse_package() is True


class TestSymlinkChecks(BaseAddServiceTest):
    def test_directory_internal_symlink_is_ok(self):
        dirpath = self.home / "mydir"
        dirpath.mkdir()
        target = dirpath / "target.txt"
        target.write_text("hello")
        (dirpath / "link.txt").symlink_to(target)

        service = self.make_service(dirpath)
        service.load()
        checks = service.validate_directory_symlinks()
        assert len(checks) == 1
        assert checks[0].status == SymlinkStatus.OK

    def test_directory_external_symlink_is_error(self, tmp_path: Path):
        dirpath = self.home / "mydir"
        dirpath.mkdir()
        outside_target = tmp_path / "outside.txt"
        outside_target.write_text("hello")
        (dirpath / "link-outside.txt").symlink_to(outside_target)

        service = self.make_service(dirpath)
        service.load()
        checks = service.validate_directory_symlinks()
        assert len(checks) == 1
        assert checks[0].status == SymlinkStatus.ERROR
        assert "points outside added path" in checks[0].message

    def test_directory_broken_symlink_is_error(self):
        dirpath = self.home / "mydir"
        dirpath.mkdir()
        (dirpath / "broken-link.txt").symlink_to(dirpath / "missing.txt")

        service = self.make_service(dirpath)
        service.load()
        checks = service.validate_directory_symlinks()
        assert len(checks) == 1
        assert checks[0].status == SymlinkStatus.ERROR
        assert checks[0].message == "broken symlink"

    def test_directory_without_symlinks_returns_empty(self):
        dirpath = self.home / "mydir"
        dirpath.mkdir()
        (dirpath / "file.txt").write_text("hello")

        service = self.make_service(dirpath)
        service.load()

        checks = service.validate_directory_symlinks()

        assert checks == []

    def test_regular_file_returns_empty(self):
        file = self.home / "file.txt"
        file.write_text("hello")

        service = self.make_service(file)
        service.load()

        checks = service.validate_directory_symlinks()

        assert checks == []

    def test_nested_internal_symlink_is_ok(self):
        dirpath = self.home / "mydir"

        (dirpath / "a").mkdir(parents=True)
        (dirpath / "b").mkdir(parents=True)

        target = dirpath / "a" / "target.txt"
        target.write_text("hello")

        (dirpath / "b" / "link.txt").symlink_to(target)

        service = self.make_service(dirpath)
        service.load()

        checks = service.validate_directory_symlinks()

        assert len(checks) == 1
        assert checks[0].status == SymlinkStatus.OK

    def test_symlink_loop_is_error(self):
        dirpath = self.home / "mydir"
        dirpath.mkdir()

        loop = dirpath / "loop"
        loop.symlink_to(loop)

        service = self.make_service(dirpath)
        service.load()

        checks = service.validate_directory_symlinks()

        assert len(checks) == 1
        assert checks[0].status == SymlinkStatus.ERROR
        assert checks[0].message == "symlink loop"


class TestNestedAndRestore(BaseAddServiceTest):
    def test_nested_path_preserved(self):
        nested = self.home / ".config" / "nvim"
        nested.mkdir(parents=True, exist_ok=True)
        file = nested / "init.lua"
        file.write_text("hello")

        service = self.make_service(file, package="nvim")
        service.load()
        assert service.service_validate() is None
        service.service_add_file()

        assert (
            self.dotfiles
            / PROFILES
            / self.profile
            / "nvim"
            / ".config"
            / "nvim"
            / "init.lua"
        ).exists()

    def test_restore_removes_empty_package(self):
        file = self.home / "file.txt"
        file.write_text("hello")
        service = self.make_service(file, package="pkg")
        service.load()
        assert service.service_validate() is None

        service.create_reuse_package()
        service.service_add_file()
        service.restore_files()
        service.add_files.delete_empty_package()

        assert not (self.dotfiles / PROFILES / self.profile / "pkg").exists()

    def test_restore_not_deletes_empty_package_if_other_directory_has_files(self):
        file = self.home / "file.txt"
        file.write_text("hello")
        service = self.make_service(file, package="pkg")
        service.load()
        assert service.service_validate() is None

        assert service.create_reuse_package() is False
        service.service_add_file()

        assert service.add_files.delete_empty_package() == 1

    def test_restore_returns_file_to_original_location(self):
        file = self.home / "file.txt"
        file.write_text("hello")
        service = self.make_service(file, package="pkg")
        service.load()
        assert service.service_validate() is None

        service.create_reuse_package()
        service.service_add_file()
        service.restore_files()

        assert file.exists()
        assert not (
            self.dotfiles / PROFILES / self.profile / "pkg" / "file.txt"
        ).exists()

        service.add_files.delete_empty_package()
        assert not (self.dotfiles / PROFILES / self.profile / "pkg").exists()


class TestMultipleFiles(BaseAddServiceTest):
    def test_multiple_files_same_package(self):
        f1 = self.home / "a.txt"
        f2 = self.home / "b.txt"
        f1.write_text("a")
        f2.write_text("b")

        s1 = self.make_service(f1, package="pkg")
        s1.load()
        assert s1.service_validate() is None
        s1.service_add_file()

        s2 = self.make_service(f2, package="pkg")
        s2.load()
        assert s2.service_validate() is None
        s2.service_add_file()

        assert (self.dotfiles / PROFILES / self.profile / "pkg" / "a.txt").exists()
        assert (self.dotfiles / PROFILES / self.profile / "pkg" / "b.txt").exists()

    def test_empty_file(self):
        file = self.home / "empty.txt"
        file.touch()
        service = self.make_service(file, package="pkg")
        service.load()
        assert service.service_validate() is None

    def test_directory_with_multiple_files(self):
        config = self.home / ".config"
        config.mkdir()
        (config / "a.txt").write_text("a")
        (config / "b.txt").write_text("b")
        (config / "c.txt").write_text("c")

        service = self.make_service(config, package="config")
        service.load()
        assert service.service_validate() is None
        service.service_add_file()

        assert (
            self.dotfiles / PROFILES / self.profile / "config" / ".config" / "a.txt"
        ).exists()
        assert (
            self.dotfiles / PROFILES / self.profile / "config" / ".config" / "b.txt"
        ).exists()
        assert (
            self.dotfiles / PROFILES / self.profile / "config" / ".config" / "c.txt"
        ).exists()

    def test_dotdot_path_inside_home_is_allowed(self):
        file = self.home / "file.txt"
        file.write_text("hello")
        weird_path = self.home / ".." / "home" / "file.txt"
        service = self.make_service(weird_path)
        service.load()
        assert service.service_validate() is None
