from pathlib import Path


class Initializer:
    def __init__(self, home_dir: Path, dotfiles_dir: Path):
        self.home_dir = home_dir
        self.dotfiles_dir = dotfiles_dir

    @property
    def is_old_dotfiles_exist(self) -> bool:
        """Checks if the existing dotfiles directory exists."""
        return self.dotfiles_dir.exists()

    @property
    def is_backup_exist(self) -> bool:
        """Checks if the backup directory exists."""
        backup_dir = self.dotfiles_dir.with_suffix(".backup")
        return backup_dir.exists()

    def convert_to_backup(self):
        """Renames the existing dotfiles directory to a backup directory."""
        backup_dir = self.dotfiles_dir.with_suffix(".backup")
        return self.dotfiles_dir.rename(backup_dir)

    def make_dir(self):
        """Creates the dotfiles directory."""
        if not self.dotfiles_dir.exists():
            self.dotfiles_dir.mkdir()

    def setup(self):
        """Sets up the dotfiles directory by creating some default files."""
        # MetaData file
        meta_file = self.dotfiles_dir / "metadata.json"
        meta_file.touch()
