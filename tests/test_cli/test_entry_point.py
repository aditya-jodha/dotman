# ruff: noqa: S101

import sys
from unittest.mock import MagicMock

import pytest
from typer.testing import CliRunner

import dotman.__cli__ as cli
from dotman.__cli__ import app

runner = CliRunner()


def test_keyboard_interrupt_handling(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify that KeyboardInterrupt prints a safe message and exits with 0."""

    # Create type-safe mocks
    mock_print = MagicMock()
    mock_exit = MagicMock()
    mock_app = MagicMock(side_effect=KeyboardInterrupt)

    # Monkeypatch the live application variables
    monkeypatch.setattr(cli, "app", mock_app)
    monkeypatch.setattr(cli.console, "print", mock_print)
    monkeypatch.setattr(sys, "exit", mock_exit)

    # Execute the actual production main function to cover lines 15-19
    cli.main()

    # Assertions on the patched components
    mock_print.assert_called_once_with("\n[red]Process interrupted. Exiting safely.[/]")
    mock_exit.assert_called_once_with(0)


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
