from __future__ import annotations

import ast
from pathlib import Path

DOMAIN_ROOT = Path("src/pytransformkit/domain")
FORBIDDEN_TOP_LEVEL_MODULES = {"pandas", "polars", "pyarrow", "duckdb"}
FORBIDDEN_INTERNAL_PREFIX = "pytransformkit.infrastructure"


def _python_files() -> tuple[Path, ...]:
    return tuple(sorted(DOMAIN_ROOT.rglob("*.py")))


def test_domain_does_not_import_engine_libraries() -> None:
    violations: list[str] = []

    for path in _python_files():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top_level = alias.name.split(".", maxsplit=1)[0]
                    if top_level in FORBIDDEN_TOP_LEVEL_MODULES:
                        violations.append(f"{path}: import {alias.name}")
            elif isinstance(node, ast.ImportFrom) and node.module:
                top_level = node.module.split(".", maxsplit=1)[0]
                if top_level in FORBIDDEN_TOP_LEVEL_MODULES:
                    violations.append(f"{path}: from {node.module} import ...")

    assert violations == []


def test_domain_does_not_import_infrastructure() -> None:
    violations: list[str] = []

    for path in _python_files():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.ImportFrom)
                and node.module
                and node.module.startswith(FORBIDDEN_INTERNAL_PREFIX)
            ):
                violations.append(f"{path}: from {node.module} import ...")
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith(FORBIDDEN_INTERNAL_PREFIX):
                        violations.append(f"{path}: import {alias.name}")

    assert violations == []
