# ruff: noqa: S101
from pathlib import Path

import pytest

from dotman.core.linker import LinkAction, Linker, LinkResult


@pytest.fixture
def tmp_dirs(tmp_path: Path) -> tuple[Path, Path]:
    home: Path = tmp_path / "home"
    backup: Path = tmp_path / "backup"
    home.mkdir()
    return home, backup


def test_link_new_file(tmp_dirs: tuple[Path, Path]) -> None:
    home, backup = tmp_dirs
    source: Path = home / "source.txt"
    source.write_text("hello")
    target: Path = home / "target.txt"

    linker: Linker = Linker(home, backup)
    result: LinkResult = linker.execute(source, target)

    assert result.action == LinkAction.LINK
    assert target.is_symlink()
    assert target.resolve() == source


def test_skip_existing_symlink(tmp_dirs: tuple[Path, Path]) -> None:
    home, backup = tmp_dirs
    source: Path = home / "source.txt"
    source.write_text("hello")
    target: Path = home / "target.txt"
    target.symlink_to(source)

    linker: Linker = Linker(home, backup)
    result: LinkResult = linker.execute(source, target)

    assert result.action == LinkAction.SKIP
    assert result.status == "ok"
    assert "already linked" in result.message


def test_fix_wrong_symlink(tmp_dirs: tuple[Path, Path]) -> None:
    home, backup = tmp_dirs
    source: Path = home / "source.txt"
    source.write_text("hello")
    wrong: Path = home / "wrong.txt"
    wrong.write_text("oops")
    target: Path = home / "target.txt"
    target.symlink_to(wrong)

    linker: Linker = Linker(home, backup)
    result: LinkResult = linker.execute(source, target)

    assert result.action == LinkAction.FIX
    assert target.is_symlink()
    assert target.resolve() == source


def test_backup_and_link(tmp_dirs: tuple[Path, Path]) -> None:
    home, backup = tmp_dirs
    source: Path = home / "source.txt"
    source.write_text("hello")
    target: Path = home / "target.txt"
    target.write_text("existing")

    linker: Linker = Linker(home, backup)
    result: LinkResult = linker.execute(source, target)

    assert result.action == LinkAction.BACKUP_AND_LINK
    backups: list[Path] = list(backup.glob("target.txt.*"))
    assert backups, "Backup file not created"
    assert target.is_symlink()
    assert target.resolve() == source


def test_dry_run(tmp_dirs: tuple[Path, Path]) -> None:
    home, backup = tmp_dirs
    source: Path = home / "source.txt"
    source.write_text("hello")
    target: Path = home / "target.txt"

    linker: Linker = Linker(home, backup, dry_run=True)
    result: LinkResult = linker.execute(source, target)

    assert result.status == "dry-run"
    assert not target.exists()


def test_error_handling(
    tmp_dirs: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    home, backup = tmp_dirs
    source: Path = home / "source.txt"
    source.write_text("hello")
    target: Path = home / "target.txt"

    linker: Linker = Linker(home, backup)

    # force symlink_to to raise
    def fake_symlink_to(self: Path, other: Path) -> None:  # noqa: ARG001
        raise OSError("fail")

    monkeypatch.setattr(Path, "symlink_to", fake_symlink_to)

    result: LinkResult = linker.execute(source, target)
    assert result.status == "error"
    assert "fail" in result.message
