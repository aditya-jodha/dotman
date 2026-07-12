# ruff: noqa: S101, ARG005
from pathlib import Path
from unittest.mock import MagicMock, patch

from pytest import MonkeyPatch

from dotman.core.add import SymlinkStatus
from dotman.core.service.add_service import AddService, Preview


# ---------- Helpers ----------
def setup_addservice(tmp_path: Path):
    file = tmp_path / "file.txt"
    file.write_text("hello")

    # Patch load_config and resolve_profile to avoid real config
    with (
        patch("dotman.core.config.config.DotmanConfig.load") as mock_load,
        patch("dotman.core.get_internal_data.resolve_profile") as mock_resolve,
        patch("dotman.core.get_internal_data.InternalData.load") as mock_internal,
    ):
        mock_load.return_value = MagicMock(home_dir=tmp_path, dotfiles_dir=tmp_path)
        mock_resolve.return_value = "default"
        mock_internal.return_value = MagicMock()

        return AddService(
            file=file,
            package="mypkg",
            home_dir=tmp_path,
            dotfiles_dir=tmp_path,
            profile="default",
        )


# ---------- Tests ----------


def test_validate_calls_addfiles_validate(tmp_path: Path):
    service = setup_addservice(tmp_path)
    service.add_files.validate = MagicMock()
    service.validate()
    service.add_files.validate.assert_called_once()


def test_preview_returns_warnings_and_package_created(tmp_path: Path, monkeypatch: MonkeyPatch):
    service = setup_addservice(tmp_path)

    # Mock validate and symlink checks
    service.add_files.validate = MagicMock()
    service.add_files.validate_directory_symlinks = MagicMock(
        return_value=[
            MagicMock(status=SymlinkStatus.ERROR, message="bad link"),
            MagicMock(status=SymlinkStatus.OK, message="fine link"),
        ]
    )

    # Patch the property package_exists to return False
    monkeypatch.setattr(type(service.add_files), "package_exists", property(lambda self: False))

    preview = service.preview()
    assert isinstance(preview, Preview)
    assert preview.warnings == ["bad link"]
    assert preview.package_created is True


def test_add_creates_package_and_moves_file(tmp_path: Path, monkeypatch: MonkeyPatch):
    service = setup_addservice(tmp_path)

    monkeypatch.setattr(type(service.add_files), "package_exists", property(lambda self: False))

    service.add_files.create_package = MagicMock()
    service.add_files.move_file_to_dotfiles = MagicMock()

    service.add()
    service.add_files.create_package.assert_called_once()
    service.add_files.move_file_to_dotfiles.assert_called_once()


def test_add_skips_create_if_exists(tmp_path: Path, monkeypatch: MonkeyPatch):
    service = setup_addservice(tmp_path)

    # Patch property to simulate package already existing
    monkeypatch.setattr(type(service.add_files), "package_exists", property(lambda self: True))

    service.add_files.create_package = MagicMock()
    service.add_files.move_file_to_dotfiles = MagicMock()

    service.add()
    service.add_files.create_package.assert_not_called()
    service.add_files.move_file_to_dotfiles.assert_called_once()


def test_commit_clears_journal(tmp_path: Path):
    service = setup_addservice(tmp_path)
    service.journal.clear = MagicMock()
    service.commit()
    service.journal.clear.assert_called_once()


def test_rollback_changes_calls_journal_and_delete(tmp_path: Path):
    service = setup_addservice(tmp_path)
    service.journal.rollback = MagicMock()
    service.add_files.delete_empty_package = MagicMock()
    service.rollback_changes()
    service.journal.rollback.assert_called_once()
    service.add_files.delete_empty_package.assert_called_once()


def test_tree_calls_print_beautiful_directory(tmp_path: Path):
    service = setup_addservice(tmp_path)
    with patch("dotman.core.service.add_service.print_beautiful_directory") as mock_print:
        service.tree()
        mock_print.assert_called_once_with(service.add_files.profile_root)
