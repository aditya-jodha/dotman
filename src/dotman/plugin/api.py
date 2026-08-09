from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    import typer

    from .manifest import PluginManifest


@dataclass(frozen=True, slots=True)
class PluginAPI:
    manifest: PluginManifest
    _root_app: typer.Typer

    def add_typer(
        self,
        app: typer.Typer,
        *,
        name: str,
    ) -> None:
        self._root_app.add_typer(app, name=name)


class DotmanPlugin(Protocol):
    def register(self, api: PluginAPI) -> None: ...
