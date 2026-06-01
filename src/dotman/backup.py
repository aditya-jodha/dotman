from pathlib import Path


class Backup:
    def __init__(self, home_dir: Path, dotfiles_dir: Path):
        self.home_dir = home_dir
        self.dotfiles_dir = dotfiles_dir

    @property
    def old_dotfiles_exist(self) -> bool:
        """Checks if the existing dotfiles directory exists."""
        return self.dotfiles_dir.exists()

    def convert_to_backup(self):
        """Renames the existing dotfiles directory to a backup directory."""
        backup_dir = self.dotfiles_dir.with_suffix(".backup")
        return self.dotfiles_dir.rename(backup_dir)

    def make_dir(self):
        """Creates the dotfiles directory."""
        if not self.dotfiles_dir.exists():
            self.dotfiles_dir.mkdir()
