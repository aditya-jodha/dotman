# ruff: noqa: S101
from pathlib import Path

import yaml

from dotman.core.get_internal_data import InternalData, InternalDataArguments


class TestInternalData:
    def test_load_creates_file_when_missing(self, tmp_path: Path):
        file_path = tmp_path / "metadata.yml"
        assert not file_path.exists()
        data = InternalData.load(file_path)
        # file should now exist, current_profile None
        assert file_path.exists()
        assert data.current_profile is None
        assert data.file_path == file_path

    def test_load_returns_none_when_empty_file(self, tmp_path: Path):
        file_path = tmp_path / "metadata.yml"
        file_path.write_text("")  # empty file
        data = InternalData.load(file_path)
        assert data.current_profile is None

    def test_load_reads_existing_profile(self, tmp_path: Path):
        file_path = tmp_path / "metadata.yml"
        yaml.safe_dump(
            {InternalDataArguments.CURRENT_PROFILE.value: "work"}, file_path.open("w")
        )
        data = InternalData.load(file_path)
        assert data.current_profile == "work"

    def test_save_writes_yaml(self, tmp_path: Path):
        file_path = tmp_path / "metadata.yml"
        data = InternalData(current_profile="personal", file_path=file_path)
        data.save()
        # file should contain YAML with current_profile
        loaded = yaml.safe_load(file_path.read_text())
        assert loaded[InternalDataArguments.CURRENT_PROFILE.value] == "personal"

    def test_write_updates_and_saves(self, tmp_path: Path):
        file_path = tmp_path / "metadata.yml"
        data = InternalData(current_profile=None, file_path=file_path)
        data.write("newprofile")
        assert data.current_profile == "newprofile"
        loaded = yaml.safe_load(file_path.read_text())
        assert loaded[InternalDataArguments.CURRENT_PROFILE.value] == "newprofile"
