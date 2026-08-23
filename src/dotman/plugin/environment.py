import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

from dotman.errors.plugin_errors import PluginRepositoryError


@dataclass(slots=True, frozen=True)
class PluginEnvironment:
    """Represents the Python environment of an installed plugin."""

    repository_path: Path

    @property
    def environment_path(self) -> Path:
        return self.repository_path / ".venv"

    @property
    def exists(self) -> bool:
        return self.python.exists() and self.site_packages.exists()

    @property
    def python(self) -> Path:
        if os.name == "nt":
            return self.environment_path / "Scripts" / "python.exe"

        return self.environment_path / "bin" / "python"

    @property
    def site_packages(self) -> Path:
        self.validate()

        result = subprocess.run(  # noqa: S603
            [
                str(self.python),
                "-c",
                "import sysconfig; print(sysconfig.get_path('purelib'))",
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        return Path(result.stdout.strip())

    def validate(self) -> None:
        """Validate that the plugin environment exists and is usable."""
        if not self.environment_path.is_dir():
            raise PluginRepositoryError(  # noqa: TRY003
                f"Plugin environment does not exist: {self.environment_path}",
                path=self.repository_path,
            )

        if not self.python.is_file():
            raise PluginRepositoryError(  # noqa: TRY003
                f"Plugin Python executable does not exist: {self.python}",
                path=self.repository_path,
            )
