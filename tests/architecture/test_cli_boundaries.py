from __future__ import annotations

import ast
from pathlib import Path

PACKAGE_ROOT = Path("src/pytransformkit")
CLI_ROOT = PACKAGE_ROOT / "cli"
JSON_RENDERER = CLI_ROOT / "rendering" / "json.py"


def _imports(path: Path) -> tuple[str, ...]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
    return tuple(imports)


def test_core_packages_do_not_import_cli() -> None:
    violations: list[str] = []

    for path in sorted(PACKAGE_ROOT.rglob("*.py")):
        if path.is_relative_to(CLI_ROOT):
            continue
        for module in _imports(path):
            if module.startswith("pytransformkit.cli"):
                violations.append(f"{path}: forbidden import {module}")

    assert violations == []


def test_json_renderer_has_no_rich_dependency() -> None:
    violations = [
        module for module in _imports(JSON_RENDERER) if module.startswith("rich")
    ]

    assert violations == []


def test_cli_context_has_no_project_runtime_dependencies() -> None:
    context_path = CLI_ROOT / "context.py"
    forbidden_prefixes = (
        "pytransformkit.domain",
        "pytransformkit.application",
        "pytransformkit.engines",
        "pytransformkit.runtime",
    )

    violations = [
        module
        for module in _imports(context_path)
        if module.startswith(forbidden_prefixes)
    ]

    assert violations == []


def test_version_path_has_no_engine_or_schema_io_dependencies() -> None:
    version_paths = (
        CLI_ROOT / "commands" / "version.py",
        CLI_ROOT / "services" / "version.py",
    )
    forbidden_prefixes = (
        "pytransformkit.engines",
        "pytransformkit.schema_io",
        "pandas",
        "polars",
        "pyarrow",
        "duckdb",
        "yaml",
    )
    violations: list[str] = []

    for path in version_paths:
        for module in _imports(path):
            if module.startswith(forbidden_prefixes):
                violations.append(f"{path}: forbidden import {module}")

    assert violations == []
