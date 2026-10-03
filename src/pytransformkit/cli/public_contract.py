"""Executable builder for the frozen PyTransformKit CLI v1 contract."""

from __future__ import annotations

import inspect
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from typer.models import ArgumentInfo, OptionInfo

from pytransformkit.cli.app import app, root
from pytransformkit.cli.commands.contract import (
    inspect_command as contract_inspect_command,
)
from pytransformkit.cli.commands.doctor import doctor_command
from pytransformkit.cli.commands.engines import (
    inspect_command as engines_inspect_command,
)
from pytransformkit.cli.commands.engines import (
    list_command as engines_list_command,
)
from pytransformkit.cli.commands.schema import (
    convert_command as schema_convert_command,
)
from pytransformkit.cli.commands.schema import (
    format_command as schema_format_command,
)
from pytransformkit.cli.commands.schema import (
    inspect_command as schema_inspect_command,
)
from pytransformkit.cli.commands.schema import (
    validate_command as schema_validate_command,
)
from pytransformkit.cli.commands.version import version_command
from pytransformkit.cli.exit_codes import ExitCode
from pytransformkit.cli.models.errors import ErrorCategory
from pytransformkit.cli.rendering.json import CLI_REPORT_CONTRACT_VERSION

CLI_CONTRACT_VERSION = 1
CLI_CONTRACT_ID = "pytransformkit.cli"
CLI_FRAMEWORK_LINE = "1.2.x"
CLI_PROGRAM = "ptk"
CLI_ENTRYPOINT = "pytransformkit.cli.bootstrap:main"


@dataclass(frozen=True, slots=True)
class _CommandSpec:
    command_id: str
    path: tuple[str, ...]
    classification: str
    callback: Callable[..., object]


_COMMAND_SPECS: tuple[_CommandSpec, ...] = (
    _CommandSpec("version", ("version",), "report", version_command),
    _CommandSpec("doctor", ("doctor",), "report", doctor_command),
    _CommandSpec(
        "schema.validate",
        ("schema", "validate"),
        "report",
        schema_validate_command,
    ),
    _CommandSpec(
        "schema.inspect",
        ("schema", "inspect"),
        "report",
        schema_inspect_command,
    ),
    _CommandSpec(
        "schema.format",
        ("schema", "format"),
        "payload",
        schema_format_command,
    ),
    _CommandSpec(
        "schema.convert",
        ("schema", "convert"),
        "payload",
        schema_convert_command,
    ),
    _CommandSpec(
        "engines.list",
        ("engines", "list"),
        "report",
        engines_list_command,
    ),
    _CommandSpec(
        "engines.inspect",
        ("engines", "inspect"),
        "report",
        engines_inspect_command,
    ),
    _CommandSpec(
        "contract.inspect",
        ("contract", "inspect"),
        "report",
        contract_inspect_command,
    ),
)

RESERVED_FUTURE_COMMANDS = (
    "project",
    "run",
    "compile",
    "plan",
    "build",
    "test",
)


def _annotation_name(annotation: object) -> str:
    if annotation is inspect.Parameter.empty:
        return "unspecified"
    if isinstance(annotation, str):
        return annotation
    if annotation is None:
        return "None"
    return getattr(annotation, "__name__", str(annotation).replace("typing.", ""))


def _json_default(value: object) -> object:
    if value is ...:
        raise ValueError("Required Typer parameters do not expose a default.")
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    raise TypeError(f"Unsupported CLI contract default: {value!r}.")


def _parameter_contracts(
    callback: Callable[..., object],
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    arguments: list[dict[str, object]] = []
    options: list[dict[str, object]] = []

    for parameter in inspect.signature(callback, eval_str=False).parameters.values():
        metadata = parameter.default
        if isinstance(metadata, ArgumentInfo):
            required = metadata.default is ...
            item: dict[str, object] = {
                "name": parameter.name,
                "type": _annotation_name(parameter.annotation),
                "required": required,
            }
            if not required:
                item["default"] = _json_default(metadata.default)
            arguments.append(item)
            continue

        if isinstance(metadata, OptionInfo):
            required = metadata.default is ...
            flags = [
                declaration
                for declaration in metadata.param_decls
                if isinstance(declaration, str) and declaration.startswith("-")
            ]
            if not flags:
                raise RuntimeError(
                    f"CLI option {callback.__name__}.{parameter.name} "
                    "must declare an explicit public flag before contract freeze."
                )
            item = {
                "name": parameter.name,
                "flags": flags,
                "type": _annotation_name(parameter.annotation),
                "required": required,
                "eager": bool(getattr(metadata, "is_eager", False)),
            }
            if not required:
                item["default"] = _json_default(metadata.default)
            options.append(item)

    return arguments, options


def _registered_command_paths() -> set[tuple[str, ...]]:
    paths: set[tuple[str, ...]] = set()

    def visit(typer_app: Any, prefix: tuple[str, ...]) -> None:
        for command in typer_app.registered_commands:
            callback = command.callback
            name = command.name
            if callback is None or name is None:
                raise RuntimeError(
                    "Every frozen CLI command must have an explicit name and callback."
                )
            paths.add((*prefix, name))

        for group in typer_app.registered_groups:
            name = group.name
            nested = group.typer_instance
            if name is None:
                raise RuntimeError("Every frozen CLI group must have an explicit name.")
            visit(nested, (*prefix, name))

    visit(app, ())
    return paths


def _command_document(spec: _CommandSpec) -> dict[str, object]:
    arguments, options = _parameter_contracts(spec.callback)
    return {
        "path": list(spec.path),
        "classification": spec.classification,
        "arguments": arguments,
        "options": options,
    }


def _root_options() -> list[dict[str, object]]:
    _arguments, options = _parameter_contracts(root)
    return options


def build_cli_contract() -> dict[str, object]:
    """Build the exact frozen CLI v1 contract from current runtime authorities."""
    expected_paths = {spec.path for spec in _COMMAND_SPECS}
    registered_paths = _registered_command_paths()
    if registered_paths != expected_paths:
        raise RuntimeError(
            "Registered CLI command tree drifted from the frozen command registry: "
            f"expected={sorted(expected_paths)!r}, "
            f"actual={sorted(registered_paths)!r}."
        )

    commands = {
        spec.command_id: _command_document(spec)
        for spec in _COMMAND_SPECS
    }
    report_commands = [
        spec.command_id
        for spec in _COMMAND_SPECS
        if spec.classification == "report"
    ]
    payload_commands = [
        spec.command_id
        for spec in _COMMAND_SPECS
        if spec.classification == "payload"
    ]

    return {
        "contract": CLI_CONTRACT_ID,
        "contract_version": CLI_CONTRACT_VERSION,
        "status": "stable",
        "framework_line": CLI_FRAMEWORK_LINE,
        "program": CLI_PROGRAM,
        "entrypoint": CLI_ENTRYPOINT,
        "root_options": _root_options(),
        "command_tree": {
            "version": None,
            "doctor": None,
            "schema": ["validate", "inspect", "format", "convert"],
            "engines": ["list", "inspect"],
            "contract": ["inspect"],
        },
        "commands": commands,
        "report_commands": report_commands,
        "payload_commands": payload_commands,
        "json_envelope": {
            "contract_version": CLI_REPORT_CONTRACT_VERSION,
            "common_required": ["contract_version", "ok", "command"],
            "success_member": "data",
            "error_member": "error",
            "error_required": ["category", "message"],
            "error_optional": ["code", "path", "hint", "details"],
        },
        "exit_codes": {
            code.name.lower(): int(code)
            for code in ExitCode
        },
        "error_categories": [
            category.value
            for category in ErrorCategory
        ],
        "critical_error_mappings": {
            "contradictory_options": {
                "category": "invalid_usage",
                "exit_code": int(ExitCode.INVALID_USAGE),
            },
            "unknown_engine_id": {
                "category": "invalid_usage",
                "exit_code": int(ExitCode.INVALID_USAGE),
            },
            "unknown_contract_id": {
                "category": "invalid_usage",
                "exit_code": int(ExitCode.INVALID_USAGE),
            },
            "PTK-DECL-010": {
                "category": "missing_optional_dependency",
                "exit_code": int(ExitCode.MISSING_OPTIONAL_DEPENDENCY),
            },
            "filesystem_failure": {
                "category": "filesystem_error",
                "exit_code": int(ExitCode.FILESYSTEM_ERROR),
            },
            "remote_source": {
                "category": "unsupported_operation",
                "exit_code": int(ExitCode.UNSUPPORTED_OPERATION),
            },
            "keyboard_interrupt": {
                "category": "interrupted",
                "exit_code": int(ExitCode.INTERRUPTED),
            },
            "broken_pipe": {
                "category": "broken_pipe",
                "exit_code": int(ExitCode.BROKEN_PIPE),
            },
        },
        "streams": {
            "human_success": "stdout",
            "human_error": "stderr",
            "json_success": "stdout",
            "json_error": "stdout",
            "debug_diagnostics": "stderr",
            "payload": "stdout_or_explicit_file",
        },
        "reserved_future_commands": list(RESERVED_FUTURE_COMMANDS),
        "security_filesystem": {
            "remote_sources": False,
            "recursive_discovery": False,
            "implicit_overwrite": False,
            "format_write_requires_flag": True,
            "convert_output_requires_path": True,
            "convert_overwrite_requires_force": True,
            "mutable_symlinks": False,
            "implicit_include": False,
            "env_expansion": False,
            "plugin_command_injection": False,
            "project_discovery": False,
            "shell_execution": False,
        },
        "packaging": {
            "core_without_cli": True,
            "cli_extra": ["typer", "rich"],
            "yaml_extra": "PyYAML",
            "missing_cli_exit_code": int(ExitCode.MISSING_OPTIONAL_DEPENDENCY),
            "missing_yaml_framework_code": "PTK-DECL-010",
        },
    }


__all__ = [
    "CLI_CONTRACT_ID",
    "CLI_CONTRACT_VERSION",
    "CLI_ENTRYPOINT",
    "CLI_FRAMEWORK_LINE",
    "CLI_PROGRAM",
    "RESERVED_FUTURE_COMMANDS",
    "build_cli_contract",
]
