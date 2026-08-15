from dataclasses import dataclass, field

from dotman.core.config.config import DotmanConfig
from dotman.core.get_internal_data import DotmanMetadata
from dotman.plugin.validation import ValidationRegistry


@dataclass(frozen=True, slots=True)
class AppContext:
    validation_registry: ValidationRegistry = field(default_factory=ValidationRegistry)

    config: DotmanConfig = field(default_factory=DotmanConfig.load)
    metadata: DotmanMetadata = field(default_factory=DotmanMetadata.load)
