from pathlib import Path

from dotman.context import AppContext
from dotman.core.service.add_service import AddOperation

from .core.service.doctor_service import DoctorService


class Dotman:
    __slots__ = ("context",)

    def __init__(
        self,
        context: AppContext | None = None,
    ):
        self.context = context or AppContext()

    def __repr__(self):
        return f"Dotman(context={self.context!r})"

    def __eq__(self, value: object) -> bool:
        return (
            isinstance(value, Dotman)
            and self.context.config == value.context.config
            and self.context.metadata == value.context.metadata
        )

    def __hash__(self) -> int:
        return hash((self.__class__, self.context.config, self.context.metadata))

    def doctor(self, detail: bool = False):
        service = DoctorService(
            current_profile=self.context.metadata.current_profile,
            detail=detail,
            config=self.context.config,
        )
        return service.execute().run_all()

    def add(self, file: Path, package: str):
        return AddOperation(
            file=file,
            package=package,
            home_dir=self.context.config.home_dir,
            dotfiles_dir=self.context.config.dotfiles_dir,
            profile=self.context.metadata.current_profile_or_raise(),
            validation=self.context.validation_registry,
        )


class Application:
    _dotman: Dotman | None = None

    @classmethod
    def configure(cls, context: AppContext) -> None:
        cls._dotman = Dotman(context)

    @classmethod
    def get_dotman(cls) -> Dotman:
        if cls._dotman is None:
            raise RuntimeError("Application has not been initialized")  # noqa: TRY003

        return cls._dotman
