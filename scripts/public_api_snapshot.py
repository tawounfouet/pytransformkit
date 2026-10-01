"""Generate or verify the PyTransformKit V1 public API freeze snapshot."""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
import sys
import tomllib
from enum import Enum
from pathlib import Path

STABLE_MODULES = (
    "pytransformkit",
    "pytransformkit.authoring",
    "pytransformkit.expressions",
    "pytransformkit.functions",
    "pytransformkit.transformations",
    "pytransformkit.planning",
    "pytransformkit.runtime",
    "pytransformkit.engines",
    "pytransformkit.lineage",
    "pytransformkit.serialization",
    "pytransformkit.diagnostics",
    "pytransformkit.plugins",
    "pytransformkit.quality",
    "pytransformkit.window",
    "pytransformkit.conformance",
    "pytransformkit.readers",
    "pytransformkit.writers",
    "pytransformkit.errors",
    "pytransformkit.adapters.pandas",
    "pytransformkit.adapters.polars",
)

PROTOCOLS = (
    ("pytransformkit.engines", "EngineAdapter"),
    ("pytransformkit.readers", "Reader"),
    ("pytransformkit.writers", "Writer"),
    ("pytransformkit.plugins", "ResourceResolver"),
    ("pytransformkit.plugins", "FunctionExtension"),
    ("pytransformkit.plugins", "OptimizerRule"),
    ("pytransformkit.plugins", "TelemetrySink"),
)

CODECS = (
    "DataTypeCodec",
    "DiagnosticCodec",
    "ExecutionManifestCodec",
    "ExpressionCodec",
    "FieldCodec",
    "LineageCodec",
    "LogicalPlanCodec",
    "ResourceReferenceCodec",
    "SchemaCodec",
    "TransformationExecutionReferenceCodec",
    "TransformationPlanCodec",
)

STABLE_RUNTIME_EXTRAS = ("duckdb", "io", "pandas", "polars", "pyarrow")
TOOLING_EXTRAS = ("dev", "performance")
LEGACY_ROOT_NAMES = (
    "CredentialReference",
    "EngineRegistry",
    "ExecutionContext",
    "ExecutionMode",
    "Pipeline",
    "PipelineExecutionResult",
    "RetrySafety",
    "RunPipelineService",
    "WriteMode",
    "WriteStatus",
)
FORBIDDEN_PUBLIC_TYPES = (
    "TransformationGraph",
    "OptimizedLogicalPlan",
    "PhysicalPlan",
)


def _signature(value: object) -> str | None:
    if not (inspect.isclass(value) or inspect.isfunction(value)):
        return None
    try:
        return str(inspect.signature(value, eval_str=False))
    except (TypeError, ValueError):
        return None


def _exports(module_name: str) -> tuple[str, ...]:
    module = importlib.import_module(module_name)
    names = getattr(module, "__all__", None)
    if names is None:
        raise RuntimeError(f"{module_name} must define __all__ before V1 freeze.")
    return tuple(names)


def _module_snapshot(module_name: str) -> dict[str, object]:
    module = importlib.import_module(module_name)
    exports = _exports(module_name)
    signatures: dict[str, str] = {}
    enum_members: dict[str, dict[str, object]] = {}

    for name in exports:
        value = getattr(module, name)
        signature = _signature(value)
        if signature is not None:
            signatures[name] = signature

        if inspect.isclass(value) and issubclass(value, Enum):
            enum_members[name] = {
                member.name: member.value for member in value
            }

    return {
        "exports": list(exports),
        "signatures": signatures,
        "enum_members": enum_members,
    }


def _protocol_snapshot() -> dict[str, object]:
    result: dict[str, object] = {}
    for module_name, symbol_name in PROTOCOLS:
        protocol = getattr(importlib.import_module(module_name), symbol_name)
        members: dict[str, str] = {}
        for name, value in vars(protocol).items():
            if name.startswith("_"):
                continue
            if isinstance(value, property):
                signature = _signature(value.fget)
            else:
                signature = _signature(value)
            if signature is not None:
                members[name] = signature
        result[f"{module_name}.{symbol_name}"] = members
    return result


def _exception_snapshot() -> dict[str, list[str]]:
    module = importlib.import_module("pytransformkit.errors")
    result: dict[str, list[str]] = {}
    for name in _exports("pytransformkit.errors"):
        value = getattr(module, name)
        if not inspect.isclass(value) or not issubclass(value, BaseException):
            continue
        bases: list[str] = []
        for base in value.__mro__[1:]:
            if base is object:
                continue
            bases.append(base.__name__)
            if base is BaseException:
                break
        result[name] = bases
    return result


def _wire_snapshot() -> dict[str, object]:
    module = importlib.import_module("pytransformkit.serialization")
    result: dict[str, object] = {}
    for name in CODECS:
        codec = getattr(module, name)
        result[name] = {
            "contract": codec.contract,
            "contract_version": codec.contract_version,
        }
    return result


def _extras_snapshot(project_file: Path) -> dict[str, list[str]]:
    with project_file.open("rb") as stream:
        project = tomllib.load(stream)["project"]
    extras = project["optional-dependencies"]
    available = tuple(sorted(extras))
    expected = set(STABLE_RUNTIME_EXTRAS) | set(TOOLING_EXTRAS)
    if set(available) != expected:
        raise RuntimeError(
            "Optional extra names drifted before snapshot creation: "
            f"expected={sorted(expected)!r}, actual={list(available)!r}."
        )
    return {
        "stable_runtime": list(STABLE_RUNTIME_EXTRAS),
        "tooling": list(TOOLING_EXTRAS),
    }


def build_snapshot(project_file: Path) -> dict[str, object]:
    root = importlib.import_module("pytransformkit")
    root_exports = set(_exports("pytransformkit"))

    forbidden_present = sorted(
        name for name in FORBIDDEN_PUBLIC_TYPES if hasattr(root, name)
    )
    if forbidden_present:
        raise RuntimeError(
            f"Forbidden V1 public types are present: {forbidden_present!r}."
        )

    legacy_promoted = sorted(name for name in LEGACY_ROOT_NAMES if name in root_exports)
    if legacy_promoted:
        raise RuntimeError(
            f"Legacy/pre-V1 names leaked into root __all__: {legacy_promoted!r}."
        )

    conformance = importlib.import_module("pytransformkit.conformance")
    profiles = conformance.PUBLISHED_ENGINE_PROFILES

    return {
        "snapshot_version": 1,
        "framework_line": "0.8.x",
        "modules": {
            module_name: _module_snapshot(module_name)
            for module_name in STABLE_MODULES
        },
        "protocol_members": _protocol_snapshot(),
        "exception_hierarchy": _exception_snapshot(),
        "extras": _extras_snapshot(project_file),
        "engine_ids": sorted(profiles),
        "wire_contracts": _wire_snapshot(),
        "root_legacy_compatibility": list(LEGACY_ROOT_NAMES),
        "forbidden_public_types": list(FORBIDDEN_PUBLIC_TYPES),
    }


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", type=Path)
    group.add_argument("--check", type=Path)
    parser.add_argument(
        "--project",
        type=Path,
        default=Path("pyproject.toml"),
    )
    return parser.parse_args()


def main() -> int:
    args = _arguments()
    actual = build_snapshot(args.project)

    if args.write is not None:
        args.write.parent.mkdir(parents=True, exist_ok=True)
        args.write.write_text(
            json.dumps(actual, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(f"Wrote public API snapshot to {args.write}")
        return 0

    expected = json.loads(args.check.read_text(encoding="utf-8"))
    if actual == expected:
        print("Public API freeze: PASS")
        return 0

    expected_text = json.dumps(expected, indent=2, sort_keys=True)
    actual_text = json.dumps(actual, indent=2, sort_keys=True)
    print("Public API freeze: FAIL", file=sys.stderr)
    print("--- expected", file=sys.stderr)
    print(expected_text, file=sys.stderr)
    print("--- actual", file=sys.stderr)
    print(actual_text, file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
