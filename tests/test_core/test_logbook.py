# ruff: noqa: S101
from dataclasses import dataclass
from pathlib import Path

import pytest

from dotman.core.add import LogBook


@dataclass
class LabPaths:
    home: Path
    dotfiles_dir: Path
    profile: str

    config_path: Path


@pytest.fixture
def lab(tmp_path: Path) -> LabPaths:
    home = tmp_path / "home"
    dotfiles = tmp_path / "dotfiles"
    config_path = tmp_path / "config.yml"
    profile = "default"

    home.mkdir()
    dotfiles.mkdir()

    return LabPaths(
        home=home, dotfiles_dir=dotfiles, profile=profile, config_path=config_path
    )


def _show_log(log_book: LogBook):
    with log_book.log_file.open("r") as f:
        return f.read()


class TestLogbook:
    @pytest.fixture(autouse=True)
    def set_up(self, lab: LabPaths):
        self.log_book = LogBook(lab.config_path)
        self.lab = lab

    def test_create_log(self):
        self.log_book.create_log()
        assert self.log_book.log_file.exists()

    def test_create_log_if_exists(self):
        self.log_book.create_log()
        with pytest.raises(FileExistsError):
            self.log_book.create_log()

    def test_clear_log(self):
        self.log_book.create_log()
        assert self.log_book.log_file.exists()

        self.log_book.clear_log()
        assert not self.log_book.log_file.exists()

    def test_write_log(self):
        self.log_book.create_log()
        assert self.log_book.log_file.exists()

        source = self.lab.home / "file.txt"
        destination = (
            self.lab.dotfiles_dir
            / "profiles"
            / self.lab.profile
            / "testpkg"
            / "file.txt"
        )

        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.touch()

        self.log_book.write_log(source, destination)

        prompt = (
            f'[[files]]\noriginal_path = "{source}"\nnew_path = "{destination}"\n\n'
        )

        assert _show_log(self.log_book) == prompt

    def test_restore_files(self):
        self.log_book.create_log()
        assert self.log_book.log_file.exists()

        source = self.lab.home / "file.txt"
        destination = (
            self.lab.dotfiles_dir
            / "profiles"
            / self.lab.profile
            / "testpkg"
            / "file.txt"
        )

        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.touch()

        self.log_book.write_log(source, destination)
        self.log_book.restore_files()

        assert not self.log_book.log_file.exists()
        assert not destination.exists()
        assert source.exists()
