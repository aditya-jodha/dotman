from collections.abc import Callable
from functools import wraps
from pathlib import Path

from dotman.core.config import load_config
from dotman.errors.validator_errors import (
    DotmanMetadataFileCorruptedError,
    DotmanNotInitializedError,
    DotmanProfileNotInitializedError,
)


class DotmanValidator:
    def __init__(self, dotfiles_dir: Path | None = None, home_dir: Path | None = None) -> None:
        cgf = load_config()
        self.dotfiles_dir = dotfiles_dir or cgf.dotfiles_dir
        self.home_dir = home_dir or cgf.home_dir
        self.metadata: Path = self.dotfiles_dir / "metadata.yml"
        self.profiles_dir: Path = self.dotfiles_dir / "profiles"

    def __call__(self) -> None:
        """Automatically finds and runs all check methods."""
        for attr_name in dir(self):
            # Filter for validation methods using prefixes
            if attr_name.startswith("validate_") or attr_name.startswith("ensure_"):
                # Retrieve the actual function object
                method = getattr(self, attr_name)
                # Confirm it is callable, then execute it
                if callable(method):
                    method()

    def ensure_profile_exists(self) -> None:
        if not self.profiles_dir.exists():
            raise DotmanProfileNotInitializedError()

    def enure_metadata_exists(self) -> None:
        if not self.metadata.exists():
            raise DotmanMetadataFileCorruptedError(self.metadata)

    def validate_initialized(self) -> None:
        if not self.dotfiles_dir.exists():
            raise DotmanNotInitializedError()

        if not self.home_dir.exists():
            raise DotmanNotInitializedError()

        if not self.metadata.exists():
            raise DotmanMetadataFileCorruptedError(self.metadata)


def require_initialized[**P, R](func: Callable[P, R]) -> Callable[P, R]:
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        DotmanValidator().validate_initialized()
        return func(*args, **kwargs)

    return wrapper


def require_profile[**P, R](func: Callable[P, R]) -> Callable[P, R]:
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        DotmanValidator().ensure_profile_exists()
        return func(*args, **kwargs)

    return wrapper
