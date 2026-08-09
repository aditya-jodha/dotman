# ruff: noqa: S101

from unittest.mock import MagicMock

import pytest
import typer
from typer.testing import CliRunner

import dotman.__cli__ as cli
from dotman.__cli__ import app

runner = CliRunner()


def test_keyboard_interrupt_handling(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify that KeyboardInterrupt prints a safe message and exits with 130."""

    # Create type-safe mocks
    mock_print = MagicMock()
    mock_app = MagicMock(side_effect=KeyboardInterrupt)

    # Monkeypatch the live application variables
    monkeypatch.setattr(cli, "app", mock_app)
    monkeypatch.setattr(cli.console, "print", mock_print)

    # Execute and assert that typer.Exit(130) is raised
    with pytest.raises(typer.Exit) as exc_info:
        cli.main()

    # Assertions on code behavior
    assert exc_info.value.exit_code == 130
    mock_print.assert_called_once_with("\n[red]Process interrupted. Exiting safely.[/]")


def test_root_app_help():
    """Verify the main app launches and displays help text."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Manage dotman configuration." in result.output
    assert "Manage profiles." in result.output


def test_config_subcommand_help():
    """Verify the 'config' subcommand is registered and accessible."""
    result = runner.invoke(app, ["config", "--help"])
    assert result.exit_code == 0


def test_profile_subcommand_help():
    """Verify the 'profile' subcommand is registered and accessible."""
    result = runner.invoke(app, ["profile", "--help"])
    assert result.exit_code == 0
