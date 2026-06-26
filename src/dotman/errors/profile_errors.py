from enum import Enum
from pathlib import Path


class ProfileError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

    @property
    def error(self) -> str:
        return self.message


class ProfileAlreadyExistsError(ProfileError):
    def __init__(self, profile: str):
        super().__init__(f"Profile {profile} already exists")
        self.profile = profile


class ProfileNotFoundError(ProfileError):
    def __init__(self, profile: str):
        super().__init__(f"Profile {profile} not found")
        self.profile = profile


class ProfileMetaDataFileCorruptedError(ProfileError):
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


class DirNotEmptyError(ProfileError):
    def __init__(self, directory: Path):
        super().__init__(f"Directory {directory.name} is not empty")
        self.directory = directory
