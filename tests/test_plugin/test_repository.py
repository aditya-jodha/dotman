# ruff: noqa: S101, TRY003
# pyright: reportAttributeAccessIssue=false
from pathlib import Path

import pytest
from dulwich.errors import NotGitRepository
from dulwich.repo import Repo
from pytest import MonkeyPatch

from dotman.errors.plugin_errors import (
    PluginRepositoryError,
    PluginRepositoryNotFoundError,
)
from dotman.plugin.repository import PluginRepository


class DummyRepo:
    def head(self) -> bytes:
        return b"deadbeef"


class BadRepo:
    def head(self) -> bytes:
        raise Exception("bad head")  # noqa: TRY002


def test_init_success(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr("dotman.plugin.repository.Repo", lambda _p: DummyRepo())
    repo = PluginRepository(tmp_path)
    assert repo.current_commit() == "deadbeef"


def test_init_failure(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    def bad_repo(_p: Repo) -> BadRepo:
        raise NotGitRepository("not a repo")

    monkeypatch.setattr("dotman.plugin.repository.Repo", bad_repo)
    with pytest.raises(PluginRepositoryNotFoundError):
        PluginRepository(tmp_path)


def test_clone_success(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    called: dict[str, str] = {}

    def fake_clone(url: str, _target: str) -> None:
        called["url"] = url

    monkeypatch.setattr("dotman.plugin.repository.porcelain.clone", fake_clone)
    monkeypatch.setattr("dotman.plugin.repository.Repo", lambda _p: DummyRepo())
    repo = PluginRepository.clone("https://example.com/repo.git", tmp_path)
    assert isinstance(repo, PluginRepository)
    assert called["url"] == "https://example.com/repo.git"


def test_clone_failure(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    def bad_clone(_url: str, _target: str) -> None:
        raise OSError("clone failed")

    monkeypatch.setattr("dotman.plugin.repository.porcelain.clone", bad_clone)
    with pytest.raises(PluginRepositoryError):
        PluginRepository.clone("https://example.com/repo.git", tmp_path)


def test_fetch_success(monkeypatch: MonkeyPatch) -> None:
    repo = PluginRepository.__new__(PluginRepository)
    repo.repo = DummyRepo()

    called: dict[str, str] = {}

    def fake_fetch(_repo_obj: DummyRepo, remote: str) -> None:
        called["remote"] = remote

    monkeypatch.setattr("dotman.plugin.repository.porcelain.fetch", fake_fetch)
    repo.fetch("origin")
    assert called["remote"] == "origin"


def test_fetch_failure(monkeypatch: MonkeyPatch) -> None:
    repo = PluginRepository.__new__(PluginRepository)
    repo.repo = DummyRepo()

    def bad_fetch(_repo_obj: DummyRepo, _remote: str) -> None:
        raise OSError("fetch failed")

    monkeypatch.setattr("dotman.plugin.repository.porcelain.fetch", bad_fetch)
    with pytest.raises(PluginRepositoryError):
        repo.fetch("origin")


def test_checkout_success(monkeypatch: MonkeyPatch) -> None:
    repo = PluginRepository.__new__(PluginRepository)
    repo.repo = DummyRepo()

    called: dict[str, str] = {}

    def fake_update_head(_repo_obj: DummyRepo, branch: str) -> None:
        called["branch"] = branch

    monkeypatch.setattr("dotman.plugin.repository.porcelain.update_head", fake_update_head)
    repo.checkout("dev")
    assert called["branch"] == "dev"


def test_checkout_failure(monkeypatch: MonkeyPatch) -> None:
    repo = PluginRepository.__new__(PluginRepository)
    repo.repo = DummyRepo()

    def bad_update_head(_repo_obj: DummyRepo, _branch: str) -> None:
        raise OSError("checkout failed")

    monkeypatch.setattr("dotman.plugin.repository.porcelain.update_head", bad_update_head)
    with pytest.raises(PluginRepositoryError):
        repo.checkout("dev")


def test_current_commit_success() -> None:
    repo = PluginRepository.__new__(PluginRepository)
    repo.repo = DummyRepo()
    assert repo.current_commit() == "deadbeef"


def test_current_commit_failure() -> None:
    repo = PluginRepository.__new__(PluginRepository)
    repo.repo = BadRepo()
    with pytest.raises(PluginRepositoryError):
        repo.current_commit()
