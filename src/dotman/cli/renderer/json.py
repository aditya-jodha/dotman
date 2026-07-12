import json
import sys

from dotman.errors.dotman_error import ErrorPayload

from .base import OutputRenderer


class JsonRenderer(OutputRenderer):
    """Machine-readable pipeline output stream."""

    def render(self, payload: ErrorPayload) -> None:
        sys.stderr.write(json.dumps(payload.to_dict(), indent=2) + "\n")
