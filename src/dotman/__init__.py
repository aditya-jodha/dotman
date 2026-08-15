from importlib.metadata import PackageNotFoundError, metadata, version

from dotman.api import Application, Dotman
from dotman.core.config.constants import DOTMAN
from dotman.plugin.api import DotmanPlugin

try:
    pkg_metadata = metadata(DOTMAN)
    __author__ = pkg_metadata.get("Author", "Unknown Author")
    __version__ = version(DOTMAN)
except PackageNotFoundError:
    __version__ = "0.0.0"


__all__ = [
    "Application",
    "Dotman",
    "DotmanPlugin",
]
