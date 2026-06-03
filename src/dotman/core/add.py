import tomllib
from pathlib import Path

from dotman.core.config import TEMP_LOG_FILE, StrPath


def sanitize_package_name(package: StrPath) -> Path:
    """Sanitizes the package name by replacing spaces with underscores and converting to lowercase."""  # noqa: E501
    sanitized_package = str(package).replace(" ", "_").lower().strip()
    return Path(sanitized_package.replace("/", "_").replace("\\", "_"))


class LogBook:
    """It will write a temp logs in form of toml of transfered files so user can easily
    restore the files if something goes wrong."""

    def __init__(self, log_file: StrPath | None = None):
        self.log_file = Path(log_file) if log_file else TEMP_LOG_FILE

    def clear_log(self):
        """Clears the log file."""
        if self.log_file.exists():
            self.log_file.unlink()

    def create_log(self):
        """Creates the log file if it does not exist."""
        if not self.log_file.exists():
            self.log_file.touch()
        else:
            raise FileExistsError(f"Log file '{self.log_file}' already exists.")  # noqa: TRY003

    def show_log(self):
        if self.log_file.exists():
            with self.log_file.open("r") as f:
                return f.read()
        else:
            return "No log entries found."

    def write_log(self, original_path: Path, new_path: Path):
        log_entry = f'[[files]]\noriginal_path = "{original_path}"\nnew_path = "{new_path}"\n\n'
        with self.log_file.open("a") as f:
            f.write(log_entry)

    def restore_files(self):
        with self.log_file.open("rb") as f:
            data = tomllib.load(f)
        _data = data.get("files", [])
        for entry in _data:
            original_path = Path(entry["original_path"])
            new_path = Path(entry["new_path"])
            if new_path.exists():
                new_path.rename(original_path)
        self.clear_log()


class AddFiles:
    """Class to handle adding files to the dotfiles directory."""

    def __init__(
        self,
        home_dir: Path,
        dotfiles_dir: Path,
        file: Path,
        package: StrPath,
        logbook: LogBook,
    ):
        self.home_dir = home_dir
        self.dotfiles_dir = dotfiles_dir
        self.file = file
        self.package = sanitize_package_name(package)
        self.log_book = logbook

    @property
    def is_dir(self) -> bool:
        return self.file.is_dir()

    @property
    def package_exists(self) -> bool:
        """Checks if the package directory exists in the dotfiles directory."""
        return (self.dotfiles_dir / self.package).exists()

    def create_package(self):
        """Creates the directory inside dotfiles"""
        pkg_to_create = self.dotfiles_dir / self.package
        pkg_to_create.mkdir(parents=True, exist_ok=False)

    def move_dir_to_dotfiles(self):
        """Moves the specified directory to the dotfiles directory.
        by creating a dir into dotfiles named as package"""
        # since we are moving the whole directory, we will move it to the package directory directly
        self.move_file_to_dotfiles()

    def move_file_to_dotfiles(self):
        """Moves the specified file to the dotfiles directory.
        by creating a dir into dotfiles named as package"""
        if not self.file.exists():
            raise FileNotFoundError(self.file)

        destination = self.dotfiles_dir / self.package / self.file.relative_to(self.home_dir)

        # Writes log for backup
        self.log_book.write_log(self.file, destination)

        # Ensure the parent directory of the destination exists before moving the file
        destination.parent.mkdir(parents=True, exist_ok=True)

        # Move the file to the destination
        self.file.rename(destination)

    def file_exists_in_package(self) -> bool:
        """Checks if the file already exists in the package directory."""
        return (self.dotfiles_dir / self.package / self.file.relative_to(self.home_dir)).exists()

    def has_files_in_package(self):
        """Checks if the log file has any entries for files in the package."""
        path = Path(self.dotfiles_dir / self.package)

        # Returns True if at least one item inside is a regular file
        return any(item.is_file() for item in path.iterdir())
