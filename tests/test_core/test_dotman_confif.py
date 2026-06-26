# ruff: noqa: S101
from pathlib import Path

import pytest
import yaml

from dotman.core import config


def test_user_defined_values():
    vals = config.UserDefinedConfig.values()
    assert "dotfiles_dir" in vals
    assert "home_dir" in vals


def test_dotmanconfig_as_dict(tmp_path: Path):
    cfg = config.DotmanConfig(dotfiles_dir=tmp_path / "dot", home_dir=tmp_path / "home")
    d = cfg.as_dict()
    assert d["dotfiles_dir"].endswith("dot")
    assert d["home_dir"].endswith("home")


def test_internal_filesystemobject_values():
    vals = config.InternalFileSystemObject.values()
    assert "packages" in vals
    assert "metadata.yml" in vals
    assert "profiles" in vals


def test_get_temp_log_file_creates_path(tmp_path: Path):
    cfg = config.DotmanConfig(dotfiles_dir=tmp_path, home_dir=tmp_path)
    path = config.get_temp_log_file(cfg)

    assert path.parent.parent.name == "logbook"
    assert path.suffix == ".log"
    assert path.name.startswith("dotman_")


def test_get_config_path_default_and_env(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    # default path
    default = config.get_config_path()
    assert isinstance(default, Path)
    # env override
    env_path = tmp_path / "custom.yml"
    monkeypatch.setenv(config.CONFIG_ENV_VAR, str(env_path))
    assert config.get_config_path() == env_path


def test_load_config_returns_defaults_when_missing(tmp_path: Path):
    path = tmp_path / "missing.yml"
    cfg = config.load_config(path)
    assert cfg.dotfiles_dir == config.DEFAULT_DOTFILES_DIR
    assert cfg.home_dir == config.DEFAULT_HOME_DIR


def test_load_config_raises_when_keys_missing(tmp_path: Path):
    path = tmp_path / "bad.yml"
    yaml.safe_dump({"dotfiles_dir": "/some/path"}, path.open("w"))
    with pytest.raises(ValueError):
        config.load_config(path)


def test_load_config_reads_valid_file(tmp_path: Path):
    path = tmp_path / "good.yml"
    yaml.safe_dump(
        {"dotfiles_dir": str(tmp_path / "dot"), "home_dir": str(tmp_path / "home")},
        path.open("w"),
    )
    cfg = config.load_config(path)
    assert cfg.dotfiles_dir == (tmp_path / "dot")
    assert cfg.home_dir == (tmp_path / "home")


def test_save_config_writes_yaml(tmp_path: Path):
    path = tmp_path / "out.yml"
    cfg = config.DotmanConfig(dotfiles_dir=tmp_path / "dot", home_dir=tmp_path / "home")
    config.save_config(cfg, path)
    data = yaml.safe_load(path.read_text())
    assert data["dotfiles_dir"].endswith("dot")
    assert data["home_dir"].endswith("home")
