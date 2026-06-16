import shutil
import time
from dataclasses import dataclass
from pathlib import Path

from dotman.core.doctor import Doctor, SymlinkStatus


@dataclass
class LinkPair:
    source: Path
    relative_source: Path
    target: Path


class LinkAction:
    SKIP = "skip"
    LINK = "link"
    BACKUP_AND_LINK = "backup_and_link"
    FIX = "fix"


@dataclass
class UnlinkCheck:
    source: Path
    target: Path

    status: SymlinkStatus


@dataclass(slots=True)
class UnlinkResult:
    source: Path
    target: Path
    status: SymlinkStatus
    removed: bool

    def as_dict(self) -> dict[str, str | float]:
        return {
            "source": str(self.source),
            "target": str(self.target),
            "status": self.status.value,
            "removed": self.removed,
        }


class LinkResult:
    def __init__(
        self, source: Path, target: Path, action: str, status: str, message: str = ""
    ):
        self.source = source
        self.target = target
        self.action = action
        self.status = status
        self.message = message
        self.timestamp = time.time()

    def as_dict(self) -> dict[str, str | float]:
        return {
            "source": str(self.source),
            "target": str(self.target),
            "action": self.action,
            "status": self.status,
            "message": self.message,
            "timestamp": self.timestamp,
        }


class Linker:
    def __init__(self, home_dir: Path, backup_dir: Path, dry_run: bool = False):
        self.home_dir = home_dir
        self.dry_run = dry_run
        self.backup_dir = Path(backup_dir).expanduser()
        if not self.backup_dir.is_absolute():
            self.backup_dir = home_dir / self.backup_dir
        if not self.dry_run:
            self.backup_dir.mkdir(parents=True, exist_ok=True)

    def resolve(self, source: Path, target: Path):
        """Resolves the source and target paths to their absolute forms."""
        source = Path(source).expanduser().resolve()
        target = Path(target).expanduser()
        return source, target

    def analyze(self, source: Path, target: Path):
        """Analyzes the state of the target path to determine the appropriate action."""
        if target.exists() or target.is_symlink():
            if target.is_symlink():
                if target.resolve() == source:
                    return LinkAction.SKIP
                return LinkAction.FIX
            return LinkAction.BACKUP_AND_LINK

        return LinkAction.LINK

    def backup(self, target: Path):
        """Backs up the existing target file or directory to the backup directory."""
        if not target.exists():
            return

        timestamp = int(time.time())
        backup_path = self.backup_dir / f"{target.name}.{timestamp}"

        backup_path.parent.mkdir(parents=True, exist_ok=True)

        shutil.move(str(target), str(backup_path))

    def execute(self, source: Path, target: Path):
        """Executes the linking action based on the analysis of the source and target paths."""
        source, target = self.resolve(source, target)
        action = self.analyze(source, target)

        if action == LinkAction.SKIP:
            return LinkResult(source, target, action, "ok", "already linked")

        if self.dry_run:
            return LinkResult(source, target, action, "dry-run", "no changes made")

        try:
            if action == LinkAction.BACKUP_AND_LINK:
                self.backup(target)

            if target.exists() or target.is_symlink():
                target.unlink()

            target.parent.mkdir(parents=True, exist_ok=True)

            target.symlink_to(source)

            return LinkResult(source, target, action, "ok", "linked successfully")

        except Exception as e:  # noqa: BLE001
            return LinkResult(source, target, action, "error", str(e))

    def link(self, linkpairs: list[LinkPair]) -> list[LinkResult]:
        """Links a source file to a target path."""
        return [
            self.execute(linkpair.source, linkpair.target) for linkpair in linkpairs
        ]


class Unlinker:
    @staticmethod
    def status(source: Path, target: Path) -> SymlinkStatus:
        return Doctor.get_symlink_status(source, target)

    def unlink(self, pairs: list[LinkPair]) -> list[UnlinkResult]:
        results: list[UnlinkResult] = []
        for pair in pairs:
            status = self.status(pair.source, pair.target)
            match status:
                case SymlinkStatus.OK:
                    pair.target.unlink(missing_ok=True)
                    results.append(
                        UnlinkResult(
                            source=pair.source,
                            target=pair.target,
                            status=SymlinkStatus.OK,
                            removed=True,
                        )
                    )
                case SymlinkStatus.BROKEN_SYMLINK:
                    pair.target.unlink(missing_ok=True)
                    results.append(
                        UnlinkResult(
                            source=pair.source,
                            target=pair.target,
                            status=status,
                            removed=True,
                        )
                    )

                case _:
                    # MISSING_TARGET shouldn't be removed.
                    # source -> exists
                    # target -> doesn't exist
                    # There is nothing to unlink.
                    results.append(
                        UnlinkResult(
                            source=pair.source,
                            target=pair.target,
                            status=status,
                            removed=False,
                        )
                    )
        return results
