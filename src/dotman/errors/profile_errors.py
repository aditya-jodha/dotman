from enum import Enum
from pathlib import Path

from dotman.errors.dotman_error import DotmanError


class ProfileAlreadyExistsError(DotmanError):
    def __init__(self, profile: str):
        super().__init__(f"Profile {profile} already exists")
        self.profile = profile


class ProfileNotFoundError(DotmanError):
    def __init__(self, profile: str | None):
        if profile is None:
            super().__init__("No profile found")
        else:
            super().__init__(f"Profile {profile} not found")
        self.profile = profile


class ProfileMetaDataFileCorruptedError(DotmanError):
    def __init__(self, argument: Enum, profile_exists: bool = True):
        if profile_exists:
            message = f"Profile metadata file is corrupted:  {argument.value}"
        else:
            message = (
                f"Profile metadata file is corrupted:  {argument.value} does not exist"
            )
        super().__init__(message)
        self.argument = argument

    @property
    def error(self) -> str:
        return self.message


class DirNotEmptyError(DotmanError):
    def __init__(self, directory: Path):
        super().__init__(f"Directory {directory.name} is not empty")
        self.directory = directory
