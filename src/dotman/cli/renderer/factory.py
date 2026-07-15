from collections.abc import Mapping
from types import MappingProxyType
from typing import ClassVar

from .base import OutputFormat, OutputRenderer
from .json import JsonRenderer
from .plain import PlainRenderer
from .rich import RichRenderer


class RuntimeState:
    """Global configuration state container for the active process RuntimeState."""

    renderer: ClassVar[OutputRenderer] = RichRenderer()

    _RENDERER_MAP: ClassVar[Mapping[OutputFormat, type[OutputRenderer]]] = MappingProxyType(
        {
            OutputFormat.RICH: RichRenderer,
            OutputFormat.JSON: JsonRenderer,
            OutputFormat.PLAIN: PlainRenderer,
        }
    )

    @classmethod
    def configure(cls, fmt: OutputFormat) -> None:
        """Dynamically instantiates the global state handler on startup."""
        renderer_class = cls._RENDERER_MAP.get(fmt, RichRenderer)
        cls.renderer = renderer_class()
