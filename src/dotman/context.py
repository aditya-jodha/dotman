from dataclasses import dataclass, field

from dotman.core.config.config import DotmanConfig
from dotman.plugin.validation import ValidationRegistry


@dataclass(frozen=True, slots=True)
class AppContext:
    validation_registry: ValidationRegistry = field(default_factory=ValidationRegistry)

    config: DotmanConfig = field(default_factory=DotmanConfig.load)
