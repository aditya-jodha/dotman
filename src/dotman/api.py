from pathlib import Path

from dotman.core.service.add_service import AddOperation

from .core.config.config import DotmanConfig
from .core.get_internal_data import DotmanMetadata
from .core.service.doctor_service import DoctorService


class Dotman:
    __slots__ = ("config", "metadata")

    def __init__(
        self,
        config: DotmanConfig | None = None,
        metadata: DotmanMetadata | None = None,
    ):
        self.config = config or DotmanConfig.load()
        self.metadata = metadata or DotmanMetadata.load()

    def refresh(self):
        self.metadata = DotmanMetadata.load()
        self.config = DotmanConfig.load()

    def __repr__(self):
        return f"Dotman(config={self.config}, metadata={self.metadata})"

    def __eq__(self, value: object) -> bool:
        return (
            isinstance(value, Dotman)
            and self.config == value.config
            and self.metadata == value.metadata
        )

    def __hash__(self) -> int:
        return hash((self.__class__, self.config, self.metadata))

    def doctor(self, detail: bool = False):
        service = DoctorService(
            current_profile=self.metadata.current_profile,
            detail=detail,
            config=self.config,
        )
        return service.execute().run_all()

    def add(self, file: Path, package: str):
        return AddOperation(
            file=file,
            package=package,
            home_dir=self.config.home_dir,
            dotfiles_dir=self.config.dotfiles_dir,
            profile=self.metadata.current_profile_or_raise(),
        )
