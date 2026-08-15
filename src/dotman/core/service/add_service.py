from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from dotman.cli.common_func import sanitize_package_name
from dotman.cli.tree_builder import print_beautiful_directory
from dotman.core.add import AddFiles, RollbackJournal, SymlinkCheck, SymlinkStatus
from dotman.core.get_internal_data import DotmanMetadata
from dotman.plugin.validation import ValidationRegistry

if TYPE_CHECKING:
    from pathlib import Path

    from rich.tree import Tree


@dataclass(slots=True)
class Preview:
    warnings: list[str]
    package_created: bool


class AddOperation:
    def __init__(
        self,
        file: Path,
        package: str,
        home_dir: Path,
        dotfiles_dir: Path,
        profile: str,
        validation: ValidationRegistry | None = None,
    ) -> None:
        self.home_dir = home_dir
        self.dotfiles_dir = dotfiles_dir

        self.journal = RollbackJournal()
        self.internal_data: DotmanMetadata = DotmanMetadata.load()

        self.file = file
        self.package: str = sanitize_package_name(package)

        self.profile = profile

        self.add_files = AddFiles(
            file=self.file,
            package=self.package,
            profile_name=self.profile,
            home_dir=self.home_dir,
            dotfiles_dir=self.dotfiles_dir,
            logbook=self.journal,
            validation=validation or ValidationRegistry(),
        )

    def validate(self):
        self.add_files.validate()

    def preview(self) -> Preview:
        """Run validation and symlink checks, return a preview object."""
        # NOTE: Will not create anything in preview

        self.add_files.validate()
        symlink_checks: list[SymlinkCheck] = self.add_files.validate_directory_symlinks()

        warnings = [check.message for check in symlink_checks if check.status != SymlinkStatus.OK]

        package_created = not self.add_files.package_exists

        return Preview(warnings=warnings, package_created=package_created)

    def add(self):
        if not self.add_files.package_exists:
            self.add_files.create_package()
        self.add_files.move_file_to_dotfiles()

    def commit(self) -> None:
        """Perform the actual move and clear rollback journal."""
        self.journal.clear()

    def rollback_changes(self):
        self.journal.rollback()
        self.add_files.delete_empty_package()

    def tree(self) -> Tree:
        return print_beautiful_directory(self.add_files.profile_root)
