# ruff: noqa: S101, TRY003
# pyright: reportUnknownParameterType=false
from pathlib import Path

from pytest import MonkeyPatch
from rich.console import Console

import dotman.cli.tree_builder as pretty


def render_tree_to_text(tree: pretty.Tree) -> str:
    """Helper: render a Rich Tree to plain text for assertions."""
    console = Console(record=True, width=120)
    console.print(tree)
    return console.export_text()


def test_print_beautiful_directory_returns_tree_and_root_label(tmp_path: Path):
    root = tmp_path / "project"
    root.mkdir()
    # create a file so the tree isn't empty
    (root / "README.md").write_text("hello")

    tree = pretty.print_beautiful_directory(root)
    assert hasattr(tree, "label")
    # label contains the directory name
    assert root.name in str(tree.label)


def test_add_to_tree_shows_files_and_folders_with_icons(tmp_path: Path):
    root = tmp_path / "repo"
    root.mkdir()
    # create folder and files with different suffixes
    src = root / "src"
    src.mkdir()
    (src / "main.py").write_text("print('x')")
    (root / "config.json").write_text("{}")
    (root / "notes.md").write_text("note")
    (root / "other.bin").write_text("data")

    tree = pretty.print_beautiful_directory(root)
    out = render_tree_to_text(tree)

    # folder icon and name
    assert "📂" in out and "src" in out
    # python file icon
    assert "🐍" in out and "main.py" in out
    # json/config icon
    assert "⚙️" in out and "config.json" in out
    # markdown icon
    assert "📝" in out and "notes.md" in out
    # generic file icon
    assert "📄" in out and "other.bin" in out


def test_sorting_folders_before_files(tmp_path: Path):
    root = tmp_path / "proj"
    root.mkdir()
    # create a file and a folder with names that would sort differently if not grouped
    (root / "a_file.txt").write_text("a")
    folder = root / "A_folder"
    folder.mkdir()
    (folder / "z.py").write_text("x")

    tree = pretty.print_beautiful_directory(root)
    out = render_tree_to_text(tree)

    # Ensure folder line appears before the file line in the rendered output
    folder_index = out.find("A_folder")
    file_index = out.find("a_file.txt")
    assert folder_index != -1 and file_index != -1
    assert folder_index < file_index


def test_permission_error_is_silently_skipped(monkeypatch: MonkeyPatch, tmp_path: Path):
    root = tmp_path / "rootperm"
    root.mkdir()
    # create a subdir that will raise PermissionError when iterated
    bad = root / "secret"
    bad.mkdir()
    (bad / "hidden.txt").write_text("secret")
    (root / "visible.txt").write_text("ok")

    # Patch Path.iterdir so that iterating over the 'secret' directory raises PermissionError
    original_iterdir = Path.iterdir

    def fake_iterdir(self):  # pyright: ignore[reportMissingParameterType]
        if self == bad:
            raise PermissionError("no access")
        return original_iterdir(self)

    monkeypatch.setattr(Path, "iterdir", fake_iterdir)

    tree = pretty.print_beautiful_directory(root)
    out = render_tree_to_text(tree)

    # 'secret' directory should not appear, but visible.txt should
    assert "secret" in out
    assert "hidden.txt" not in out
    assert "visible.txt" in out


def test_empty_directory_renders_without_error(tmp_path: Path):
    root = tmp_path / "empty"
    root.mkdir()
    tree = pretty.print_beautiful_directory(root)
    out = render_tree_to_text(tree)
    # root name should be present and no exceptions raised
    assert "empty" in out
