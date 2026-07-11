# ruff: noqa: S101, ARG001
# pyright: reportPrivateUsage=false, reportUnknownParameterType=false, reportMissingParameterType=false
from pathlib import Path
from types import SimpleNamespace

import pytest
from pytest import MonkeyPatch

import dotman.core.validator as validator
from dotman.errors.validator_errors import (
    DotmanMetadataFileCorruptedError,
    DotmanNotInitializedError,
    DotmanProfileNotInitializedError,
)


def make_config(dotfiles_dir: Path, home_dir: Path) -> SimpleNamespace:
    cfg = SimpleNamespace()
    cfg.dotfiles_dir = dotfiles_dir
    cfg.home_dir = home_dir
    return cfg


def test_ensure_profile_exists_raises_when_profiles_missing(
    tmp_path: Path, monkeypatch: MonkeyPatch
):
    dotfiles = tmp_path / "dotfiles"
    # do not create profiles dir
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setattr(validator, "load_config", lambda: make_config(dotfiles, home))

    v = validator.DotmanValidator()
    # profiles_dir does not exist -> should raise
    with pytest.raises(DotmanProfileNotInitializedError):
        v.ensure_profile_exists()


def test_enure_metadata_exists_raises_when_metadata_missing(
    tmp_path: Path, monkeypatch: MonkeyPatch
):
    dotfiles = tmp_path / "dotfiles"
    dotfiles.mkdir(parents=True)
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setattr(validator, "load_config", lambda: make_config(dotfiles, home))

    v = validator.DotmanValidator()
    # metadata file not present -> should raise DotmanMetadataFileCorruptedError
    with pytest.raises(DotmanMetadataFileCorruptedError):
        v.enure_metadata_exists()


@pytest.mark.parametrize(
    "setup_missing, expected_exception",
    [
        ("dotfiles", DotmanNotInitializedError),
        ("home", DotmanNotInitializedError),
        ("metadata", DotmanMetadataFileCorruptedError),
    ],
)
def test_validate_initialized_various_failures(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    setup_missing: str,
    expected_exception: type[BaseException],
):
    dotfiles = tmp_path / "dotfiles"
    home = tmp_path / "home"

    # create both by default
    dotfiles.mkdir(parents=True)
    home.mkdir()

    # create metadata file unless testing metadata missing
    metadata = dotfiles / "metadata.yml"
    if setup_missing != "metadata":
        metadata.parent.mkdir(parents=True, exist_ok=True)
        metadata.write_text("ok")

    # remove whichever should be missing
    if setup_missing == "dotfiles":
        # remove dotfiles dir entirely
        for p in list(dotfiles.glob("*")):
            p.unlink(missing_ok=True)
        dotfiles.rmdir()
    if setup_missing == "home":
        for p in list(home.glob("*")):
            p.unlink(missing_ok=True)
        home.rmdir()

    monkeypatch.setattr(validator, "load_config", lambda: make_config(dotfiles, home))
    v = validator.DotmanValidator()

    with pytest.raises(expected_exception):
        v.validate_initialized()


def test_call_executes_all_validate_and_ensure_methods(tmp_path: Path):
    """
    __call__ should discover and execute all methods whose names start with
    'validate_' or 'ensure_'. We create a tiny subclass that flips flags when run.
    """

    class MyValidator(validator.DotmanValidator):
        def __init__(self, base: Path):
            # use tmp_path-based directories so test is isolated
            self.dotfiles_dir = base / "tmp_dot"
            self.home_dir = base / "tmp_home"

            # create the directories and metadata so base ensure/validate methods succeed
            self.dotfiles_dir.mkdir(parents=True, exist_ok=True)
            self.home_dir.mkdir(parents=True, exist_ok=True)

            self.metadata = self.dotfiles_dir / "metadata.yml"
            self.metadata.parent.mkdir(parents=True, exist_ok=True)
            self.metadata.write_text("ok")

            self.profiles_dir = self.dotfiles_dir / "profiles"
            self.profiles_dir.mkdir(parents=True, exist_ok=True)

            self.called = []

        def validate_one(self):
            self.called.append("v1")

        def ensure_two(self):
            self.called.append("e2")

        # non-matching method should not be called
        def helper(self):
            self.called.append("h")

    v = MyValidator(tmp_path)
    v()  # invoke __call__
    assert "v1" in v.called
    assert "e2" in v.called
    assert "h" not in v.called


def test_require_initialized_decorator_calls_validator(monkeypatch: MonkeyPatch):
    # patch DotmanValidator.validate_initialized to record calls or raise
    called = {"count": 0}

    # must accept self because it's an instance method
    def fake_validate(self):
        called["count"] += 1

    monkeypatch.setattr(validator.DotmanValidator, "validate_initialized", fake_validate)

    @validator.require_initialized
    def target(a, b=1):
        return a + b

    # decorator should call validator before executing function
    assert target(2, b=3) == 5
    assert called["count"] == 1

    # now make validator raise and ensure the wrapped function is not executed
    def raise_validate(self):
        raise DotmanNotInitializedError()

    monkeypatch.setattr(validator.DotmanValidator, "validate_initialized", raise_validate)

    executed = {"ran": False}

    @validator.require_initialized
    def should_not_run():
        executed["ran"] = True

    with pytest.raises(DotmanNotInitializedError):
        should_not_run()

    assert executed["ran"] is False


def test_require_profile_decorator_calls_validator(monkeypatch: MonkeyPatch):
    called = {"count": 0}

    # must accept self because it's an instance method
    def fake_ensure(self):
        called["count"] += 1

    monkeypatch.setattr(validator.DotmanValidator, "ensure_profile_exists", fake_ensure)

    @validator.require_profile
    def target_profile(x):
        return x * 2

    assert target_profile(4) == 8
    assert called["count"] == 1

    # when ensure_profile_exists raises, wrapped function should not run
    def raise_ensure(self):
        raise DotmanProfileNotInitializedError()

    monkeypatch.setattr(validator.DotmanValidator, "ensure_profile_exists", raise_ensure)

    executed = {"ran": False}

    @validator.require_profile
    def should_not_run_profile():
        executed["ran"] = True

    with pytest.raises(DotmanProfileNotInitializedError):
        should_not_run_profile()

    assert executed["ran"] is False
