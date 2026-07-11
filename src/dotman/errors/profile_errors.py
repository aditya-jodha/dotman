from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from dotman.core.config import StrPath
from dotman.errors.dotman_error import (
    ErrorContext,
    ExitCode,
    FilesystemError,
    IntegrityError,
    ProfileError,
)


# ----------------------------------------------------
# Typed Dataclass Context Schemas
# ----------------------------------------------------
@dataclass(frozen=True)
class ProfileContext(ErrorContext):
    profile_name: str | None


@dataclass(frozen=True)
class ProfileMetadataContext(ErrorContext):
    argument_value: str
    profile_exists: bool


@dataclass(frozen=True)
class DirectoryContext(ErrorContext):
    directory_path: Path


@dataclass(frozen=True)
class MetadataContext(ErrorContext):
    path: StrPath


# ----------------------------------------------------
# Custom Exceptions
# ----------------------------------------------------
class ProfileAlreadyExistsError(ProfileError):
    EXIT_CODE = ExitCode.INVALID_ARGUMENTS

    def __init__(self, profile: str) -> None:
        ctx = ProfileContext(profile_name=profile)
        super().__init__(f"Profile '{profile}' already exists.", context=ctx)


class ProfileNotFoundError(ProfileError):
    EXIT_CODE = ExitCode.INVALID_ARGUMENTS

    def __init__(self, profile: str | None) -> None:
        ctx = ProfileContext(profile_name=profile)
        msg = "No profile found." if profile is None else f"Profile '{profile}' not found."
        super().__init__(msg, context=ctx)


class ProfileMetaDataFileCorruptedError(IntegrityError):
    EXIT_CODE = ExitCode.DATA_CORRUPTED

    def __init__(self, argument: Enum, profile_exists: bool = True) -> None:
        ctx = ProfileMetadataContext(
            argument_value=str(argument.value), profile_exists=profile_exists
        )
        if profile_exists:
            msg = f"Profile metadata file is corrupted: {argument.value}"
        else:
            msg = f"Profile metadata file is corrupted: {argument.value} does not exist."
        super().__init__(msg, context=ctx)


class DirNotEmptyError(FilesystemError):
    EXIT_CODE = ExitCode.PERMISSION_DENIED

    def __init__(self, directory: Path) -> None:
        ctx = DirectoryContext(directory_path=directory)
        super().__init__(f"Directory '{directory.name}' is not empty.", context=ctx)
