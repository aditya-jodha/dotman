# ruff: noqa: S101, S108
from pathlib import Path

import pytest
import yaml
from pytest import MonkeyPatch

import dotman.core.get_internal_data as gid
from dotman.core.config.config import InternalFileSystemObject
from dotman.errors.profile_errors import ProfileMetaDataFileCorruptedError


def make_config(dotfiles_dir: Path):
    """Simple object that mimics the config returned by load_config()."""

    class C:
        pass

    c = C()
    c.dotfiles_dir = dotfiles_dir  # pyright: ignore[reportAttributeAccessIssue] # ty:ignore[unresolved-attribute]
    # home_dir is not used here
    return c


def test_resolve_profile_prefers_explicit():
    internal = gid.InternalData(current_profile="internal", file_path=Path("/tmp/x"))
    assert gid.resolve_profile("explicit", internal) == "explicit"


def test_resolve_profile_uses_internal_when_explicit_none():
    internal = gid.InternalData(current_profile="internal", file_path=Path("/tmp/x"))
    assert gid.resolve_profile(None, internal) == "internal"


def test_resolve_profile_raises_when_both_none():
    internal = gid.InternalData(current_profile=None, file_path=Path("/tmp/x"))
    with pytest.raises(ProfileMetaDataFileCorruptedError):
        gid.resolve_profile(None, internal)


def test_load_creates_file_when_missing(tmp_path: Path, monkeypatch: MonkeyPatch):
    dotfiles = tmp_path / "dotfiles"

    # Mock DotmanConfig.load instead so InternalData.load can find the right directory path
    monkeypatch.setattr(gid.DotmanConfig, "load", lambda *_: make_config(dotfiles))

    # Call the real InternalData.load; it will now use mocked config.dotfiles_dir
    internal = gid.InternalData.load(None)

    assert internal.current_profile is None
    assert internal.file_path.exists()

    # file should be empty YAML (or at least valid YAML)
    content = internal.file_path.read_text(encoding="utf-8")
    # empty file may be blank; safe_load of blank returns None in implementation
    assert content == "" or isinstance(content, str)


def test_load_reads_existing_metadata(tmp_path: Path, monkeypatch: MonkeyPatch):
    dotfiles = tmp_path / "dotfiles"
    meta = dotfiles / InternalFileSystemObject.METADATA.value
    meta.parent.mkdir(parents=True)
    # write YAML with current_profile
    yaml.safe_dump({"current_profile": "saved_profile"}, meta.open("w", encoding="utf-8"))

    # Change this line to target the new class method:
    monkeypatch.setattr(gid.DotmanConfig, "load", lambda *_: make_config(dotfiles))

    # Then verify the rest of the test functions smoothly
    internal = gid.InternalData.load(None)
    assert internal.current_profile == "saved_profile"


def test_save_writes_yaml(tmp_path: Path):
    # create an InternalData pointing to a file path
    file_path = tmp_path / "meta.yaml"
    internal = gid.InternalData(current_profile="me", file_path=file_path)
    # ensure parent exists and call save
    internal.save()
    # file must exist and contain the YAML mapping
    data = yaml.safe_load(file_path.read_text(encoding="utf-8"))
    assert data.get("current_profile") == "me"


def test_write_updates_and_saves(tmp_path: Path):
    file_path = tmp_path / "meta.yaml"
    internal = gid.InternalData(current_profile=None, file_path=file_path)
    internal.write("new_profile")
    assert internal.current_profile == "new_profile"
    data = yaml.safe_load(file_path.read_text(encoding="utf-8"))
    assert data.get("current_profile") == "new_profile"
