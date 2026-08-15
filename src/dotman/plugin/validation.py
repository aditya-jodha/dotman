from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class AddValidationContext:
    """Context for add validation."""

    file: Path
    package: str
    home_dir: Path
    dotfiles_dir: Path


AddValidator = Callable[[AddValidationContext], None]


class ValidationRegistry:
    def __init__(self) -> None:
        self._add_validators: list[AddValidator] = []

    def add_validator(self, validator: AddValidator) -> None:
        self._add_validators.append(validator)

    def validate_add(self, context: AddValidationContext) -> None:
        for validator in self._add_validators:
            validator(context)
