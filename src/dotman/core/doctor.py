import os
from enum import Enum
from pathlib import Path

from dotman.core.config import InternalFileSystemObject


class DoctorStatus(Enum):
    OK = "ok"
    WARN = "warn"
    ERROR = "error"


class SummeryReport:
    def __init__(self, ok: int, warn: int, error: int):
        self.ok = ok
        self.warn = warn
        self.error = error


class DoctorStatusName(Enum):
    """Names of the checks\n
    NOTE: There is one more format of name i.e. "{pkg.name}:{source.relative_to(pkg)}"
    which is not listed here.
    """

    DOTFILES_DIR = "Dotfiles Directory"
    PACKAGE = "Package"
    SYMLINK = "Symlink"


class SymlinkStatus(Enum):
    OK = "ok"
    BROKEN_SYMLINK = "broken_symlink"
    MISSING_TARGET = "missing_target"
    NOT_A_SYMLINK = "not_a_symlink"
    WRONG_SOURCE = "wrong_source"


class DoctorCheck:
    def __init__(self, name: str, status: DoctorStatus, message: str):
        self.name = name
        self.status = status
        self.message = message

    def as_dict(self):
        return {
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
        }


class Doctor:
    def __init__(self, profile_name: str, home_dir: Path, dotfile_dir: Path, detail: bool) -> None:
        self.home_dir = home_dir
        self.profile_name = profile_name
        self.dotfiles_dir = dotfile_dir
        self.detail = detail

        self.packages = []
        self.valid_dir = self.is_dotfiles_dir_valid()
        if self.valid_dir.status == DoctorStatus.OK:
            self.packages = [p for p in (self.dotfiles_dir / "profiles" / self.profile_name).iterdir() if p.is_dir()]

    def is_dotfiles_dir_valid(self) -> DoctorCheck:
        if not self.dotfiles_dir.exists():
            return DoctorCheck(
                name=DoctorStatusName.DOTFILES_DIR.value,
                status=DoctorStatus.ERROR,
                message=f"Dotfiles directory '{self.dotfiles_dir}' does not exist.",
            )
        if not self.dotfiles_dir.is_dir():
            return DoctorCheck(
                name=DoctorStatusName.DOTFILES_DIR.value,
                status=DoctorStatus.ERROR,
                message=f"'{self.dotfiles_dir}' exists but is not a directory.",
            )
        return DoctorCheck(
            name=DoctorStatusName.DOTFILES_DIR.value,
            status=DoctorStatus.OK,
            message=f"Dotfiles directory '{self.dotfiles_dir}' is valid.",
        )

    @staticmethod
    def get_symlink_status(source: Path, target: Path) -> SymlinkStatus:
        if not target.exists() and not target.is_symlink():
            # target missing entirely
            return SymlinkStatus.MISSING_TARGET

        if target.is_symlink() and not target.exists():
            # broken symlink
            return SymlinkStatus.BROKEN_SYMLINK

        if not target.is_symlink():
            # target is not a symlink: regular file
            return SymlinkStatus.NOT_A_SYMLINK

        if target.resolve() != source.resolve():
            # symlink of target points to wrong source
            return SymlinkStatus.WRONG_SOURCE

        # If everything is fine
        return SymlinkStatus.OK

    def has_files(self, pkg: Path):
        """Recurively check if there are any files in the package."""
        return any(item.is_file() or item.is_symlink() for item in pkg.rglob("*"))

    def is_internal_package(self, pkg: Path):
        return pkg.name in InternalFileSystemObject.values()

    def package_check(self) -> list[DoctorCheck]:
        checks: list[DoctorCheck] = []
        if not self.packages:
            checks.append(
                DoctorCheck(
                    name=DoctorStatusName.PACKAGE.value,
                    status=DoctorStatus.WARN,
                    message="No packages found in the dotfiles directory.",
                )
            )

        checks.extend([
            DoctorCheck(
                name=f"{DoctorStatusName.PACKAGE.value}: {pkg.name}",
                status=DoctorStatus.WARN,
                message=f"Package '{pkg.name}' is empty.",
            )
            for pkg in self.packages
            if not self.has_files(pkg) and not self.is_internal_package(pkg)
        ])

        return checks

    def is_symlinked(self) -> list[DoctorCheck]:
        checks: list[DoctorCheck] = []

        if not self.packages:
            checks.append(
                DoctorCheck(
                    name=DoctorStatusName.SYMLINK.value,
                    status=DoctorStatus.WARN,
                    message="No packages found in the dotfiles directory.",
                )
            )
            return checks

        for pkg in self.packages:
            for source in pkg.rglob("*"):
                if source.is_file() or source.is_symlink():
                    target = self.home_dir / source.relative_to(pkg)

                    status = self.get_symlink_status(source, target)
                    match status:
                        case SymlinkStatus.MISSING_TARGET:
                            checks.append(
                                DoctorCheck(
                                    name=f"{pkg.name}:{source.relative_to(pkg)}",
                                    status=DoctorStatus.WARN,
                                    message=f"Missing target: '{target}' entirely.",
                                )
                            )
                        case SymlinkStatus.BROKEN_SYMLINK:
                            checks.append(
                                DoctorCheck(
                                    name=f"{pkg.name}:{source.relative_to(pkg)}",
                                    status=DoctorStatus.WARN,
                                    message=f"Broken symlink: '{target}' points to a missing file.",
                                )
                            )
                        case SymlinkStatus.NOT_A_SYMLINK:
                            checks.append(
                                DoctorCheck(
                                    name=f"{pkg.name}:{source.relative_to(pkg)}",
                                    status=DoctorStatus.WARN,
                                    message=f"Expected symlink but found regular file: '{target}'.",
                                )
                            )
                        case SymlinkStatus.WRONG_SOURCE:
                            checks.append(
                                DoctorCheck(
                                    name=f"{pkg.name}:{source.relative_to(pkg)}",
                                    status=DoctorStatus.WARN,
                                    message=(f"Expected '{source}', but '{target}' points to '{target.resolve()}'."),
                                )
                            )
                        case SymlinkStatus.OK:
                            # Last case only shown when detail is Enabled via a User.
                            if self.detail:
                                checks.append(
                                    DoctorCheck(
                                        name=f"{pkg.name}:{source.relative_to(pkg)}",
                                        status=DoctorStatus.OK,
                                        message=f"Link OK: '{target}'.",
                                    )
                                )

        if not checks:
            checks.append(
                DoctorCheck(
                    name=DoctorStatusName.SYMLINK.value,
                    status=DoctorStatus.OK,
                    message="All files in packages are properly symlinked.",
                )
            )

        return checks

    def check_permissions_dotfiles(self) -> DoctorCheck:
        if not os.access(self.dotfiles_dir, os.W_OK):
            return DoctorCheck(
                name="Permissions", status=DoctorStatus.ERROR, message=f"No write permission for {self.dotfiles_dir}"
            )
        return DoctorCheck(name="Permissions", status=DoctorStatus.OK, message="Permissions look fine.")

    def check_permissions_home(self) -> DoctorCheck:
        if not os.access(self.home_dir, os.W_OK):
            return DoctorCheck(
                name="Permissions", status=DoctorStatus.ERROR, message=f"No write permission for {self.home_dir}"
            )
        return DoctorCheck(name="Permissions", status=DoctorStatus.OK, message="Permissions look fine.")

    def summary(self, doctorchecks: list[DoctorCheck]) -> SummeryReport:
        report = SummeryReport(ok=0, warn=0, error=0)
        for check in doctorchecks:
            match check.status:
                case DoctorStatus.OK:
                    report.ok += 1
                case DoctorStatus.WARN:
                    report.warn += 1
                case DoctorStatus.ERROR:
                    report.error += 1
        return report

    def run_all(self) -> tuple[list[DoctorCheck], SummeryReport]:
        checks: list[DoctorCheck] = []
        checks.append(self.valid_dir)

        if self.valid_dir.status != DoctorStatus.ERROR:
            checks.append(self.check_permissions_dotfiles())
            checks.append(self.check_permissions_home())
            checks.extend(self.package_check())
            checks.extend(self.is_symlinked())

        return checks, self.summary(checks)
