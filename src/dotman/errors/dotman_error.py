from dataclasses import dataclass, fields, is_dataclass
from enum import Enum, IntEnum, StrEnum
from pathlib import Path
from typing import Any, Literal


def _serialize(obj: object) -> object:
    """Recursively serializes an object to a JSON-compatible format."""
    if obj is None:
        return None

    if isinstance(obj, Path):
        return str(obj)

    if isinstance(obj, Enum):
        return obj.value

    if is_dataclass(obj):
        return {field.name: _serialize(getattr(obj, field.name)) for field in fields(obj)}

    if isinstance(obj, dict):
        return {_serialize(key): _serialize(value) for key, value in obj.items()}

    if isinstance(obj, (list, tuple, set)):
        return [_serialize(item) for item in obj]

    return obj


type PayloadKey = Literal[
    "message",
    "exit_code",
    "category",
    "context",
]


class ExitCode(IntEnum):
    """Canonical operating system exit codes for the dotman CLI."""

    SUCCESS = 0
    GENERIC_FAILURE = 1
    INVALID_ARGUMENTS = 2
    DATA_CORRUPTED = 65
    PERMISSION_DENIED = 77
    KEYBOARD_INTERRUPT = 130


class Category(StrEnum):
    GENERIC = "generic"
    PROFILE = "profile"
    INITIALIZATION = "initialization"
    FILESYSTEM = "filesystem"
    INTEGRITY = "integrity"


@dataclass(frozen=True, slots=True)
class ErrorContext:
    """Base structural container for JSON serialization and debugging."""


@dataclass(frozen=True, slots=True, kw_only=True)
class ErrorPayload:
    """The unified data structure returned to the CLI layer for formatting and rendering."""

    message: str
    exit_code: ExitCode
    category: Category
    context: ErrorContext | None

    def to_dict(self) -> dict[PayloadKey, Any]:
        return {
            "message": self.message,
            "exit_code": self.exit_code.value,
            "category": self.category.value,
            "context": _serialize(self.context),
        }


class DotmanError(Exception):
    """Base class for all dotman errors."""

    EXIT_CODE: ExitCode = ExitCode.GENERIC_FAILURE
    CATEGORY: Category = Category.GENERIC

    def __init__(self, message: str, context: ErrorContext | None = None) -> None:
        super().__init__(message)
        self.message: str = message
        self.context: ErrorContext | None = context

    def __str__(self) -> str:
        """Returns the actual user-facing error message instead of the class name."""
        return self.message

    def to_payload(self) -> ErrorPayload:
        """Converts exception metadata into a pure dataclass payload for the CLI layer to handle."""
        return ErrorPayload(
            message=self.message,
            exit_code=self.EXIT_CODE,
            category=self.CATEGORY,
            context=self.context,
        )


# --- Category Class Groupings ---


class InitializationError(DotmanError):
    CATEGORY = Category.INITIALIZATION


class ProfileError(DotmanError):
    CATEGORY = Category.PROFILE


class FilesystemError(DotmanError):
    CATEGORY = Category.FILESYSTEM


class IntegrityError(DotmanError):
    CATEGORY = Category.INTEGRITY
