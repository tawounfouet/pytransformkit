from __future__ import annotations

import subprocess
import sys
import tomllib
from pathlib import Path

import pytransformkit
import pytransformkit.schema_io as schema_io


def test_schema_io_bootstrap_does_not_expand_root_api() -> None:
    assert "schema_io" not in pytransformkit.__all__
    assert schema_io.__all__ == []


def test_schema_io_import_does_not_eagerly_import_yaml() -> None:
    code = (
        "import sys; import pytransformkit.schema_io; assert 'yaml' not in sys.modules"
    )
    subprocess.run([sys.executable, "-c", code], check=True)


def test_yaml_support_is_optional_package_metadata() -> None:
    project = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    assert project["project"]["dependencies"] == []
    assert project["project"]["optional-dependencies"]["yaml"] == ["PyYAML>=6,<7"]
