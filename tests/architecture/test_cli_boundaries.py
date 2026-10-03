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


def test_doctor_service_is_offline_and_does_not_import_optional_runtimes() -> None:
    doctor_path = CLI_ROOT / "services" / "doctor.py"
    forbidden_prefixes = (
        "http",
        "requests",
        "socket",
        "urllib",
        "pytransformkit.engines",
        "pytransformkit.plugins",
        "pytransformkit.schema_io",
        "pandas",
        "polars",
        "pyarrow",
        "duckdb",
        "yaml",
    )

    violations = [
        module
        for module in _imports(doctor_path)
        if module.startswith(forbidden_prefixes)
    ]

    assert violations == []


def test_schema_service_uses_public_schema_io_api_only() -> None:
    schema_service = CLI_ROOT / "services" / "schema.py"
    imports = _imports(schema_service)

    assert "pytransformkit.schema_io" in imports
    assert all(not module.startswith("pytransformkit.schema_io.") for module in imports)


def test_schema_validate_path_has_no_network_dependency() -> None:
    schema_paths = (
        CLI_ROOT / "commands" / "schema.py",
        CLI_ROOT / "services" / "schema.py",
    )
    forbidden_prefixes = (
        "http",
        "requests",
        "socket",
        "urllib.request",
        "pytransformkit.engines",
        "pytransformkit.plugins",
    )
    violations: list[str] = []

    for path in schema_paths:
        for module in _imports(path):
            if module.startswith(forbidden_prefixes):
                violations.append(f"{path}: forbidden import {module}")

    assert violations == []


def test_schema_inspect_does_not_depend_on_schema_codec() -> None:
    schema_paths = (
        CLI_ROOT / "commands" / "schema.py",
        CLI_ROOT / "services" / "schema.py",
    )
    violations: list[str] = []

    for path in schema_paths:
        for module in _imports(path):
            if module.startswith("pytransformkit.serialization"):
                violations.append(f"{path}: forbidden import {module}")

    assert violations == []


def test_schema_convert_service_uses_public_schema_and_wire_apis_only() -> None:
    convert_service = CLI_ROOT / "services" / "schema_convert.py"
    imports = _imports(convert_service)

    assert "pytransformkit.schema_io" in imports
    assert "pytransformkit.serialization" in imports
    assert all(not module.startswith("pytransformkit.schema_io.") for module in imports)
    assert all(
        not module.startswith("pytransformkit.serialization.") for module in imports
    )


def test_schema_convert_path_has_no_network_or_engine_dependency() -> None:
    convert_paths = (
        CLI_ROOT / "commands" / "schema.py",
        CLI_ROOT / "services" / "schema_convert.py",
    )
    forbidden_prefixes = (
        "http",
        "requests",
        "socket",
        "urllib.request",
        "pytransformkit.engines",
        "pytransformkit.plugins",
    )
    violations: list[str] = []

    for path in convert_paths:
        for module in _imports(path):
            if module.startswith(forbidden_prefixes):
                violations.append(f"{path}: forbidden import {module}")

    assert violations == []


def test_schema_command_module_does_not_eagerly_import_serialization() -> None:
    command_path = CLI_ROOT / "commands" / "schema.py"
    top_level_imports: list[str] = []
    tree = ast.parse(
        command_path.read_text(encoding="utf-8"),
        filename=str(command_path),
    )

    for node in tree.body:
        if isinstance(node, ast.Import):
            top_level_imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            top_level_imports.append(node.module)

    assert all(
        not module.startswith("pytransformkit.serialization")
        for module in top_level_imports
    )


def test_engines_cli_path_does_not_import_optional_adapters_or_plugins() -> None:
    engine_paths = (
        CLI_ROOT / "commands" / "engines.py",
        CLI_ROOT / "services" / "engines.py",
    )
    forbidden_prefixes = (
        "pytransformkit.adapters",
        "pytransformkit.infrastructure.engines",
        "pytransformkit.plugins",
        "pandas",
        "polars",
        "pyarrow",
        "duckdb",
    )
    violations: list[str] = []

    for path in engine_paths:
        for module in _imports(path):
            if module.startswith(forbidden_prefixes):
                violations.append(f"{path}: forbidden import {module}")

    assert violations == []


def test_engines_service_uses_conformance_authority() -> None:
    engine_service = CLI_ROOT / "services" / "engines.py"
    imports = _imports(engine_service)

    assert "pytransformkit.conformance.model" in imports
    assert all(
        not module.startswith("pytransformkit.application.execution")
        for module in imports
    )


def test_contract_inspection_is_offline_and_plugin_safe() -> None:
    contract_paths = (
        CLI_ROOT / "commands" / "contract.py",
        CLI_ROOT / "services" / "contracts.py",
    )
    forbidden_prefixes = (
        "http",
        "requests",
        "socket",
        "urllib.request",
        "subprocess",
        "pytransformkit.plugins",
        "pytransformkit.adapters",
        "pytransformkit.infrastructure.engines",
    )
    violations: list[str] = []

    for path in contract_paths:
        for module in _imports(path):
            if module.startswith(forbidden_prefixes):
                violations.append(f"{path}: forbidden import {module}")

    assert violations == []


def test_contract_service_uses_packaged_resources_not_checkout_paths() -> None:
    service_path = CLI_ROOT / "services" / "contracts.py"
    source = service_path.read_text(encoding="utf-8")

    assert "from importlib import resources" in source
    assert 'Path("contracts")' not in source
    assert '"contracts/' not in source
    assert "Path.cwd()" not in source
