# ruff: noqa: S101
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest

from dotman.core.utils.fs import FileSystemUtil

if TYPE_CHECKING:
    import os


@pytest.fixture
def fs_util() -> FileSystemUtil:
    """Fixture providing a fresh instance of the FileSystemUtil class."""
    return FileSystemUtil()


class TestFileSystemUtil:
    def test_get_inode_key_success(
        self, fs_util: FileSystemUtil, tmp_path: Path
    ) -> None:
        """Verify that get_inode_key returns the real dev and inode."""
        test_file = tmp_path / "file.txt"
        test_file.write_text("data")

        stat = test_file.stat(follow_symlinks=False)
        expected = (stat.st_dev, stat.st_ino)

        assert fs_util.get_inode_key(test_file) == expected

    def test_path_has_files_skips_ignored_patterns(self, tmp_path: Path) -> None:
        """Verify that files matching the ignore pattern are skipped entirely."""
        # Initialize the utility to explicitly ignore '.git' or 'caches' directories
        util_with_ignore = FileSystemUtil(ignore_patterns=[".git", "caches"])

        # Create a file inside an ignored folder structure
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        (git_dir / "config").write_text("git core data")

        # Create a file inside another ignored name variant
        cache_dir = tmp_path / "sub" / "caches"
        cache_dir.mkdir(parents=True)
        (cache_dir / "temp.tmp").write_text("temporary cache stuff")

        # The loop should hit the continue block for these files and find no payload
        assert util_with_ignore(tmp_path) is False

    def test_path_has_files_processes_non_ignored_files(self, tmp_path: Path) -> None:
        """Verify that files not matching the ignore pattern are processed normally."""
        util_with_ignore = FileSystemUtil(ignore_patterns=[".git"])

        # Create an ignored directory structure
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        (git_dir / "config").write_text("git core data")

        # Create a valid source file outside of the ignored tree
        valid_dir = tmp_path / "src"
        valid_dir.mkdir()
        (valid_dir / "main.py").write_text("print('hello')")

        # The loop will skip the git folder but find and process main.py successfully
        assert util_with_ignore(tmp_path) is True

    def test_get_inode_key_oserror(
        self, fs_util: FileSystemUtil, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Verify that get_inode_key returns None when stat raises an OSError."""
        test_file = tmp_path / "missing.txt"

        def mock_stat(self: Path, follow_symlinks: bool = False) -> Any:  # noqa: ARG001
            raise OSError("Permission denied")  # noqa: TRY003

        monkeypatch.setattr(Path, "stat", mock_stat)
        assert fs_util.get_inode_key(test_file) is None

    def test_is_valid_file_or_link_real_file(
        self, fs_util: FileSystemUtil, tmp_path: Path
    ) -> None:
        """Verify it returns True for regular physical files."""
        test_file = tmp_path / "real.txt"
        test_file.write_text("content")
        assert fs_util.is_valid_file_or_link(test_file) is True

    def test_is_valid_file_or_link_directory(
        self, fs_util: FileSystemUtil, tmp_path: Path
    ) -> None:
        """Verify it returns False for directories."""
        test_dir = tmp_path / "dir"
        test_dir.mkdir()
        assert fs_util.is_valid_file_or_link(test_dir) is False

    def test_is_valid_file_or_link_valid_symlink(
        self, fs_util: FileSystemUtil, tmp_path: Path
    ) -> None:
        """Verify it returns True for a symlink pointing to a valid file."""
        target = tmp_path / "target.txt"
        target.write_text("hello")
        link = tmp_path / "link.txt"
        link.symlink_to(target)
        assert fs_util.is_valid_file_or_link(link) is True

    def test_is_valid_file_or_link_broken_symlink(
        self, fs_util: FileSystemUtil, tmp_path: Path
    ) -> None:
        """Verify it returns False for a broken symlink targeting nothing."""
        link = tmp_path / "broken_link.txt"
        link.symlink_to(tmp_path / "non_existent.txt")
        assert fs_util.is_valid_file_or_link(link) is False

    def test_is_valid_file_or_link_symlink_oserror(
        self, fs_util: FileSystemUtil, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Verify it returns False when symlink resolution crashes with OSError."""
        target = tmp_path / "target.txt"
        target.write_text("hello")
        link = tmp_path / "link.txt"
        link.symlink_to(target)

        # 1. Force is_file() to return False for symlinks so the code moves to the symlink block
        orig_is_file = Path.is_file

        def mock_is_file(self: Path) -> bool:
            if self == link:
                return False
            return orig_is_file(self)

        # 2. Mock resolve to raise the target OSError
        def mock_resolve(self: Path, strict: bool = False) -> Any:  # noqa: ARG001
            raise OSError("Locked location")  # noqa: TRY003

        monkeypatch.setattr(Path, "is_file", mock_is_file)
        monkeypatch.setattr(Path, "resolve", mock_resolve)

        # Now it will skip the first if block, enter the symlink block, and trigger the exception!
        assert fs_util.is_valid_file_or_link(link) is False

    def test_path_has_files_empty_directory(
        self, fs_util: FileSystemUtil, tmp_path: Path
    ) -> None:
        """Verify it returns False if the directory has nothing inside."""
        assert fs_util.path_has_files(tmp_path) is False

    def test_path_has_files_nested_success(
        self, fs_util: FileSystemUtil, tmp_path: Path
    ) -> None:
        """Verify it detects files deep in nested structures."""
        nested_dir = tmp_path / "sub" / "deep"
        nested_dir.mkdir(parents=True)
        (nested_dir / "payload.cfg").write_text("config data")
        assert fs_util.path_has_files(tmp_path) is True

    def test_path_has_files_recursion_error(
        self, fs_util: FileSystemUtil, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Verify that RecursionError defaults to returning True safely."""

        def mock_rglob(self: Path, pattern: str) -> Any:  # noqa: ARG001
            raise RecursionError("Call stack overflow simulation")  # noqa: TRY003

        monkeypatch.setattr(Path, "rglob", mock_rglob)
        assert fs_util.path_has_files(tmp_path) is True

    def test_path_has_files_skips_duplicate_inodes(
        self, fs_util: FileSystemUtil, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Force path_has_files to evaluate the exact same inode twice and continue."""
        dir1 = tmp_path / "dir1"
        dir1.mkdir()
        dir2 = tmp_path / "dir2"
        dir2.mkdir()

        real_stat = dir1.stat(follow_symlinks=False)

        fake_stat_result: os.stat_result = type(real_stat)(
            (
                real_stat.st_mode,
                99999,  # Mock duplicate Inode Number
                88888,  # Mock duplicate Device Identifier
                real_stat.st_nlink,
                real_stat.st_uid,
                real_stat.st_gid,
                real_stat.st_size,
                int(real_stat.st_atime),
                int(real_stat.st_mtime),
                int(real_stat.st_ctime),
            )
        )

        def mock_stat(self: Path, follow_symlinks: bool = False) -> Any:  # noqa: ARG001
            return fake_stat_result

        monkeypatch.setattr(Path, "stat", mock_stat)
        assert fs_util.path_has_files(tmp_path) is False
