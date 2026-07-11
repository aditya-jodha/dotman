# ruff: noqa: S101, ARG001, TRY003, ARG005
# pyright: reportPrivateUsage=false
from pathlib import Path
from typing import Any

import pytest

from dotman.core.utils.fs import FileSystemUtil
from dotman.errors.dotman_error import ExitCode


@pytest.fixture
def fs_util() -> FileSystemUtil:
    """Fixture providing a fresh instance of the FileSystemUtil class."""
    return FileSystemUtil()


class TestFileSystemUtil:
    def test_get_inode_key_success(self, fs_util: FileSystemUtil, tmp_path: Path) -> None:
        test_file = tmp_path / "file.txt"
        test_file.write_text("data")
        stat = test_file.stat(follow_symlinks=False)
        expected = (stat.st_dev, stat.st_ino)
        assert fs_util.get_inode_key(test_file) == expected

    def test_get_inode_key_oserror(
        self, fs_util: FileSystemUtil, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        test_file = tmp_path / "missing.txt"

        def mock_stat(self: Path, follow_symlinks: bool = False) -> Any:
            raise OSError("Permission denied")

        monkeypatch.setattr(Path, "stat", mock_stat)
        assert fs_util.get_inode_key(test_file) is None

    def test_is_valid_file_or_link_real_file(self, fs_util: FileSystemUtil, tmp_path: Path) -> None:
        f = tmp_path / "real.txt"
        f.write_text("content")
        assert fs_util.is_valid_file_or_link(f) is True

    def test_is_valid_file_or_link_directory(self, fs_util: FileSystemUtil, tmp_path: Path) -> None:
        d = tmp_path / "dir"
        d.mkdir()
        assert fs_util.is_valid_file_or_link(d) is False

    def test_is_valid_file_or_link_valid_symlink(
        self, fs_util: FileSystemUtil, tmp_path: Path
    ) -> None:
        target = tmp_path / "target.txt"
        target.write_text("hello")
        link = tmp_path / "link.txt"
        link.symlink_to(target)
        assert fs_util.is_valid_file_or_link(link) is True

    def test_is_valid_file_or_link_broken_symlink(
        self, fs_util: FileSystemUtil, tmp_path: Path
    ) -> None:
        link = tmp_path / "broken.txt"
        link.symlink_to(tmp_path / "missing.txt")
        assert fs_util.is_valid_file_or_link(link) is False

    def test_is_valid_file_or_link_symlink_oserror(
        self, fs_util: FileSystemUtil, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        target = tmp_path / "target.txt"
        target.write_text("hello")
        link = tmp_path / "link.txt"
        link.symlink_to(target)
        orig_is_file = Path.is_file

        def mock_is_file(self: Path) -> bool:
            if self == link:
                return False
            return orig_is_file(self)

        def mock_resolve(self: Path, strict: bool = False) -> Any:
            raise OSError("Locked location")

        monkeypatch.setattr(Path, "is_file", mock_is_file)
        monkeypatch.setattr(Path, "resolve", mock_resolve)
        assert fs_util.is_valid_file_or_link(link) is False

    def test_path_has_files_empty_directory(self, fs_util: FileSystemUtil, tmp_path: Path) -> None:
        assert fs_util.path_has_files(tmp_path) is False

    def test_path_has_files_nested_success(self, fs_util: FileSystemUtil, tmp_path: Path) -> None:
        nested = tmp_path / "sub" / "deep"
        nested.mkdir(parents=True)
        (nested / "payload.cfg").write_text("data")
        assert fs_util.path_has_files(tmp_path) is True

    def test_path_has_files_recursion_error(
        self, fs_util: FileSystemUtil, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        def mock_rglob(self: Path, pattern: str) -> Any:
            raise RecursionError("overflow")

        monkeypatch.setattr(Path, "rglob", mock_rglob)
        assert fs_util.path_has_files(tmp_path) is True

    def test_path_has_files_skips_duplicate_inodes(
        self, fs_util: FileSystemUtil, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        d1 = tmp_path / "d1"
        d1.mkdir()
        real_stat = d1.stat(follow_symlinks=False)
        fake_stat = type(real_stat)(
            (
                real_stat.st_mode,
                99999,
                88888,
                real_stat.st_nlink,
                real_stat.st_uid,
                real_stat.st_gid,
                real_stat.st_size,
                int(real_stat.st_atime),
                int(real_stat.st_mtime),
                int(real_stat.st_ctime),
            )
        )

        def mock_stat(self: Path, follow_symlinks: bool = False) -> Any:
            return fake_stat

        monkeypatch.setattr(Path, "stat", mock_stat)
        assert fs_util.path_has_files(tmp_path) is False

    def test_path_has_files_skips_ignored_patterns(self, tmp_path: Path) -> None:
        util = FileSystemUtil(ignore_patterns=[".git", "caches"])
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        (git_dir / "config").write_text("git core data")
        cache_dir = tmp_path / "sub" / "caches"
        cache_dir.mkdir(parents=True)
        (cache_dir / "temp.tmp").write_text("cache stuff")
        assert util(tmp_path) is False

    def test_path_has_files_processes_non_ignored_files(self, tmp_path: Path) -> None:
        util = FileSystemUtil(ignore_patterns=[".git"])
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        (git_dir / "config").write_text("git core data")
        valid_dir = tmp_path / "src"
        valid_dir.mkdir()
        (valid_dir / "main.py").write_text("print('hello')")
        assert util(tmp_path) is True

    # --- New coverage additions ---
    def test_call_operator_delegates(self, tmp_path: Path):
        f = tmp_path / "f.txt"
        f.write_text("hi")
        util = FileSystemUtil()
        assert util(tmp_path) is True

    def test_normalize_path_relative_and_expanduser(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        rel = Path("somefile")
        abs_path = FileSystemUtil.normalize_path(rel)
        assert abs_path.is_absolute()
        monkeypatch.setenv("HOME", str(tmp_path))
        user_path = Path("~")
        result = FileSystemUtil.normalize_path(user_path)
        assert result.is_absolute()

    def test_delete_empty_package_success_and_invalid(self, tmp_path: Path):
        profile = tmp_path / "profiles"
        pkg = profile / "mypkg"
        pkg.mkdir(parents=True)
        result = FileSystemUtil.delete_empty_package(profile, pkg / "dummy.txt")
        assert result == ExitCode.SUCCESS
        assert not pkg.exists()
        pkg.mkdir(parents=True)
        (pkg / "file.txt").write_text("data")
        result = FileSystemUtil.delete_empty_package(profile, pkg / "file.txt")
        assert result == ExitCode.INVALID_ARGUMENTS
        assert pkg.exists()

    def test_should_ignore_matches_and_non_matches(self, tmp_path: Path):
        util = FileSystemUtil(ignore_patterns=["ignoreme"])
        p = tmp_path / "ignoreme" / "f.txt"
        assert util._should_ignore(p) is True
        q = tmp_path / "other" / "f.txt"
        assert util._should_ignore(q) is False

    def test_path_has_files_skips_none_inode(
        self, fs_util: FileSystemUtil, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Force get_inode_key to return None so the loop continues without processing."""
        f = tmp_path / "f.txt"
        f.write_text("hello")

        # Patch get_inode_key to always return None
        monkeypatch.setattr(FileSystemUtil, "get_inode_key", lambda self, item: None)

        # Since inode_key is None, path_has_files should skip and return False
        assert fs_util.path_has_files(tmp_path) is False
