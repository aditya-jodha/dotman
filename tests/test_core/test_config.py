# ruff: noqa: S101, S108
from pathlib import Path

import pytest
import yaml

from dotman.core.config.config import (
    DotmanConfig,
    InternalFileSystemObject,
    LogBookData,
    get_temp_log_file,
)
from dotman.errors.config_errors import (
    DotmanConfigParseError,
    InvalidConfigFileError,
    InvalidConfigKeyError,
    InvalidConfigValueError,
)


class TestDotmanConfig:
    def test_save_and_load_roundtrip(self, tmp_path: Path):
        dot = tmp_path / "dot"
        home = tmp_path / "home"
        dot.mkdir()
        home.mkdir()

        cfg = DotmanConfig(dotfiles_dir=dot, home_dir=home)
        path = tmp_path / "config.yml"
        cfg.save(path)
        loaded = DotmanConfig.load(path)
        assert loaded.dotfiles_dir == cfg.dotfiles_dir
        assert loaded.home_dir == cfg.home_dir

    def test_path_env_var(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("DOTMAN_CONFIG", "/tmp/custom.yml")
        assert DotmanConfig.path() == Path("/tmp/custom.yml")

    def test_expand_path(self):
        p = DotmanConfig.expand_path("~/testdir")
        assert p.is_absolute()

    def test_default_returns_expected(self):
        cfg = DotmanConfig.default()
        assert isinstance(cfg, DotmanConfig)

    def test_set_valid_and_invalid_key(self, tmp_path: Path):
        dot = tmp_path / "dot"
        home = tmp_path / "home"
        dot.mkdir()
        home.mkdir()

        cfg = DotmanConfig(dotfiles_dir=dot, home_dir=home)

        # valid update
        new_cfg = cfg.set("dotfiles_dir", tmp_path / "newdot")
        assert new_cfg.dotfiles_dir == tmp_path / "newdot"

        # invalid key
        with pytest.raises(InvalidConfigKeyError):
            cfg.set("badkey", "value")

    def test_set_invalid_value(self, tmp_path: Path):
        dot = tmp_path / "dot"
        home = tmp_path / "home"
        dot.mkdir()
        home.mkdir()

        cfg = DotmanConfig(dotfiles_dir=dot, home_dir=home)
        # Pass a string path that exists but is not a directory
        bad_file = tmp_path / "notadir.txt"
        bad_file.write_text("oops")

        with pytest.raises(InvalidConfigValueError):
            cfg.set("home_dir", str(bad_file))

    def test_load_missing_returns_default(self, tmp_path: Path):
        path = tmp_path / "missing.yml"
        cfg = DotmanConfig.load(path)
        assert isinstance(cfg, DotmanConfig)

    def test_load_yaml_error(self, tmp_path: Path):
        path = tmp_path / "bad.yml"
        path.write_text(":\n:bad_yaml")
        with pytest.raises(DotmanConfigParseError):
            DotmanConfig.load(path)

    def test_load_validation_error(self, tmp_path: Path):
        path = tmp_path / "bad.yml"
        path.write_text(yaml.safe_dump({"unknown": "oops"}))
        with pytest.raises(InvalidConfigFileError):
            DotmanConfig.load(path)


class TestInternalFileSystemObject:
    def test_values_contains_all(self):
        vals = InternalFileSystemObject.values()
        assert "packages" in vals
        assert "metadata.yml" in vals
        assert "profiles" in vals
        assert "logbook" in vals
        assert "tmp" in vals


class TestLogBookDataAndTempFile:
    def test_logbookdata_and_tempfile(self, tmp_path: Path):
        dot = tmp_path / "dot"
        home = tmp_path / "home"
        dot.mkdir()
        home.mkdir()

        cfg = DotmanConfig(dotfiles_dir=dot, home_dir=home)
        log_path = get_temp_log_file(cfg)
        assert log_path.parent.name == "tmp"
        lb = LogBookData(original_path=Path("orig"), new_path=Path("new"))
        assert lb.original_path.name == "orig"
        assert lb.new_path.name == "new"
