from dotman.core.config import StrPath
from dotman.errors.dotman_error import ExitCode, InitializationError, IntegrityError
from dotman.errors.profile_errors import MetadataContext


class DotmanNotInitializedError(InitializationError):
    EXIT_CODE = ExitCode.INVALID_ARGUMENTS

    def __init__(self) -> None:
        # Keeps your original explicit attribute mapping intact
        self.message = "Dotman is not initialized\nRun 'dotman init' first."
        super().__init__(message=self.message)


class DotmanProfileNotInitializedError(InitializationError):
    EXIT_CODE = ExitCode.INVALID_ARGUMENTS

    def __init__(self) -> None:
        self.message = "Dotman profile is not initialized\nRun 'dotman profile init' first."
        super().__init__(message=self.message)


class DotmanMetadataFileCorruptedError(IntegrityError):
    EXIT_CODE = ExitCode.DATA_CORRUPTED

    def __init__(self, argument: StrPath) -> None:
        self.message = f"Dotman metadata file is corrupted:  {argument}"
        super().__init__(message=self.message, context=MetadataContext(path=argument))
