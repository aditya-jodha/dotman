# ruff: noqa: S101
from importlib.metadata import EntryPoint
from pathlib import Path
from types import SimpleNamespace
from typing import cast
from unittest.mock import MagicMock

import pytest
from dulwich import porcelain
from pytest import MonkeyPatch

from dotman.errors.plugin_errors import PluginNotFoundError
from dotman.plugin.api import PluginAPI
from dotman.plugin.installer import PluginInstaller
from dotman.plugin.manager import PluginManager
from dotman.plugin.manifest import InstalledPlugin, PluginManifest
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


def plugin_entry_point(name: str = "test-plugin", value: str = "test_plugin:Plugin") -> EntryPoint:
    return cast(
        "EntryPoint",
        SimpleNamespace(
            name=name,
            value=value,
            dist=SimpleNamespace(
                metadata={
                    "Name": "test-plugin-package",
                    "Version": "1.0.0",
                    "Summary": "A test plugin",
                    "Author": "Aditya",
                }
            ),
        ),
    )


def write_project(path: Path, name: str = "test-plugin-package") -> None:
    (path / "pyproject.toml").write_text(
        f'''
[project]
name = "{name}"
version = "1.0.0"
description = "A test plugin"

[project.entry-points."dotman.plugins"]
test-plugin = "test_plugin:Plugin"
'''
    )


def test_list_plugins_discovers_package_entry_points(
    monkeypatch: MonkeyPatch, tmp_path: Path
) -> None:
    manager = PluginManager(tmp_path / "plugins", FakeInstaller())
    repository_dir = manager.plugins_dir / "example-repository"
    repository_dir.mkdir()
    porcelain.init(str(repository_dir))
    monkeypatch.setattr(
        manager,
        "_plugin_entry_points",
        lambda _environment: [plugin_entry_point()],
    )

    plugins = manager.list_plugins()

    assert [plugin.manifest.name for plugin in plugins] == ["test-plugin"]
    assert plugins[0].repository.path == repository_dir
    assert plugins[0].manifest.distribution_name == "test-plugin-package"


def test_install_local_plugin_uses_package_metadata(
    monkeypatch: MonkeyPatch, tmp_path: Path
) -> None:
    source_repo = tmp_path / "source-plugin"
    source_repo.mkdir()
    porcelain.init(str(source_repo))
    write_project(source_repo)
    porcelain.add(str(source_repo), paths=["pyproject.toml"])
    porcelain.commit(str(source_repo), message=b"Initial plugin")

    plugin_dir = tmp_path / "plugins"
    installer = FakeInstaller()
    manager = PluginManager(plugin_dir, installer)
    expected = InstalledPlugin(
        cast("PluginRepository", SimpleNamespace(path=plugin_dir / "source-plugin")),
        PluginManifest.from_entry_point(plugin_entry_point()),
    )
    monkeypatch.setattr(manager, "_get_installed_plugin_by_repository", lambda _repo: expected)

    manifest = manager.install(str(source_repo))

    assert manifest.name == "test-plugin"
    assert (plugin_dir / "source-plugin" / "pyproject.toml").exists()
    assert installer.installed == [(plugin_dir / "source-plugin").resolve()]


def test_uninstall_removes_package_and_managed_repository(
    monkeypatch: MonkeyPatch, tmp_path: Path
) -> None:
    plugins_dir = tmp_path / "plugins"
    repository_dir = plugins_dir / "example-repository"
    repository_dir.mkdir(parents=True)
    porcelain.init(str(repository_dir))
    write_project(repository_dir)

    installer = FakeInstaller()
    manager = PluginManager(plugins_dir, installer)
    monkeypatch.setattr(
        manager,
        "_plugin_entry_points",
        lambda _environment: [plugin_entry_point()],
    )

    manager.uninstall("test-plugin")

    assert installer.uninstalled == ["test-plugin-package"]
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
    write_project(source_repo)
    porcelain.add(str(source_repo), paths=["pyproject.toml"])
    porcelain.commit(str(source_repo), message=b"Initial plugin")

    plugins_dir = tmp_path / "plugins"
    manager = PluginManager(plugins_dir, FailingInstaller())

    with pytest.raises(RuntimeError, match="package installation failed"):
        manager.install(str(source_repo))

    assert not (plugins_dir / "source-plugin").exists()


def test_broken_plugin_does_not_prevent_other_plugins_from_loading(
    monkeypatch: MonkeyPatch, tmp_path: Path
) -> None:
    class BrokenPlugin:
        api_version = "1"

        def register(self, api: PluginAPI) -> None:
            api.add_typer(MagicMock(), name="broken")
            api.add_validator(lambda _context: None)
            raise RuntimeError("broken")

    class GoodPlugin:
        api_version = "1"

        def register(self, api: PluginAPI) -> None:
            api.add_typer(MagicMock(), name="good")
            api.add_validator(lambda _context: None)

    manager = PluginManager(tmp_path / "plugins", FakeInstaller())
    broken_repository = cast(
        "PluginRepository", SimpleNamespace(path=tmp_path / "broken-repository")
    )
    good_repository = cast("PluginRepository", SimpleNamespace(path=tmp_path / "good-repository"))
    monkeypatch.setattr(
        manager,
        "list_plugins",
        lambda: [
            InstalledPlugin(
                broken_repository,
                PluginManifest.from_entry_point(plugin_entry_point("broken")),
            ),
            InstalledPlugin(
                good_repository,
                PluginManifest.from_entry_point(plugin_entry_point("good")),
            ),
        ],
    )
    calls = iter(
        [
            (
                BrokenPlugin(),
                PluginManifest.from_entry_point(plugin_entry_point("broken")).with_api_version("1"),
            ),
            (
                GoodPlugin(),
                PluginManifest.from_entry_point(plugin_entry_point("good")).with_api_version("1"),
            ),
        ]
    )
    monkeypatch.setattr(
        "dotman.plugin.manager.PluginLoader.load_plugin", lambda _self, _manifest: next(calls)
    )

    root_app = MagicMock()
    registry = manager.load_plugins(root_app)

    assert len(registry._add_validators) == 1  # pyright: ignore[reportPrivateUsage]
    root_app.add_typer.assert_called_once()
    assert root_app.add_typer.call_args.kwargs == {"name": "good"}
