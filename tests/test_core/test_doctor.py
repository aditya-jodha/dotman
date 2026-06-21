# ruff: noqa: S101
from dataclasses import dataclass
from pathlib import Path

import pytest

from dotman.core.doctor import (
    Doctor,
    DoctorCheck,
    DoctorStatus,
    DoctorStatusName,
    SummeryReport,
    SymlinkStatus,
)


@dataclass
class LabPaths:
    home: Path
    dotfiles_dir: Path
    profile: str
    profile_root: Path


@pytest.fixture
def lab(tmp_path: Path) -> LabPaths:
    home = tmp_path / "home"
    dotfiles = tmp_path / "dotfiles"
    profile = "test_profile"
    home.mkdir()
    profile_root = dotfiles / "profiles" / profile
    profile_root.mkdir(parents=True)
    return LabPaths(
        home=home, dotfiles_dir=dotfiles, profile=profile, profile_root=profile_root
    )


class TestDataClass:
    def test_doctorcheck_as_dict(self):
        check = DoctorCheck("name", DoctorStatus.OK, "message")
        assert check.as_dict() == {"name": "name", "status": "ok", "message": "message"}


class TestPermissions:
    def test_dotfiles_permissions(self, lab: LabPaths):
        doctor = Doctor(lab.profile, lab.home, lab.dotfiles_dir, detail=False)
        lab.dotfiles_dir.chmod(0o555)
        assert doctor.check_permissions_dotfiles().status == DoctorStatus.ERROR
        lab.dotfiles_dir.chmod(0o755)
        assert doctor.check_permissions_dotfiles().status == DoctorStatus.OK

    def test_home_permissions(self, lab: LabPaths):
        doctor = Doctor(lab.profile, lab.home, lab.dotfiles_dir, detail=False)
        lab.home.chmod(0o555)
        assert doctor.check_permissions_home().status == DoctorStatus.ERROR
        lab.home.chmod(0o755)
        assert doctor.check_permissions_home().status == DoctorStatus.OK


class TestIsDotfilesDirValid:
    def test_nonexistent_dotfiles_dir(self, tmp_path: Path):
        home = tmp_path / "home"
        home.mkdir()
        dotfiles = tmp_path / "dotfiles_missing"
        doctor = Doctor("default", home, dotfiles, detail=False)
        check = doctor.is_dotfiles_dir_valid()
        assert check.status == DoctorStatus.ERROR
        assert DoctorStatusName.DOTFILES_DIR.value == check.name
        assert "does not exist" in check.message

    def test_dotfiles_path_is_file(self, tmp_path: Path):
        home = tmp_path / "home"
        home.mkdir()
        dotfiles_file = tmp_path / "dotfiles"
        dotfiles_file.write_text("not a dir")
        doctor = Doctor("default", home, dotfiles_file, detail=False)
        check = doctor.is_dotfiles_dir_valid()
        assert check.status == DoctorStatus.ERROR
        assert "not a directory" in check.message

    def test_dotfiles_dir_is_valid(self, tmp_path: Path):
        home = tmp_path / "home"
        home.mkdir()
        dotfiles = tmp_path / "dotfiles"
        dotfiles.mkdir()
        (dotfiles / "profiles" / "default").mkdir(parents=True)
        doctor = Doctor("default", home, dotfiles, detail=False)
        check = doctor.is_dotfiles_dir_valid()
        assert check.status == DoctorStatus.OK
        assert "is valid"


class TestSymlinkStatus:
    def setup_doctor(self, lab: LabPaths):
        return Doctor(lab.profile, lab.home, lab.dotfiles_dir, detail=False)

    def test_missing_target(self, lab: LabPaths):
        src = lab.profile_root / "file.txt"
        src.touch()
        tgt = lab.home / "file.txt"
        assert (
            self.setup_doctor(lab).get_symlink_status(src, tgt)
            == SymlinkStatus.MISSING_TARGET
        )

    def test_broken_symlink(self, lab: LabPaths):
        broken = lab.home / "ghost.txt"
        link = lab.home / "link.txt"
        link.symlink_to(broken)
        assert (
            self.setup_doctor(lab).get_symlink_status(Path("unused"), link)
            == SymlinkStatus.BROKEN_SYMLINK
        )

    def test_not_a_symlink(self, lab: LabPaths):
        src = lab.home / "pure.txt"
        src.touch()
        tgt = lab.profile_root / "pkg" / "pure.txt"
        tgt.parent.mkdir()
        tgt.touch()
        assert (
            self.setup_doctor(lab).get_symlink_status(src, tgt)
            == SymlinkStatus.NOT_A_SYMLINK
        )

    def test_wrong_source(self, lab: LabPaths):
        correct = lab.home / "file.txt"
        correct.write_text("hello")
        wrong = lab.home / "other.txt"
        wrong.write_text("world")
        link = lab.profile_root / "pkg" / "file.txt"
        link.parent.mkdir()
        link.symlink_to(wrong)
        assert (
            self.setup_doctor(lab).get_symlink_status(correct, link)
            == SymlinkStatus.WRONG_SOURCE
        )

    def test_ok_symlink(self, lab: LabPaths):
        src = lab.profile_root / "pkg" / "file.txt"
        src.parent.mkdir()
        src.touch()
        tgt = lab.home / "file.txt"
        tgt.symlink_to(src)
        assert self.setup_doctor(lab).get_symlink_status(src, tgt) == SymlinkStatus.OK


class TestPackageCheck:
    def test_no_packages_warns(self, lab: LabPaths):
        doctor = Doctor(lab.profile, lab.home, lab.dotfiles_dir, detail=False)
        checks = doctor.package_check()
        assert any("No packages" in c.message for c in checks)

    def test_empty_package_warns(self, lab: LabPaths):
        pkg = lab.profile_root / "pkg1"
        pkg.mkdir()
        doctor = Doctor(lab.profile, lab.home, lab.dotfiles_dir, detail=False)
        checks = doctor.package_check()
        assert any("empty" in c.message for c in checks)


class TestIsSymlinked:
    def test_no_packages_warns(self, tmp_path: Path):
        home = tmp_path / "home"
        home.mkdir()
        dotfiles = tmp_path / "dotfiles"
        dotfiles.mkdir()
        (dotfiles / "profiles" / "default").mkdir(parents=True)
        doctor = Doctor("default", home, dotfiles, detail=False)
        checks = doctor.is_symlinked()
        assert any("No packages" in c.message for c in checks)

    def test_missing_target_warns(self, lab: LabPaths):
        pkg = lab.profile_root / "pkg"
        pkg.mkdir()
        src = pkg / "file.txt"
        src.write_text("hello")
        doctor = Doctor(lab.profile, lab.home, lab.dotfiles_dir, detail=False)
        checks = doctor.is_symlinked()
        assert any("Missing target" in c.message for c in checks)

    def test_broken_symlink_warns(self, lab: LabPaths):
        pkg = lab.profile_root / "pkg"
        pkg.mkdir()
        src = pkg / "file.txt"
        src.write_text("hello")
        tgt = lab.home / "file.txt"
        tgt.symlink_to(lab.home / "nonexistent.txt")
        doctor = Doctor(lab.profile, lab.home, lab.dotfiles_dir, detail=False)
        checks = doctor.is_symlinked()
        assert any("Broken symlink" in c.message for c in checks)

    def test_not_a_symlink_warns(self, lab: LabPaths):
        pkg = lab.profile_root / "pkg"
        pkg.mkdir()
        src = pkg / "file.txt"
        src.write_text("hello")
        tgt = lab.home / "file.txt"
        tgt.write_text("world")
        doctor = Doctor(lab.profile, lab.home, lab.dotfiles_dir, detail=False)
        checks = doctor.is_symlinked()
        assert any("Expected symlink" in c.message for c in checks)

    def test_wrong_source_warns(self, lab: LabPaths):
        pkg = lab.profile_root / "pkg"
        pkg.mkdir()
        src = pkg / "file.txt"
        src.write_text("hello")
        wrong = lab.home / "wrong.txt"
        wrong.write_text("oops")
        tgt = lab.home / "file.txt"
        tgt.symlink_to(wrong)
        doctor = Doctor(lab.profile, lab.home, lab.dotfiles_dir, detail=False)
        checks = doctor.is_symlinked()
        assert any("Expected" in c.message and "points to" in c.message for c in checks)

    def test_ok_with_detail(self, lab: LabPaths):
        pkg = lab.profile_root / "pkg"
        pkg.mkdir()
        src = pkg / "file.txt"
        src.write_text("hello")
        tgt = lab.home / "file.txt"
        tgt.symlink_to(src)
        doctor = Doctor(lab.profile, lab.home, lab.dotfiles_dir, detail=True)
        checks = doctor.is_symlinked()
        assert any(
            c.status == DoctorStatus.OK and "Link OK" in c.message for c in checks
        )

    def test_all_ok_without_detail_returns_summary_ok(self, lab: LabPaths):
        pkg = lab.profile_root / "pkg"
        pkg.mkdir()
        src = pkg / "file.txt"
        src.write_text("hello")
        tgt = lab.home / "file.txt"
        tgt.symlink_to(src)
        doctor = Doctor(lab.profile, lab.home, lab.dotfiles_dir, detail=False)
        checks = doctor.is_symlinked()
        assert len(checks) == 1
        assert checks[0].status == DoctorStatus.OK
        assert "All files in packages are properly symlinked" in checks[0].message

    def test_is_symlinked_missing_parent_structure(self, tmp_path: Path):
        home = tmp_path / "home"
        home.mkdir()
        dotfiles = tmp_path / "dotfiles"
        dotfiles.mkdir()
        pkg = dotfiles / "profiles" / "default" / "pkg1"
        pkg.mkdir(parents=True)

        # Create a nested folder in pkg
        nested = pkg / "missing_parent"
        nested.mkdir()
        src = nested / "file.txt"
        src.write_text("hello")

        # Note: we do NOT create home/missing_parent
        doctor = Doctor("default", home, dotfiles, detail=False)
        checks = doctor.is_symlinked()
        assert any("Missing parent structure" in c.message for c in checks)


class TestSummaryAndRunAll:
    def test_summary_counts(self, lab: LabPaths):
        doctor = Doctor(lab.profile, lab.home, lab.dotfiles_dir, detail=False)
        checks = [
            DoctorCheck("c1", DoctorStatus.OK, ""),
            DoctorCheck("c2", DoctorStatus.WARN, ""),
            DoctorCheck("c3", DoctorStatus.ERROR, ""),
        ]
        report = doctor.summary(checks)
        assert report.ok == 1 and report.warn == 1 and report.error == 1

    def test_run_all_includes_valid_dir_and_summary(self, lab: LabPaths):
        pkg = lab.profile_root / "pkg1"
        pkg.mkdir()
        doctor = Doctor(lab.profile, lab.home, lab.dotfiles_dir, detail=False)
        checks, report = doctor.run_all()
        assert any(c.name == DoctorStatusName.DOTFILES_DIR.value for c in checks)
        assert isinstance(report, SummeryReport)
