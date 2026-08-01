# ruff: noqa: S101
from pathlib import Path

from dulwich import porcelain

from dotman.plugin.manager import PluginManager


def test_install_local_plugin(tmp_path: Path) -> None:
    # Create a fake plugin repository
    source_repo = tmp_path / "source-plugin"
    source_repo.mkdir()

    porcelain.init(str(source_repo))

    # Add a minimal plugin manifest
    manifest = source_repo / "plugin.toml"
    manifest.write_text(
        """
[plugin]
name = "test-plugin"
version = "1.0.0"
description = "A test plugin"
authors = ["Aditya"]
entry_point = "test_plugin:TestPlugin"

[dotman]
api_version = "1"
"""
    )

    # Commit the manifest
    porcelain.add(str(source_repo), paths=["plugin.toml"])
    porcelain.commit(
        str(source_repo),
        message=b"Initial plugin",
    )

    # Directory where Dotman installs plugins
    plugin_dir = tmp_path / "plugins"

    manager = PluginManager(plugin_dir)

    # Install from local repository
    manifest = manager.install(str(source_repo))

    assert manifest.name == "test-plugin"
    assert manifest.version == "1.0.0"

    # Repository should now exist in plugin directory
    installed_repo = plugin_dir / "source-plugin"

    assert installed_repo.exists()
    assert (installed_repo / "plugin.toml").exists()
