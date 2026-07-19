from .core.config.config import DotmanConfig
from .core.get_internal_data import DotmanMetadata
from .core.service.doctor_service import DoctorService


class Dotman:
    __slots__ = ("config", "metadata")

    def __init__(self):
        self.config = DotmanConfig.load()
        self.metadata = DotmanMetadata.load()

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
