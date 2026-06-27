from dotman.core.config import StrPath
from dotman.errors.dotman_error import DotmanError


class DotmanNotInitializedError(DotmanError):
    def __init__(self):
        self.message = "Dotman is not initialized\nRun 'dotman init' first."
        super().__init__(self.message)


class DotmanProfileNotInitializedError(DotmanError):
    def __init__(self):
        self.message = (
            "Dotman profile is not initialized\nRun 'dotman profile init' first."
        )
        super().__init__(self.message)


class DotmanMetadataFileCorruptedError(DotmanError):
    def __init__(self, argument: StrPath):
        self.message = f"Dotman metadata file is corrupted:  {argument}"
        super().__init__(self.message)
