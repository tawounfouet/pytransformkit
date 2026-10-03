from __future__ import annotations

import importlib.machinery

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
