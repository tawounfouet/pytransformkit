from __future__ import annotations

import importlib.machinery

import pytest

from pytransformkit.cli import bootstrap


def test_missing_cli_dependencies_reports_only_missing_modules(monkeypatch) -> None:
    def fake_find_spec(name: str):
        if name == "rich":
            return None
        return importlib.machinery.ModuleSpec(name, loader=None)

    monkeypatch.setattr(bootstrap.importlib.util, "find_spec", fake_find_spec)

    assert bootstrap._missing_cli_dependencies() == ("rich",)


def test_main_without_cli_dependencies_is_controlled(
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.setattr(
        bootstrap,
        "_missing_cli_dependencies",
        lambda: ("typer", "rich"),
    )

    assert bootstrap.main(()) == 11

    captured = capsys.readouterr()
    assert captured.out == ""
    assert "PyTransformKit CLI dependencies are not installed." in captured.err
    assert "typer, rich" in captured.err
    assert 'pip install "pytransformkit[cli]"' in captured.err


def test_main_returns_broken_pipe_exit_for_epipe_from_click_boundary(
    monkeypatch,
) -> None:
    pytest.importorskip("click")
    pytest.importorskip("typer")
    pytest.importorskip("rich")
    monkeypatch.setattr(bootstrap, "_missing_cli_dependencies", lambda: ())

    import pytransformkit.cli.app as app_module

    def fail_app(*args, **kwargs):
        raise BrokenPipeError()

    monkeypatch.setattr(app_module, "app", fail_app)

    assert bootstrap.main(()) == 141
