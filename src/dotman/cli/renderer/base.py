from enum import StrEnum
from typing import Protocol

from dotman.errors.dotman_error import ErrorPayload


class OutputFormat(StrEnum):
    RICH = "rich"
    JSON = "json"
    PLAIN = "plain"


class OutputRenderer(Protocol):
    """Strategy abstract base class for output boundaries."""

    def render(self, payload: ErrorPayload) -> None: ...
