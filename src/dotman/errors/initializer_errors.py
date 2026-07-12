from pathlib import Path

from dotman.core.config.types import StrPath
from dotman.errors.dotman_error import ExitCode, InitializationError, IntegrityError
from dotman.errors.profile_errors import MetadataContext


class DotmanNotInitializedError(InitializationError):
    EXIT_CODE = ExitCode.INVALID_ARGUMENTS

    def __init__(self) -> None:
        super().__init__(message="Dotman is not initialized\nRun 'dotman init' first.")


class DotmanProfileNotInitializedError(InitializationError):
    EXIT_CODE = ExitCode.INVALID_ARGUMENTS

    def __init__(self) -> None:
        super().__init__(
            message="Dotman profile is not initialized\nRun 'dotman profile init' first."
        )


class DotmanMetadataFileCorruptedError(IntegrityError):
    EXIT_CODE = ExitCode.DATA_CORRUPTED

    def __init__(self, argument: StrPath) -> None:
        super().__init__(
            message=f"Dotman metadata file is corrupted:  {argument}",
            context=MetadataContext(path=argument),
        )


class DotmanDotfilesBackupDirExistsError(InitializationError):
    EXIT_CODE = ExitCode.INVALID_ARGUMENTS

    def __init__(self, dotfiles_dir: Path) -> None:
        super().__init__(message=f"Dotfiles backup directory already exists at {dotfiles_dir}")
