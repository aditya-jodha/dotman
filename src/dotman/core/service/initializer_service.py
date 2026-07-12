from pathlib import Path

from dotman.core.config.config import DotmanConfig
from dotman.core.initializer import Initializer
from dotman.errors.initializer_errors import DotmanDotfilesBackupDirExistsError


class InitializerService:
    def __init__(self, home_dir: Path | None = None, dotfiles_dir: Path | None = None) -> None:
        cfg = DotmanConfig.load()
        self.dotfiles_dir = dotfiles_dir or cfg.dotfiles_dir
        self.home_dir = home_dir or cfg.home_dir
        self.initializer = Initializer(self.home_dir, self.dotfiles_dir)

    def setup(self, current_profile: str):
        if self.initializer.is_old_dotfiles_exist:
            if self.initializer.is_backup_exist:
                raise DotmanDotfilesBackupDirExistsError(self.dotfiles_dir)

            self.initializer.convert_to_backup()

        self.initializer.make_dir()
        self.initializer.create_meta(current_profile)
        self.initializer.create_profile(current_profile)

        return self.initializer
