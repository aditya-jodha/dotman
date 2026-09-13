import shutil
from pathlib import Path

from dotman.core.config.config import InternalFileSystemObject
from dotman.core.profile import ProfileManager


class Initializer:
    def __init__(self, home_dir: Path, dotfiles_dir: Path):
        self.home_dir = home_dir
        self.dotfiles_dir = dotfiles_dir

        self.profile_manager = ProfileManager(self.dotfiles_dir)

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

    def backup_to_current(self):
        """Renames the existing dotfiles directory to the dotfiles directory."""
        return self.dotfiles_dir.with_suffix(".backup").rename(self.dotfiles_dir)

    def make_dir(self):
        """Creates the dotfiles directory."""
        self.dotfiles_dir.mkdir(parents=True, exist_ok=True)

    def create_meta(self, current_profile: str):
        """Creates the metadata file."""
        meta_file = self.dotfiles_dir / InternalFileSystemObject.METADATA.value
        meta_file.write_text(f"current_profile: {current_profile}\n")
        return meta_file

    def delete_dotfiles_dir(self):
        """Deletes the dotfiles directory."""
        if self.dotfiles_dir.exists():
            shutil.rmtree(self.dotfiles_dir)

    def create_profile(self, name: str):
        """Creates a profile directory."""
        self.profile_manager.create_profile(name)
