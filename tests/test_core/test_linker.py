# ruff: noqa: S101
# death_tests/test_linker_unit.py
import shutil
import time
from pathlib import Path

import pytest

from dotman.core.doctor import SymlinkStatus
from dotman.core.linker import LinkAction, Linker, LinkPair, LinkResult, UnlinkResult


@pytest.fixture
def tmp_dirs(tmp_path: Path) -> tuple[Path, Path]:
    home: Path = tmp_path / "home"
    backup: Path = tmp_path / "backup"
    home.mkdir()
    return home, backup


class TestDataClass:
    def test_unlinkresult_as_dict(self):
        source: Path = Path("source")
        target: Path = Path("target")
        result: UnlinkResult = UnlinkResult(
            source=source,
            target=target,
            status=SymlinkStatus.OK,
            removed=True,
        )

        assert result.as_dict() == {
            "source": str(source),
            "target": str(target),
            "status": "ok",
            "removed": True,
        }

    def test_linkresult_as_dict(self):
        source: Path = Path("source")
        target: Path = Path("target")
        result: LinkResult = LinkResult(
            source=source,
            target=target,
            action="link",
            status="ok",
            message="linked successfully",
        )

        assert result.as_dict() == {
            "source": str(source),
            "target": str(target),
            "action": "link",
            "status": "ok",
            "message": "linked successfully",
            "timestamp": result.timestamp,
        }


def test_resolve_returns_absolute_source_and_expanded_target(tmp_path: Path):
    home = tmp_path / "home"
    home.mkdir()
    linker = Linker(home_dir=home, backup_dir=tmp_path / "backup", dry_run=True)

    # create a source file using a relative path
    src_rel = Path("somefile.txt")
    (home / src_rel).write_text("x")

    # target uses ~ (expanduser) to ensure expanduser is applied
    target = Path("target.txt")

    source_abs, target_expanded = linker.resolve(home / src_rel, target)
    assert source_abs.is_absolute()
    # resolve() should have returned an absolute path for source
    assert source_abs == (home / src_rel).resolve()
    # target is expanded but not resolved (no .resolve() in code)
    assert target_expanded == target.expanduser()


@pytest.mark.parametrize("setup", ["linked_same", "linked_other", "file_exists", "missing"])
def test_analyze_various_states(tmp_path: Path, setup: str):
    home = tmp_path / "home"
    home.mkdir()
    linker = Linker(home_dir=home, backup_dir=tmp_path / "backup", dry_run=True)

    source = home / "src.txt"
    source.write_text("content")

    target = home / "target.txt"

    if setup == "linked_same":
        # create symlink pointing to source -> should SKIP
        target.symlink_to(source)
        assert linker.analyze(source, target) == LinkAction.SKIP

    elif setup == "linked_other":
        # create another file and symlink pointing elsewhere -> FIX
        other = home / "other.txt"
        other.write_text("other")
        target.symlink_to(other)
        assert linker.analyze(source, target) == LinkAction.FIX

    elif setup == "file_exists":
        # create a regular file -> BACKUP_AND_LINK
        target.write_text("old")
        assert linker.analyze(source, target) == LinkAction.BACKUP_AND_LINK

    elif setup == "missing":
        # target does not exist -> LINK
        if target.exists() or target.is_symlink():
            target.unlink()
        assert linker.analyze(source, target) == LinkAction.LINK


def test_backup_moves_existing_target(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    home = tmp_path / "home"
    home.mkdir()
    backup_dir = tmp_path / "backups"
    # create a target file
    target = home / "file.txt"
    target.write_text("hello")

    # freeze time for deterministic backup name
    fixed_time = 1_700_000_000
    monkeypatch.setattr(time, "time", lambda: fixed_time)

    linker = Linker(home_dir=home, backup_dir=backup_dir, dry_run=False)
    # call backup
    linker.backup(target)

    # backup file should exist in backup_dir with timestamp suffix
    expected_name = f"{target.name}.{int(fixed_time)}"
    found = list(backup_dir.glob(f"{target.name}.*"))
    assert len(found) == 1
    assert found[0].name == expected_name
    # original target should no longer exist
    assert not target.exists()

    assert linker.backup(target) is None


def test_execute_dry_run_returns_dry_run_result(tmp_path: Path):
    home = tmp_path / "home"
    home.mkdir()
    backup_dir = tmp_path / "backups"
    linker = Linker(home_dir=home, backup_dir=backup_dir, dry_run=True)

    source = home / "src.txt"
    source.write_text("x")
    target = home / "target.txt"

    result = linker.execute(source, target)
    assert isinstance(result, LinkResult)
    assert result.status == "dry-run"
    assert result.message == "no changes made"


def test_execute_link_and_backup_and_link_and_skip_and_fix(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    home = tmp_path / "home"
    home.mkdir()
    backup_dir = tmp_path / "backups"

    # freeze time for deterministic backup name
    fixed_time = 1_700_000_001
    monkeypatch.setattr(time, "time", lambda: fixed_time)

    linker = Linker(home_dir=home, backup_dir=backup_dir, dry_run=False)

    # 1) LINK: target missing -> should create symlink
    src1 = home / "s1.txt"
    src1.write_text("1")
    tgt1 = home / "t1.txt"
    res1 = linker.execute(src1, tgt1)
    assert res1.status == "ok"
    assert tgt1.is_symlink()
    assert tgt1.resolve() == src1.resolve()

    # cleanup
    tgt1.unlink()

    # 2) BACKUP_AND_LINK: target exists as file -> backup then link
    src2 = home / "s2.txt"
    src2.write_text("2")
    tgt2 = home / "t2.txt"
    tgt2.write_text("old")
    res2 = linker.execute(src2, tgt2)
    assert res2.status == "ok"
    # backup created
    backup_candidates = list(backup_dir.glob("t2.txt.*"))
    assert len(backup_candidates) == 1
    assert tgt2.is_symlink()
    assert tgt2.resolve() == src2.resolve()

    # cleanup
    tgt2.unlink()
    shutil.rmtree(backup_dir)

    # 3) SKIP: target is symlink already pointing to source
    src3 = home / "s3.txt"
    src3.write_text("3")
    tgt3 = home / "t3.txt"
    tgt3.symlink_to(src3)
    res3 = linker.execute(src3, tgt3)
    assert res3.status == "ok"
    assert res3.message == "already linked"

    # 4) FIX: target is symlink pointing elsewhere -> should unlink and relink
    src4 = home / "s4.txt"
    src4.write_text("4")
    other = home / "other.txt"
    other.write_text("other")
    tgt4 = home / "t4.txt"
    tgt4.symlink_to(other)
    res4 = linker.execute(src4, tgt4)
    assert res4.status == "ok"
    assert tgt4.is_symlink()
    assert tgt4.resolve() == src4.resolve()


def test_link_batch_returns_results(tmp_path: Path):
    home = tmp_path / "home"
    home.mkdir()
    backup_dir = tmp_path / "backups"
    linker = Linker(home_dir=home, backup_dir=backup_dir, dry_run=False)

    s1 = home / "a.txt"
    s2 = home / "b.txt"
    s1.write_text("a")
    s2.write_text("b")
    t1 = home / "ta.txt"
    t2 = home / "tb.txt"

    pairs = [
        LinkPair(source=s1, target=t1, relative_source=s1),
        LinkPair(source=s2, target=t2, relative_source=s2),
    ]
    results = linker.link(pairs)
    assert isinstance(results, list)
    assert len(results) == 2
    assert all(isinstance(r, LinkResult) for r in results)
    assert t1.is_symlink() and t2.is_symlink()


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


def test_error_handling(tmp_dirs: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch) -> None:
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


# death_tests/test_linker_backup_dir.py


def test_backup_dir_relative_is_created_under_home(tmp_path: Path):
    """
    If backup_dir is a relative path, Linker should treat it as relative to home_dir
    and create the directory when dry_run is False.
    """
    home = tmp_path / "home"
    home.mkdir()
    # relative backup dir (not absolute)
    rel_backup = Path("backups")

    linker = Linker(home_dir=home, backup_dir=rel_backup, dry_run=False)

    # expected backup dir is home / rel_backup
    expected = home / rel_backup
    assert linker.backup_dir == expected
    assert expected.exists() and expected.is_dir()


def test_backup_dir_relative_not_created_in_dry_run(tmp_path: Path):
    """
    When dry_run is True, Linker should not create the backup directory even if
    backup_dir is relative.
    """
    home = tmp_path / "home"
    home.mkdir()
    rel_backup = Path("backups")

    linker = Linker(home_dir=home, backup_dir=rel_backup, dry_run=True)

    expected = home / rel_backup
    # attribute should still be normalized to home / rel_backup
    assert linker.backup_dir == expected
    # but directory must not be created in dry-run mode
    assert not expected.exists()
