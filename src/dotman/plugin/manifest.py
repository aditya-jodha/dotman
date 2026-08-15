from __future__ import annotations

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass as pydantic_dataclass

if TYPE_CHECKING:
    from importlib.metadata import EntryPoint

    from dotman.plugin.repository import PluginRepository


@dataclass(frozen=True, slots=True)
class InstalledPlugin:
    repository: PluginRepository | None
    manifest: PluginManifest


@pydantic_dataclass(config=ConfigDict(extra="forbid"))
class PluginManifest:
    name: str
    version: str
    description: str
    authors: list[str]
    entry_point: str
    distribution_name: str | None = None
    api_version: str = ""

    @classmethod
    def from_entry_point(cls, entry_point: EntryPoint) -> PluginManifest:
        """Build a plugin manifest from installed Python package metadata."""
        distribution = entry_point.dist
        if distribution is None:
            raise ValueError

        metadata = distribution.metadata
        author = metadata.get("Author") or metadata.get("Author-email") or ""
        authors = [author] if author else []

        return cls(
            name=entry_point.name,
            version=metadata["Version"],
            description=metadata.get("Summary", ""),
            authors=authors,
            entry_point=entry_point.value,
            distribution_name=metadata["Name"],
        )

    def with_api_version(self, api_version: str) -> PluginManifest:
        return replace(self, api_version=api_version)
