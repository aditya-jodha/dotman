# ruff: noqa: S101, ARG005
# pyright: reportPrivateUsage=false

import sys
from collections.abc import Iterator
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from pytest import CaptureFixture, MonkeyPatch

import dotman.cli.app.add as cli
from dotman.api import Application


def make_responses(seq: Iterator[str]):
    it = iter(seq)

    def responder() -> str:
        try:
            return next(it)
        except StopIteration:
            raise KeyboardInterrupt  # force exit instead of infinite loop  # noqa: B904

    return responder


@pytest.fixture
def fake_dotman(monkeypatch: MonkeyPatch):
    fake = MagicMock()
    fake.add.return_value.preview.return_value.warnings = ["warn1"]
    fake.add.return_value.preview.return_value.package_created = True
    monkeypatch.setattr("dotman.cli.app.add.Dotman", lambda: fake)
    return fake


class TestHelperFunctions:
    @staticmethod
    def test_get_user_choice_yes(monkeypatch: MonkeyPatch):
        monkeypatch.setattr(cli, "_get_single_key_safe", lambda: "y")
        assert cli.get_user_choice() is True

    @staticmethod
    def test_get_user_choice_no(monkeypatch: MonkeyPatch):
        monkeypatch.setattr(cli, "_get_single_key_safe", lambda: "n")
        assert cli.get_user_choice() is False

    @staticmethod
    def test_get_user_choice_invalid_then_yes(
        monkeypatch: MonkeyPatch, capsys: CaptureFixture[str]
    ):
        responses = iter(["x", "y"])
        monkeypatch.setattr(cli, "_get_single_key_safe", make_responses(responses))

        result = cli.get_user_choice()
        out = capsys.readouterr().out

        assert result is True
        assert "Invalid choice" in out

    @staticmethod
    def test_get_user_choice_invalid_then_no(monkeypatch: MonkeyPatch, capsys: CaptureFixture[str]):

        monkeypatch.setattr(cli, "_get_single_key_safe", make_responses(iter(["x", "n"])))

        result = cli.get_user_choice()
        out = capsys.readouterr().out

        assert result is False
        assert "Invalid choice" in out

    @staticmethod
    def test_get_user_choice_keyboard_interrupt(monkeypatch: MonkeyPatch):
        def raise_interrupt():
            raise KeyboardInterrupt

        monkeypatch.setattr(cli, "_get_single_key_safe", raise_interrupt)

        with pytest.raises(KeyboardInterrupt):
            cli.get_user_choice()

    @staticmethod
    def test_multiple_invalid_inputs(monkeypatch: MonkeyPatch, capsys: CaptureFixture[str]) -> None:
        responses = iter(["x", "z", "y"])
        monkeypatch.setattr(cli, "_get_single_key_safe", lambda: next(responses))
        result: bool = cli.get_user_choice()
        out: str = capsys.readouterr().out
        assert result is True
        assert out.count("Invalid choice") == 2

    @staticmethod
    def test_case_insensitivity(monkeypatch: MonkeyPatch) -> None:
        monkeypatch.setattr(cli, "_get_single_key_safe", lambda: "Y")
        assert cli.get_user_choice() is True
        monkeypatch.setattr(cli, "_get_single_key_safe", lambda: "N")
        assert cli.get_user_choice() is False

    @staticmethod
    def test_get_user_choice_ctrl_c(monkeypatch: MonkeyPatch):
        monkeypatch.setattr(
            cli,
            "_get_single_key_safe",
            lambda: (_ for _ in ()).throw(KeyboardInterrupt),
        )
        with pytest.raises(KeyboardInterrupt):
            cli.get_user_choice()


class TestHelperOfHelperFunction:
    @staticmethod
    def test__get_single_key_safe_returns_char(monkeypatch: MonkeyPatch):
        # Patch sys.stdin.read to return 'a'
        monkeypatch.setattr(sys.stdin, "read", lambda n: "a")
        monkeypatch.setattr(sys.stdin, "fileno", lambda: 0)

        # Patch termios and tty functions to no-ops
        monkeypatch.setattr(cli.termios, "tcgetattr", lambda fd: ["old"])
        monkeypatch.setattr(cli.termios, "tcsetattr", lambda fd, when, settings: None)
        monkeypatch.setattr(cli.tty, "setraw", lambda fd: None)

        result = cli._get_single_key_safe()
        assert result == "a"

    @staticmethod
    def test__get_single_key_safe_ctrl_c(monkeypatch: MonkeyPatch):
        # Patch sys.stdin.read to return Ctrl+C
        monkeypatch.setattr(sys.stdin, "read", lambda n: "\x03")
        monkeypatch.setattr(sys.stdin, "fileno", lambda: 0)

        monkeypatch.setattr(cli.termios, "tcgetattr", lambda fd: ["old"])
        monkeypatch.setattr(cli.termios, "tcsetattr", lambda fd, when, settings: None)
        monkeypatch.setattr(cli.tty, "setraw", lambda fd: None)

        with pytest.raises(KeyboardInterrupt):
            cli._get_single_key_safe()


def test_add_requires_package_name(tmp_path: Path):
    file = tmp_path / "f.txt"
    file.write_text("hello")
    with patch.object(cli.console, "print") as mock_print:
        cli.add(file, None)
        mock_print.assert_any_call("Package name is required to add a file.", style="red")


def test_add_with_warnings_and_cancel(tmp_path: Path, monkeypatch: MonkeyPatch):
    file = tmp_path / "f.txt"
    file.write_text("hello")

    fake_operation = MagicMock()
    fake_operation.preview.return_value.warnings = ["warn1"]
    fake_operation.preview.return_value.package_created = False

    fake_dotman = MagicMock()
    fake_dotman.add.return_value = fake_operation

    monkeypatch.setattr(
        Application,
        "get_dotman",
        lambda: fake_dotman,
    )
    monkeypatch.setattr(cli, "get_user_choice", lambda: False)

    with patch.object(cli.console, "print") as mock_print:
        cli.add(file, "mypkg")

    mock_print.assert_any_call("Operation cancelled by user.", style="red")
    fake_operation.add.assert_not_called()
    fake_operation.commit.assert_not_called()
    fake_operation.rollback_changes.assert_not_called()


def test_add_with_warnings_and_continue_commit(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
):
    file = tmp_path / "f.txt"
    file.write_text("hello")

    fake_operation = MagicMock()
    fake_operation.preview.return_value.warnings = ["warn1"]
    fake_operation.preview.return_value.package_created = True
    fake_operation.tree.return_value = "TREE"

    fake_dotman = MagicMock()
    fake_dotman.add.return_value = fake_operation

    monkeypatch.setattr(
        Application,
        "get_dotman",
        lambda: fake_dotman,
    )

    choices = iter([True, True])
    monkeypatch.setattr(cli, "get_user_choice", lambda: next(choices))

    with patch.object(cli.console, "print") as mock_print:
        cli.add(file, "mypkg")

    fake_operation.add.assert_called_once()
    fake_operation.commit.assert_called_once()
    fake_operation.rollback_changes.assert_not_called()

    mock_print.assert_any_call(
        "Changes committed successfully.",
        style="green",
    )


def test_add_with_no_warnings_and_rollback(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
):
    file = tmp_path / "f.txt"
    file.write_text("hello")

    fake_operation = MagicMock()
    fake_operation.preview.return_value.warnings = []
    fake_operation.preview.return_value.package_created = False
    fake_operation.tree.return_value = "TREE"

    fake_dotman = MagicMock()
    fake_dotman.add.return_value = fake_operation

    monkeypatch.setattr(
        Application,
        "get_dotman",
        lambda: fake_dotman,
    )
    monkeypatch.setattr(cli, "get_user_choice", lambda: False)

    with patch.object(cli.console, "print") as mock_print:
        cli.add(file, "mypkg")

    fake_operation.add.assert_called_once()
    fake_operation.commit.assert_not_called()
    fake_operation.rollback_changes.assert_called_once()

    mock_print.assert_any_call(
        "Files restored successfully.",
        style="yellow",
    )


def test_add_keyboard_interrupt_on_commit(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
):
    file = tmp_path / "f.txt"
    file.write_text("hello")

    fake_operation = MagicMock()
    fake_operation.preview.return_value.warnings = []
    fake_operation.preview.return_value.package_created = False
    fake_operation.tree.return_value = "TREE"

    fake_dotman = MagicMock()
    fake_dotman.add.return_value = fake_operation

    monkeypatch.setattr(
        Application,
        "get_dotman",
        lambda: fake_dotman,
    )

    def raise_keyboard_interrupt():
        raise KeyboardInterrupt

    monkeypatch.setattr(cli, "get_user_choice", raise_keyboard_interrupt)

    with patch.object(cli.console, "print") as mock_print:
        cli.add(file, "mypkg")

    fake_operation.add.assert_called_once()
    fake_operation.commit.assert_not_called()
    fake_operation.rollback_changes.assert_called_once()

    mock_print.assert_any_call(
        "Files restored successfully.",
        style="yellow",
    )
