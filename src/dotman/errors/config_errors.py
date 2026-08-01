from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from yaml.error import MarkedYAMLError

from dotman.errors.dotman_error import ErrorContext, ExitCode, IntegrityError

if TYPE_CHECKING:
    import tomllib
    from pathlib import Path

    import yaml
    from pydantic import ValidationError


@dataclass(frozen=True, slots=True)
class ConfigValidationIssue:
    field: str
    reason: str

    @classmethod
    def from_validation_error(cls, error: ValidationError) -> list[ConfigValidationIssue]:
        return [
            cls(
                field=".".join(map(str, err["loc"])),
                reason=err["msg"],
            )
            for err in error.errors()
        ]


@dataclass(frozen=True, slots=True)
class ConfigParseIssue:
    line: int | None
    column: int | None
    reason: str

    @classmethod
    def from_error(cls, error: yaml.YAMLError | tomllib.TOMLDecodeError) -> ConfigParseIssue:
        if isinstance(error, MarkedYAMLError) and error.problem_mark is not None:
            mark = error.problem_mark
            return cls(
                line=mark.line + 1,
                column=mark.column + 1,
                reason=error.problem or str(error),
            )
        return cls(line=None, column=None, reason=str(error))


@dataclass(frozen=True, slots=True)
class ConfigParseContext(ErrorContext):
    path: Path
    issue: ConfigParseIssue


@dataclass(frozen=True, slots=True)
class InvalidConfigContext(ErrorContext):
    path: Path
    issues: list[ConfigValidationIssue]


@dataclass(frozen=True, slots=True)
class InvalidConfigValueContext(ErrorContext):
    key: str
    value: object
    issues: list[ConfigValidationIssue]


@dataclass(frozen=True, slots=True)
class InvalidConfigKeyContext(ErrorContext):
    key: str
    valid_keys: tuple[str, ...]


class ConfigParseError(IntegrityError):
    EXIT_CODE = ExitCode.DATA_CORRUPTED

    def __init__(self, path: Path, error: yaml.YAMLError | tomllib.TOMLDecodeError):
        super().__init__(
            f"Failed to parse config file: {path}",
            context=ConfigParseContext(path=path, issue=ConfigParseIssue.from_error(error)),
        )


class InvalidConfigValueError(IntegrityError):
    EXIT_CODE = ExitCode.DATA_CORRUPTED

    def __init__(
        self,
        key: str,
        value: object,
        error: ValidationError,
    ):
        super().__init__(
            f"Invalid value for '{key}'",
            context=InvalidConfigValueContext(
                key=key,
                value=value,
                issues=ConfigValidationIssue.from_validation_error(error),
            ),
        )


class InvalidConfigKeyError(IntegrityError):
    EXIT_CODE = ExitCode.DATA_CORRUPTED

    def __init__(self, key: str, valid_keys: tuple[str, ...]):
        super().__init__(
            f"Unknown configuration key: {key}",
            context=InvalidConfigKeyContext(
                key=key,
                valid_keys=valid_keys,
            ),
        )


class InvalidConfigFileError(IntegrityError):
    EXIT_CODE = ExitCode.DATA_CORRUPTED

    def __init__(self, path: Path, error: ValidationError):
        super().__init__(
            f"Dotman config file is corrupted: {path}",
            context=InvalidConfigContext(
                path=path,
                issues=ConfigValidationIssue.from_validation_error(error),
            ),
        )


class ConfigFileNotFoundError(IntegrityError):
    EXIT_CODE = ExitCode.DATA_CORRUPTED

    def __init__(self, path: Path):
        super().__init__(f"Config file not found: {path}")
