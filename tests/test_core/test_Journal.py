# ruff: noqa: S101  # noqa: N999

import sqlite3
from pathlib import Path

from dotman.core.add import RollbackJournal

# ============================================================
# RollbackJournal: Unit Tests
# ============================================================


# ---------- Setup Helpers ----------
def create_dummy_file(path: Path, content: str = "data") -> Path:
    """Utility to create a file with given content."""
    path.write_text(content, encoding="utf-8")
    return path


# ---------- Tests for add_entry ----------
def test_add_entries(tmp_path: Path) -> None:
    """Ensure entries are added and persisted in the SQLite journal."""
    log_file = tmp_path / "journal.db"
    journal = RollbackJournal(log_file)

    journal.add_entry(tmp_path / "a.txt", tmp_path / "b.txt")
    journal.add_entry(tmp_path / "c.txt", tmp_path / "d.txt")

    with sqlite3.connect(log_file) as conn:
        rows = conn.execute(
            """ SELECT original_path, new_path FROM journal ORDER BY id """
        ).fetchall()

    assert len(rows) == 2
    assert rows[0][0].endswith("a.txt")
    assert rows[0][1].endswith("b.txt")
    assert rows[1][0].endswith("c.txt")
    assert rows[1][1].endswith("d.txt")


# ---------- Tests for clear ----------
def test_clear_removes_log_entries(tmp_path: Path) -> None:
    """Verify that clear() removes all journal entries."""
    log_file = tmp_path / "journal.db"
    journal = RollbackJournal(log_file)

    journal.add_entry(tmp_path / "a.txt", tmp_path / "b.txt")

    journal.clear()

    with sqlite3.connect(log_file) as conn:
        count = conn.execute("SELECT COUNT(*) FROM journal").fetchone()[0]

    assert count == 0


# ---------- Tests for rollback ----------
def test_rollback_restores_files(tmp_path: Path) -> None:
    """Rollback should rename files back to their original paths."""
    original = tmp_path / "orig.txt"
    new = create_dummy_file(tmp_path / "new.txt", "hello")

    log_file = tmp_path / "journal.db"
    journal = RollbackJournal(log_file)
    journal.add_entry(original, new)

    journal.rollback()

    assert original.exists()
    assert original.read_text() == "hello"
    assert not new.exists()

    with sqlite3.connect(log_file) as conn:
        count = conn.execute("SELECT COUNT(*) FROM journal").fetchone()[0]

    assert count == 0


def test_rollback_skips_missing_files(tmp_path: Path) -> None:
    """Rollback should skip gracefully if new_path does not exist."""
    original = tmp_path / "orig.txt"
    new = tmp_path / "new.txt"

    log_file = tmp_path / "journal.db"
    journal = RollbackJournal(log_file)
    journal.add_entry(original, new)

    journal.rollback()

    assert not original.exists()
    assert not new.exists()

    with sqlite3.connect(log_file) as conn:
        count = conn.execute("SELECT COUNT(*) FROM journal").fetchone()[0]

    assert count == 0


def test_rollback_restores_files_in_reverse_order(tmp_path: Path) -> None:
    """Rollback should restore file operations in reverse order."""
    first_original = tmp_path / "first.txt"
    second_original = tmp_path / "second.txt"

    first_new = create_dummy_file(
        tmp_path / "first-new.txt",
        "first",
    )
    second_new = create_dummy_file(
        tmp_path / "second-new.txt",
        "second",
    )

    log_file = tmp_path / "journal.db"
    journal = RollbackJournal(log_file)

    # Operations are recorded in this order.
    journal.add_entry(first_original, first_new)
    journal.add_entry(second_original, second_new)

    journal.rollback()

    assert first_original.exists()
    assert first_original.read_text() == "first"
    assert not first_new.exists()

    assert second_original.exists()
    assert second_original.read_text() == "second"
    assert not second_new.exists()
