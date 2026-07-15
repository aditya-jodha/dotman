import sys

from dotman.errors.dotman_error import ErrorPayload


class PlainRenderer:
    """Minimal text stream fallback for simple shell utilities."""

    def render(self, payload: ErrorPayload) -> None:
        sys.stderr.write(f"Error ({payload.category}): {payload.message}\n")
