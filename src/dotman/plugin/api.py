from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    import typer

    from .manifest import PluginManifest
    from .validation import AddValidator, ValidationRegistry


@dataclass(frozen=True, slots=True)
class PluginAPI:
    manifest: PluginManifest
    _root_app: typer.Typer
    _validation_registry: ValidationRegistry
    _typer_apps: list[tuple[typer.Typer, str]] = field(default_factory=list)
    _validators: list[AddValidator] = field(default_factory=list)

    def add_typer(
        self,
        app: typer.Typer,
        *,
        name: str,
    ) -> None:
        self._typer_apps.append((app, name))

    def add_validator(self, validator: AddValidator) -> None:
        self._validators.append(validator)

    def _commit(self) -> None:
        """Apply registrations after a plugin has registered successfully."""
        for app, name in self._typer_apps:
            self._root_app.add_typer(app, name=name)
        for validator in self._validators:
            self._validation_registry.add_validator(validator)


class DotmanPlugin(Protocol):
    def register(self, api: PluginAPI) -> None: ...
