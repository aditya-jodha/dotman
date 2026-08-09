# ruff: noqa: S101
from pathlib import Path

import pytest
import yaml

from dotman.core.get_internal_data import DotmanMetadata, resolve_profile
from dotman.errors.config_errors import ConfigParseError, InvalidConfigFileError
from dotman.errors.profile_errors import ProfileMetaDataFileCorruptedError


def make_config(dotfiles_dir: Path):
    """Simple object that mimics the config returned by load_config()."""

    class C:
        pass

    c = C()
    c.dotfiles_dir = dotfiles_dir  # pyright: ignore[reportAttributeAccessIssue] # ty:ignore[unresolved-attribute]
    # home_dir is not used here
    return c


class TestResolveProfile:
    def test_explicit_profile_wins(self):
        md = DotmanMetadata(file_path=Path("dummy"), current_profile="meta")
        assert resolve_profile("explicit", md) == "explicit"

    def test_fallback_to_metadata(self):
        md = DotmanMetadata(file_path=Path("dummy"), current_profile="meta")
        assert resolve_profile(None, md) == "meta"

    def test_both_none_raises(self):
        md = DotmanMetadata(file_path=Path("dummy"), current_profile=None)
        with pytest.raises(ProfileMetaDataFileCorruptedError):
            resolve_profile(None, md)


class TestDotmanMetadata:
    def test_load_creates_file_if_missing(self, tmp_path: Path):
        file_path = tmp_path / "meta.yaml"
        md = DotmanMetadata.load(file_path)
        assert md.file_path == file_path
        assert md.current_profile is None
        assert file_path.exists()

    def test_load_valid_yaml(self, tmp_path: Path):
        file_path = tmp_path / "meta.yaml"
        file_path.write_text(yaml.safe_dump({"current_profile": "abc"}))
        md = DotmanMetadata.load(file_path)
        assert md.current_profile == "abc"

    def test_load_yaml_error(self, tmp_path: Path):
        file_path = tmp_path / "meta.yaml"
        file_path.write_text(":\n:bad_yaml")
        with pytest.raises(ConfigParseError):
            DotmanMetadata.load(file_path)

    def test_load_validation_error(self, tmp_path: Path):
        file_path = tmp_path / "meta.yaml"
        file_path.write_text(yaml.safe_dump({"unknown_field": "oops"}))
        with pytest.raises(InvalidConfigFileError):
            DotmanMetadata.load(file_path)

    def test_save_and_with_current_profile(self, tmp_path: Path):
        file_path = tmp_path / "meta.yaml"
        md = DotmanMetadata(file_path=file_path, current_profile="one")
        md.save()
        data = yaml.safe_load(file_path.read_text())
        assert data["current_profile"] == "one"

        new_md = md.with_current_profile("two")
        new_md.save()
        assert new_md.current_profile == "two"
        data2 = yaml.safe_load(file_path.read_text())
        assert data2["current_profile"] == "two"

    def test_current_profile_or_raise(self, tmp_path: Path):
        md = DotmanMetadata(file_path=tmp_path / "meta.yaml", current_profile="x")
        assert md.current_profile_or_raise() == "x"
        md_none = DotmanMetadata(file_path=tmp_path / "meta.yaml", current_profile=None)
        with pytest.raises(ProfileMetaDataFileCorruptedError):
            md_none.current_profile_or_raise()
