from pathlib import Path

from dotman.core.config import InternalFileSystemObject


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
        self.dotfiles_dir.mkdir(parents=True, exist_ok=True)

    def create_meta(self, current_profile: str):
        """Creates the metadata file."""
        meta_file = self.dotfiles_dir / InternalFileSystemObject.METADATA.value
        meta_file.write_text(f"current_profile: {current_profile}\n")
        return meta_file

    def create_profile(self, name: str):
        """Writes a profile file."""
        profile_dir = self.dotfiles_dir / InternalFileSystemObject.PROFILES.value / name
        profile_dir.mkdir(parents=True)
        return profile_dir
