# ruff: noqa: S101
# pyright: reportPrivateUsage=false
from pathlib import Path

import pytest
import yaml

from dotman.core.config import config
from dotman.errors.config_errors import InvalidConfigFileError


def cfg(tmp_path: Path) -> config.DotmanConfig:
    dot = tmp_path / "dot"
    home = tmp_path / "home"
    plugins = tmp_path / "plugins"
    dot.mkdir()
    home.mkdir()
    return config.DotmanConfig(dotfiles_dir=dot, home_dir=home, plugins_dir=plugins)


def test_dotmanconfig_as_dict(cfg: config.DotmanConfig):
    d = cfg.model_dump(mode="json")
    assert d["dotfiles_dir"].endswith("dot")
    assert d["home_dir"].endswith("home")


def test_internal_filesystemobject_values():
    vals = config.InternalFileSystemObject.values()
    assert "packages" in vals
    assert "metadata.yml" in vals
    assert "profiles" in vals


def test_get_temp_log_file_creates_path(cfg: config.DotmanConfig):
    path = config.get_temp_log_file(cfg)

    assert path.parent.parent.name == "logbook"
    assert path.suffix == ".log"
    assert path.name.startswith("dotman_")


def test_get_config_path_default_and_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    # default path
    default = config.DotmanConfig.path()
    assert isinstance(default, Path)
    # env override
    env_path = tmp_path / "custom.yml"
    monkeypatch.setenv(config.CONFIG_ENV_VAR, str(env_path))
    assert config.DotmanConfig.path() == env_path


def test_load_config_returns_defaults_when_missing(tmp_path: Path):
    path = tmp_path / "missing.yml"
    cfg = config.DotmanConfig.load(path)
    assert cfg.dotfiles_dir == config.DEFAULT_DOTFILES_DIR
    assert cfg.home_dir == config.DEFAULT_HOME_DIR


def test_load_config_raises_when_keys_missing(tmp_path: Path):
    path = tmp_path / "bad.yml"
    yaml.safe_dump({"dotfiles_dir": "/some/path"}, path.open("w"))
    with pytest.raises(InvalidConfigFileError):
        config.DotmanConfig.load(path)


def test_load_config_reads_valid_file(tmp_path: Path):
    path = tmp_path / "good.yml"
    yaml.safe_dump(
        {"dotfiles_dir": str(tmp_path / "dot"), "home_dir": str(tmp_path / "home")},
        path.open("w"),
    )
    (tmp_path / "dot").mkdir()
    (tmp_path / "home").mkdir()
    cfg = config.DotmanConfig.load(path)
    assert cfg.dotfiles_dir == (tmp_path / "dot")
    assert cfg.home_dir == (tmp_path / "home")


def test_save_config_writes_yaml(tmp_path: Path, cfg: config.DotmanConfig):
    path = tmp_path / "out.yml"
    cfg.save(path)
    data = yaml.safe_load(path.read_text())
    assert data["dotfiles_dir"].endswith("dot")
    assert data["home_dir"].endswith("home")
