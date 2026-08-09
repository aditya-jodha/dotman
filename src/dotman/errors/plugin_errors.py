from dataclasses import dataclass
from pathlib import Path

from dotman.errors.dotman_error import ErrorContext, ExitCode, IntegrityError


@dataclass(frozen=True, slots=True)
class RepositoryContext(ErrorContext):
    """Context for repository-related errors."""

    path: Path | None = None
    url: str | None = None


@dataclass(frozen=True, slots=True)
class EntryPointContext(ErrorContext):
    """Context for plugin entry point errors."""

    entry_point: str


@dataclass(frozen=True, slots=True)
class SourceContext(ErrorContext):
    """Context for plugin source errors."""

    source: str


class PluginInstallationError(IntegrityError):
    """Generic failure when installing a plugin."""

    EXIT_CODE = ExitCode.DATA_CORRUPTED

    def __init__(self, message: str | None = None):
        if message is None:
            message = "Failed to install plugin"
        super().__init__(message)


class PluginRepositoryError(IntegrityError):
    """Generic failure when operating on a plugin repository."""

    EXIT_CODE = ExitCode.DATA_CORRUPTED

    def __init__(self, message: str, path: Path | None = None, url: str | None = None):
        super().__init__(
            message,
            context=RepositoryContext(path=path, url=url),
        )


class PluginRepositoryNotFoundError(IntegrityError):
    """Raised when a plugin repository cannot be found or opened."""

    EXIT_CODE = ExitCode.DATA_CORRUPTED

    def __init__(self, path: Path):
        super().__init__(
            f"Plugin repository not found: {path}",
            context=RepositoryContext(path=path),
        )


class InvalidPluginEntryPointError(IntegrityError):
    """Raised when an invalid plugin entry point is specified."""

    EXIT_CODE = ExitCode.DATA_CORRUPTED

    def __init__(self, entry_point: str):
        super().__init__(
            f"Invalid plugin entry point: {entry_point}",
            context=EntryPointContext(entry_point=entry_point),
        )


class InvalidPluginSourceError(IntegrityError):
    """Raised when an invalid plugin source is specified."""

    EXIT_CODE = ExitCode.DATA_CORRUPTED

    def __init__(self, source: str):
        super().__init__(
            f"Invalid plugin source: {source}",
            context=SourceContext(source=source),
        )


class PluginNotFoundError(IntegrityError):
    """Raised when no installed plugin has the requested name."""

    EXIT_CODE = ExitCode.DATA_CORRUPTED

    def __init__(self, name: str):
        super().__init__(f"Plugin not found: {name}")
