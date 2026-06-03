import shutil
import time
from pathlib import Path


class LinkAction:
    SKIP = "skip"
    LINK = "link"
    BACKUP_AND_LINK = "backup_and_link"
    FIX = "fix"


class LinkResult:
    def __init__(self, source: Path, target: Path, action: str, status: str, message: str = ""):
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
    def __init__(self, dry_run: bool = False, backup_dir: Path = Path(".dotman_backup")):
        self.dry_run = dry_run
        self.backup_dir = Path(backup_dir).expanduser()
        if not self.backup_dir.is_absolute():
            self.backup_dir = Path.home() / self.backup_dir
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
