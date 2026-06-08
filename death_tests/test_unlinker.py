# ruff: noqa: S101
from pathlib import Path

import pytest

from dotman.core.doctor import SymlinkStatus
from dotman.core.linker import LinkPair, Unlinker, UnlinkResult


@pytest.fixture
def tmp_dirs(tmp_path: Path) -> tuple[Path, Path]:
    home = tmp_path / "home"
    dotfiles = tmp_path / "dotfiles"
    home.mkdir()
    dotfiles.mkdir()
    return home, dotfiles


def make_pair(home: Path, dotfiles: Path, filename: str) -> LinkPair:
    source = dotfiles / filename
    source.write_text("hello")
    target = home / filename
    return LinkPair(source=source, relative_source=Path(filename), target=target)


def test_unlink_ok_symlink(tmp_dirs: tuple[Path, Path]) -> None:
    home, dotfiles = tmp_dirs
    pair = make_pair(home, dotfiles, "file.txt")
    pair.target.symlink_to(pair.source)

    unlinker = Unlinker()
    results: list[UnlinkResult] = unlinker.unlink([pair])

    assert results[0].status == SymlinkStatus.OK
    assert results[0].removed is True
    assert not pair.target.exists()


def test_unlink_broken_symlink(tmp_dirs: tuple[Path, Path]) -> None:
    home, dotfiles = tmp_dirs
    source = dotfiles / "missing.txt"
    target = home / "broken.txt"
    target.symlink_to(source)  # source does not exist
    pair = LinkPair(source=source, relative_source=Path("missing.txt"), target=target)

    unlinker = Unlinker()
    results = unlinker.unlink([pair])

    assert results[0].status == SymlinkStatus.BROKEN_SYMLINK
    assert results[0].removed is True
    assert not target.exists()


def test_unlink_wrong_source(tmp_dirs: tuple[Path, Path]) -> None:
    home, dotfiles = tmp_dirs
    source = dotfiles / "file.txt"
    source.write_text("hello")
    wrong = dotfiles / "wrong.txt"
    wrong.write_text("oops")
    target = home / "file.txt"
    target.symlink_to(wrong)
    pair = LinkPair(source=source, relative_source=Path("file.txt"), target=target)

    unlinker = Unlinker()
    results = unlinker.unlink([pair])

    assert results[0].status == SymlinkStatus.WRONG_SOURCE
    assert results[0].removed is False
    assert target.exists()


def test_unlink_regular_file(tmp_dirs: tuple[Path, Path]) -> None:
    home, dotfiles = tmp_dirs
    source = dotfiles / "file.txt"
    source.write_text("hello")
    target = home / "file.txt"
    target.write_text("not a symlink")
    pair = LinkPair(source=source, relative_source=Path("file.txt"), target=target)

    unlinker = Unlinker()
    results = unlinker.unlink([pair])

    assert results[0].status == SymlinkStatus.NOT_A_SYMLINK
    assert results[0].removed is False
    assert target.exists()


def test_unlink_missing_target(tmp_dirs: tuple[Path, Path]) -> None:
    home, dotfiles = tmp_dirs
    source = dotfiles / "file.txt"
    source.write_text("hello")
    target = home / "file.txt"  # never created
    pair = LinkPair(source=source, relative_source=Path("file.txt"), target=target)

    unlinker = Unlinker()
    results = unlinker.unlink([pair])

    assert results[0].status == SymlinkStatus.MISSING_TARGET
    assert results[0].removed is False


def test_unlink_multiple_pairs(tmp_dirs: tuple[Path, Path]) -> None:
    home, dotfiles = tmp_dirs
    # OK symlink
    ok_source = dotfiles / "ok.txt"
    ok_source.write_text("ok")
    ok_target = home / "ok.txt"
    ok_target.symlink_to(ok_source)
    ok_pair = LinkPair(ok_source, Path("ok.txt"), ok_target)

    # Broken symlink
    broken_source = dotfiles / "missing.txt"
    broken_target = home / "broken.txt"
    broken_target.symlink_to(broken_source)
    broken_pair = LinkPair(broken_source, Path("missing.txt"), broken_target)

    # Wrong source
    wrong_source = dotfiles / "right.txt"
    wrong_source.write_text("right")
    wrong_target = home / "wrong.txt"
    wrong_other = dotfiles / "other.txt"
    wrong_other.write_text("other")
    wrong_target.symlink_to(wrong_other)
    wrong_pair = LinkPair(wrong_source, Path("right.txt"), wrong_target)

    unlinker = Unlinker()
    results = unlinker.unlink([ok_pair, broken_pair, wrong_pair])

    assert len(results) == 3
    assert results[0].removed is True
    assert results[1].removed is True
    assert results[2].removed is False
