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
    def __init__(self, argument: Enum):
        super().__init__(f"MetaData file is corrupted:  {argument.value}")
        self.argument = argument


class DirNotEmptyError(ProfileError):
    def __init__(self, directory: Path):
        super().__init__(f"Directory {directory.name} is not empty")
        self.directory = directory
