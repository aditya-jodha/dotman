from pathlib import Path


class DoctorStatus:
    OK = "ok"
    WARN = "warn"
    ERROR = "error"


class DoctorCheck:
    def __init__(self, name: str, status: str, message: str):
        self.name = name
        self.status = status
        self.message = message

    def as_dict(self):
        return {
            "name": self.name,
            "status": self.status,
            "message": self.message,
        }


class Doctor:
    def __init__(self, home_dir: Path, dotfile_dir: Path, detail: bool) -> None:
        self.home_dir = home_dir
        self.dotfiles_dir = dotfile_dir
        self.detail = detail

        self.packages = []
        if self.is_dotfiles_dir_valid().status == DoctorStatus.OK:
            self.packages = [p for p in self.dotfiles_dir.iterdir() if p.is_dir()]

    def is_dotfiles_dir_valid(self) -> DoctorCheck:
        if not self.dotfiles_dir.exists():
            return DoctorCheck(
                name="Dotfiles Directory",
                status=DoctorStatus.ERROR,
                message=f"Dotfiles directory '{self.dotfiles_dir}' does not exist.",
            )
        if not self.dotfiles_dir.is_dir():
            return DoctorCheck(
                name="Dotfiles Directory",
                status=DoctorStatus.ERROR,
                message=f"'{self.dotfiles_dir}' exists but is not a directory.",
            )
        return DoctorCheck(
            name="Dotfiles Directory",
            status=DoctorStatus.OK,
            message=f"Dotfiles directory '{self.dotfiles_dir}' is valid.",
        )

    def check_symlink(self, pkg: Path, source: Path, target: Path) -> DoctorCheck | None:
        if not target.exists():
            return DoctorCheck(
                name=f"{pkg.name}:{source.relative_to(pkg)}",
                status=DoctorStatus.WARN,
                message=f"Missing target: '{target}'",
            )

        if not target.is_symlink():
            return DoctorCheck(
                name=f"{pkg.name}:{source.relative_to(pkg)}",
                status=DoctorStatus.WARN,
                message=f"Target exists but is not a symlink: '{target}'",
            )

        if target.resolve() != source.resolve():
            return DoctorCheck(
                name=f"{pkg.name}:{source.relative_to(pkg)}",
                status=DoctorStatus.WARN,
                message=f"Symlink points to wrong source: '{target}'",
            )

        return None

    def is_package_existing(self) -> DoctorCheck:
        if not self.packages:
            return DoctorCheck(
                name="Packages",
                status=DoctorStatus.WARN,
                message="No packages found in the dotfiles directory.",
            )

        for pkg in self.packages:
            for source in pkg.rglob("*"):
                if source.is_file() or source.is_symlink():
                    # If we find at least one file or symlink in any package, we consider it a valid package structure.  # noqa: E501
                    return DoctorCheck(
                        name="Packages",
                        status=DoctorStatus.OK,
                        message=f"Found package '{pkg.name}' with files.",
                    )

        return DoctorCheck(
            name="Packages",
            status=DoctorStatus.WARN,
            message="No files found in any packages in the dotfiles directory.",
        )

    def is_symlinked(self) -> list[DoctorCheck]:
        checks = []

        for pkg in self.packages:
            for source in pkg.rglob("*"):
                if source.is_file() or source.is_symlink():
                    target = self.home_dir / source.relative_to(pkg)

                    check = self.check_symlink(pkg, source, target)
                    if check:
                        # None will come if everything is fine
                        checks.append(check)

                    elif self.detail:
                        checks.append(
                            DoctorCheck(
                                name=f"{pkg.name}:{source.relative_to(pkg)}",
                                status=DoctorStatus.OK,
                                message=f"Link OK: {target}",
                            )
                        )

        if not checks:
            checks.append(
                DoctorCheck(
                    name="Symlink",
                    status=DoctorStatus.OK,
                    message="All files in packages are properly symlinked.",
                )
            )

        return checks

    def run_all(self):
        checks: list[DoctorCheck] = []
        valid_dir = self.is_dotfiles_dir_valid()
        checks.append(valid_dir)

        if valid_dir.status != DoctorStatus.ERROR:
            checks.append(self.is_package_existing())
            checks.extend(self.is_symlinked())

        return checks
