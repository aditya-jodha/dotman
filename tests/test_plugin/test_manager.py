# ruff: noqa: S101
from pathlib import Path

import pytest
from dulwich import porcelain

from dotman.errors.plugin_errors import PluginNotFoundError
from dotman.plugin.installer import PluginInstaller
from dotman.plugin.manager import PluginManager
from dotman.plugin.repository import PluginRepository


class FakeInstaller(PluginInstaller):
    def __init__(self) -> None:
        self.installed: list[Path] = []
        self.uninstalled: list[str] = []

    def install(self, repository: PluginRepository) -> None:
        self.installed.append(repository.path)

    def uninstall(self, distribution_name: str) -> None:
        self.uninstalled.append(distribution_name)


class FailingInstaller(FakeInstaller):
    def install(self, repository: PluginRepository) -> None:
        super().install(repository)
        raise RuntimeError("package installation failed")  # noqa: TRY003


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

    installer = FakeInstaller()
    manager = PluginManager(plugin_dir, installer)

    # Install from local repository
    manifest = manager.install(str(source_repo))

    assert manifest.name == "test-plugin"
    assert manifest.version == "1.0.0"

    # Repository should now exist in plugin directory
    installed_repo = plugin_dir / "source-plugin"

    assert installed_repo.exists()
    assert (installed_repo / "plugin.toml").exists()
    assert installer.installed == [installed_repo.resolve()]


def test_uninstall_removes_package_and_repository(tmp_path: Path) -> None:
    plugins_dir = tmp_path / "plugins"
    repository_dir = plugins_dir / "example-repository"
    repository_dir.mkdir(parents=True)
    porcelain.init(str(repository_dir))
    (repository_dir / "plugin.toml").write_text(
        """
[plugin]
name = "example-plugin"
distribution_name = "example-plugin-package"
version = "1.0.0"
description = "An example plugin"
authors = ["Aditya"]
entry_point = "example_plugin:ExamplePlugin"
"""
    )

    installer = FakeInstaller()
    manager = PluginManager(plugins_dir, installer)

    manager.uninstall("example-plugin")

    assert installer.uninstalled == ["example-plugin-package"]
    assert not repository_dir.exists()


def test_uninstall_rejects_unknown_plugin(tmp_path: Path) -> None:
    manager = PluginManager(tmp_path / "plugins", FakeInstaller())

    with pytest.raises(PluginNotFoundError):
        manager.uninstall("missing-plugin")


def test_install_removes_cloned_repository_when_package_installation_fails(
    tmp_path: Path,
) -> None:
    source_repo = tmp_path / "source-plugin"
    source_repo.mkdir()
    porcelain.init(str(source_repo))
    (source_repo / "plugin.toml").write_text(
        """
[plugin]
name = "test-plugin"
version = "1.0.0"
description = "A test plugin"
authors = ["Aditya"]
entry_point = "test_plugin:TestPlugin"
"""
    )
    porcelain.add(str(source_repo), paths=["plugin.toml"])
    porcelain.commit(str(source_repo), message=b"Initial plugin")

    plugins_dir = tmp_path / "plugins"
    manager = PluginManager(plugins_dir, FailingInstaller())

    with pytest.raises(RuntimeError, match="package installation failed"):
        manager.install(str(source_repo))

    assert not (plugins_dir / "source-plugin").exists()
