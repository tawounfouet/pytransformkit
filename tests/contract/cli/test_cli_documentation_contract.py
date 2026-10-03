from __future__ import annotations

import json
from pathlib import Path

import pytest

pytest.importorskip("typer")
pytest.importorskip("rich")
pytest.importorskip("yaml")

from typer.testing import CliRunner

from pytransformkit.cli.app import app

ROOT = Path(__file__).resolve().parents[3]
runner = CliRunner()

DOCS = (
    ROOT / "docs" / "CLI_GETTING_STARTED.md",
    ROOT / "docs" / "CLI_REFERENCE.md",
    ROOT / "docs" / "RELEASE_NOTES_1_2_0.md",
    ROOT / "README.md",
    ROOT / "CHANGELOG.md",
)


def test_cli_release_documentation_files_exist() -> None:
    for path in DOCS:
        assert path.is_file(), path


def test_cli_reference_covers_frozen_command_ids() -> None:
    contract = json.loads(
        (ROOT / "contracts" / "cli_contract_v1.json").read_text(encoding="utf-8")
    )
    reference = (ROOT / "docs" / "CLI_REFERENCE.md").read_text(encoding="utf-8")

    commands = contract["commands"]
    assert isinstance(commands, dict)

    for command_id, document in commands.items():
        assert command_id in reference or " ".join(document["path"]) in reference


def test_readme_links_cli_guides_and_release_notes() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "docs/CLI_GETTING_STARTED.md" in readme
    assert "docs/CLI_REFERENCE.md" in readme
    assert "docs/RELEASE_NOTES_1_2_0.md" in readme
    assert 'pip install "pytransformkit[cli]"' in readme
    assert 'pip install "pytransformkit[cli,yaml]"' in readme


def test_changelog_records_stable_1_2_release_date() -> None:
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")

    assert "## [Unreleased]\n\nNo changes yet." in changelog
    assert "## [1.2.0] - 2026-10-03" in changelog
    assert "1.2.0rc2" not in changelog


def test_release_notes_describe_stable_publication_evidence() -> None:
    notes = (ROOT / "docs" / "RELEASE_NOTES_1_2_0.md").read_text(encoding="utf-8")

    assert "PyTransformKit `1.2.0` is the stable Developer CLI release." in notes
    assert "PyPI Trusted Publishing" in notes
    assert "public consumer smoke" in notes
    assert "v1.2.0" in notes


def test_shell_completion_options_remain_absent_after_contract_freeze() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "--install-completion" not in result.stdout
    assert "--show-completion" not in result.stdout

    contract = json.loads(
        (ROOT / "contracts" / "cli_contract_v1.json").read_text(encoding="utf-8")
    )
    flags = {flag for option in contract["root_options"] for flag in option["flags"]}
    assert "--install-completion" not in flags
    assert "--show-completion" not in flags
