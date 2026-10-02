from __future__ import annotations

import ast
from pathlib import Path

DOMAIN_ROOT = Path("src/pytransformkit/domain")
SCHEMA_IO_ROOT = Path("src/pytransformkit/schema_io")
OPTIONAL_TOP_LEVEL_MODULES = {"yaml", "pandas", "polars", "pyarrow", "duckdb"}


def _python_files(root: Path) -> tuple[Path, ...]:
    return tuple(sorted(root.rglob("*.py")))


def _module_level_imports(path: Path) -> tuple[str, ...]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imports: list[str] = []

    for node in tree.body:
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)

    return tuple(imports)


def test_domain_does_not_import_schema_io() -> None:
    violations: list[str] = []

    for path in _python_files(DOMAIN_ROOT):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith("pytransformkit.schema_io"):
                        violations.append(f"{path}: import {alias.name}")
            elif (
                isinstance(node, ast.ImportFrom)
                and node.module
                and node.module.startswith("pytransformkit.schema_io")
            ):
                violations.append(f"{path}: from {node.module} import ...")

    assert violations == []


def test_schema_io_has_no_eager_optional_imports() -> None:
    violations: list[str] = []

    for path in _python_files(SCHEMA_IO_ROOT):
        for module in _module_level_imports(path):
            top_level = module.split(".", maxsplit=1)[0]
            if top_level in OPTIONAL_TOP_LEVEL_MODULES:
                violations.append(f"{path}: eager import {module}")

    assert violations == []


def test_definition_model_has_no_parser_domain_engine_or_io_dependencies() -> None:
    model_path = SCHEMA_IO_ROOT / "_model.py"
    forbidden_top_level = {
        "yaml",
        "pandas",
        "polars",
        "pyarrow",
        "duckdb",
        "pathlib",
        "os",
        "urllib",
        "requests",
    }
    forbidden_internal_prefixes = (
        "pytransformkit.domain",
        "pytransformkit.infrastructure",
    )
    violations: list[str] = []

    for module in _module_level_imports(model_path):
        top_level = module.split(".", maxsplit=1)[0]
        if top_level in forbidden_top_level or module.startswith(
            forbidden_internal_prefixes
        ):
            violations.append(f"{model_path}: forbidden import {module}")

    assert violations == []
