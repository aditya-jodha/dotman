from abc import ABC, abstractmethod
from enum import StrEnum

from dotman.errors.dotman_error import ErrorPayload


class OutputFormat(StrEnum):
    RICH = "rich"
    JSON = "json"
    PLAIN = "plain"


class OutputRenderer(ABC):
    """Strategy abstract base class for output boundaries."""

    @abstractmethod
    def render(self, payload: ErrorPayload) -> None:
        raise NotImplementedError
