# ruff: noqa: S101  # noqa: N999

import json
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


# ---------- Tests for add_entry + save ----------
def test_add_and_save_entries(tmp_path: Path):
    """Ensure entries are added and persisted correctly in JSON log."""
    log_file = tmp_path / "journal.json"
    journal = RollbackJournal(log_file)

    journal.add_entry(tmp_path / "a.txt", tmp_path / "b.txt")
    journal.add_entry(tmp_path / "c.txt", tmp_path / "d.txt")
    journal.save()

    # Verify JSON structure
    data = json.loads(log_file.read_text(encoding="utf-8"))
    assert "files" in data
    assert len(data["files"]) == 2
    assert data["files"][0]["original_path"].endswith("a.txt")
    assert data["files"][1]["new_path"].endswith("d.txt")


# ---------- Tests for clear ----------
def test_clear_removes_log_file(tmp_path: Path):
    """Verify that clear() deletes the log file if it exists."""
    log_file = tmp_path / "journal.json"
    journal = RollbackJournal(log_file)

    journal.add_entry(tmp_path / "a.txt", tmp_path / "b.txt")
    journal.save()
    assert log_file.exists()

    journal.clear()
    assert not log_file.exists()


# ---------- Tests for rollback ----------
def test_rollback_restores_files(tmp_path: Path):
    """Rollback should rename files back to their original paths."""
    original = tmp_path / "orig.txt"
    new = create_dummy_file(tmp_path / "new.txt", "hello")

    log_file = tmp_path / "journal.json"
    journal = RollbackJournal(log_file)
    journal.add_entry(original, new)
    journal.save()

    journal.rollback()

    # Verify rollback results
    assert original.exists()
    assert original.read_text() == "hello"
    assert not new.exists()
    assert not log_file.exists()  # journal cleared


def test_rollback_skips_missing_files(tmp_path: Path):
    """Rollback should skip gracefully if new_path does not exist."""
    original = tmp_path / "orig.txt"
    new = tmp_path / "new.txt"  # not created

    log_file = tmp_path / "journal.json"
    journal = RollbackJournal(log_file)
    journal.add_entry(original, new)
    journal.save()

    journal.rollback()

    # Nothing should be created
    assert not original.exists()
    assert not new.exists()
    assert not log_file.exists()
