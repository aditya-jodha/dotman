# ruff: noqa: S101

from dataclasses import dataclass
from pathlib import Path

import pytest

from dotman.core.doctor import Doctor, DoctorStatus, SymlinkStatus


@dataclass
class LabPaths:
    home: Path
    dotfiles_dir: Path


@pytest.fixture
def lab(tmp_path: Path) -> LabPaths:
    home = tmp_path / "home"
    dotfiles = tmp_path / "dotfiles"

    home.mkdir()
    dotfiles.mkdir()

    return LabPaths(home=home, dotfiles_dir=dotfiles)


class TestPermissionCheck:
    def test_doctor_check_permission_dotfiles(self, lab: LabPaths):
        home_pth, dotfile_pth = lab.home, lab.dotfiles_dir
        doctor = Doctor(home_dir=home_pth, dotfile_dir=dotfile_pth, detail=False)

        dotfile_pth.mkdir(exist_ok=True)
        dotfile_pth.chmod(0o555)
        check = doctor.check_permissions_dotfiles()
        assert check.status == DoctorStatus.ERROR

        dotfile_pth.chmod(0o755)
        check = doctor.check_permissions_dotfiles()
        assert check.status == DoctorStatus.OK

    def test_doctor_check_permission_home(self, lab: LabPaths):
        home_pth, dotfiles_pth = lab.home, lab.dotfiles_dir
        doctor = Doctor(home_dir=home_pth, dotfile_dir=dotfiles_pth, detail=False)

        home_pth.mkdir(exist_ok=True)
        home_pth.chmod(0o555)
        check = doctor.check_permissions_home()
        assert check.status == DoctorStatus.ERROR

        home_pth.chmod(0o755)
        check = doctor.check_permissions_home()
        assert check.status == DoctorStatus.OK


class TestSymlink:
    @pytest.fixture(autouse=True)
    def setup(self, lab: LabPaths):
        self.home_dir = lab.home
        self.dotfiles_dir = lab.dotfiles_dir
        self.doctor = Doctor(home_dir=self.home_dir, dotfile_dir=self.dotfiles_dir, detail=False)
        self.home_dir.mkdir(exist_ok=True)
        self.dotfiles_dir.mkdir(exist_ok=True)

    def test_missing_taget(self):
        pkg_dir = self.dotfiles_dir / "testpgk"
        pkg_dir.mkdir(exist_ok=True)
        source_file = pkg_dir / "MISSING_TARGET.txt"
        source_file.touch()

        target_file = self.home_dir / "MISSING_TARGET.txt"

        status = self.doctor.get_symlink_status(source=source_file, target=target_file)
        assert status == SymlinkStatus.MISSING_TARGET

    def test_broken_symlink(self):
        broken_target = self.home_dir / "broken_link.txt"
        link_file = self.home_dir / "link.txt"
        link_file.symlink_to(broken_target)

        status = self.doctor.get_symlink_status(source=Path("not_needed"), target=link_file)
        assert status == SymlinkStatus.BROKEN_SYMLINK

    def test_not_a_symlink(self):
        file = self.home_dir / "pure_file.txt"
        file.touch()

        dotfile_pkg = self.dotfiles_dir / "file"
        dotfile_pkg.mkdir()
        pkg_file = dotfile_pkg / "pure_file.txt"
        pkg_file.touch()

        status = self.doctor.get_symlink_status(source=file, target=pkg_file)
        assert status == SymlinkStatus.NOT_A_SYMLINK

    def test_wrong_source(self):
        correct_file = self.home_dir / "file.txt"
        correct_file.write_text("hello")

        wrong_file = self.home_dir / "foreign_file.txt"
        wrong_file.write_text("world")

        pkg_dir = self.dotfiles_dir / "pkg"
        pkg_dir.mkdir()
        pkg_link = pkg_dir / "file.txt"
        pkg_link.symlink_to(wrong_file)

        status = self.doctor.get_symlink_status(source=correct_file, target=pkg_link)
        assert status == SymlinkStatus.WRONG_SOURCE

    def test_everthing_is_file(self):
        file = self.home_dir / "file.txt"

        pkg_dir = self.dotfiles_dir / "pkg"
        pkg_dir.mkdir()
        pkg_link = pkg_dir / "file.txt"
        pkg_link.touch()
        file.symlink_to(pkg_link)

        status = self.doctor.get_symlink_status(source=pkg_link, target=file)
        assert status == SymlinkStatus.OK
