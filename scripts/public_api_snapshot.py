"""Generate or verify the PyTransformKit V1 public API freeze snapshot."""

from __future__ import annotations

import argparse
import hashlib
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

SIGNATURE_TARGETS = (
    ("pytransformkit", "DataType"),
    ("pytransformkit", "Dataset"),
    ("pytransformkit", "Field"),
    ("pytransformkit", "Schema"),
    ("pytransformkit", "TransformationPlan"),
    ("pytransformkit", "LogicalPlan"),
    ("pytransformkit", "InputBinding"),
    ("pytransformkit", "OutputBinding"),
    ("pytransformkit", "TransformationRuntime"),
    ("pytransformkit", "TransformationResult"),
    ("pytransformkit", "ResourceReference"),
    ("pytransformkit", "col"),
    ("pytransformkit", "lit"),
    ("pytransformkit.authoring", "TransformationPlanBuilder"),
    ("pytransformkit.planning", "TransformationCompiler"),
    ("pytransformkit.planning", "LogicalOptimizer"),
    ("pytransformkit.engines", "EngineRegistry"),
    ("pytransformkit.engines", "EngineAdapter"),
    ("pytransformkit.engines", "EngineDescriptor"),
    ("pytransformkit.runtime", "CorrelationContext"),
    ("pytransformkit.plugins", "PluginRegistry"),
    ("pytransformkit.plugins", "PluginDescriptor"),
    ("pytransformkit.plugins", "PluginCompatibility"),
    ("pytransformkit.readers", "ReadRequest"),
    ("pytransformkit.readers", "ReadResult"),
    ("pytransformkit.writers", "WriteRequest"),
    ("pytransformkit.writers", "WriteResult"),
    ("pytransformkit.adapters.pandas", "PandasEngineAdapter"),
    ("pytransformkit.adapters.polars", "PolarsEngineAdapter"),
)

ENUM_TARGETS = (
    ("pytransformkit.engines", "EngineCapability"),
    ("pytransformkit.runtime", "CancellationSupport"),
    ("pytransformkit.runtime", "ExecutionMode"),
    ("pytransformkit.runtime", "ExecutionStatus"),
    ("pytransformkit.runtime", "FailureCategory"),
    ("pytransformkit.runtime", "OutcomeUncertainty"),
    ("pytransformkit.runtime", "Retryability"),
    ("pytransformkit.runtime", "RetrySafety"),
    ("pytransformkit.runtime", "WriteMode"),
    ("pytransformkit.runtime", "WriteStatus"),
    ("pytransformkit.diagnostics", "DiagnosticSeverity"),
    ("pytransformkit.diagnostics", "MetricKind"),
    ("pytransformkit.plugins", "PluginKind"),
    ("pytransformkit.conformance", "ConformanceDimension"),
    ("pytransformkit.conformance", "ConformanceStatus"),
    ("pytransformkit.conformance", "EngineStability"),
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
V1_1_STABLE_RUNTIME_ADDITIONS = ("yaml",)
TOOLING_EXTRAS = ("dev", "performance")

V1_1_ADDITIVE_MODULES = ("pytransformkit.schema_io",)
V1_1_SIGNATURE_TARGETS = (
    ("pytransformkit.schema_io", "load_schema"),
    ("pytransformkit.schema_io", "loads_schema"),
    ("pytransformkit.schema_io", "load_schemas"),
    ("pytransformkit.schema_io", "loads_schemas"),
    ("pytransformkit.schema_io", "dump_schema"),
    ("pytransformkit.schema_io", "dumps_schema"),
    ("pytransformkit.schema_io", "dump_schemas"),
    ("pytransformkit.schema_io", "dumps_schemas"),
)
V1_1_DECLARATIVE_EXCEPTIONS = (
    "DeclarativeSchemaError",
    "DeclarativeSchemaParseError",
    "DeclarativeSchemaVersionError",
    "DeclarativeSchemaValidationError",
    "DeclarativeSchemaUnknownPropertyError",
    "DeclarativeSchemaTypeError",
    "DeclarativeSchemaDuplicateKeyError",
    "DeclarativeSchemaDuplicateFieldError",
    "DeclarativeSchemaDuplicateSchemaError",
    "DeclarativeSchemaCardinalityError",
    "DeclarativeSchemaDependencyError",
    "DeclarativeSchemaIOError",
    "DeclarativeSchemaExportError",
    "DeclarativeSchemaLimitError",
)
V1_1_DECLARATIVE_SUPPORTING_VALUES = ("DeclarativeErrorContext",)
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


def _v1_exports(module_name: str) -> tuple[str, ...]:
    names = _exports(module_name)
    if module_name != "pytransformkit.errors":
        return names
    return tuple(name for name in names if not name.startswith("Declarative"))


def _module_snapshot(module_name: str) -> dict[str, object]:
    return {"exports": list(_v1_exports(module_name))}


def _signature_snapshot(
    targets: tuple[tuple[str, str], ...] = SIGNATURE_TARGETS,
) -> dict[str, str]:
    result: dict[str, str] = {}
    for module_name, symbol_name in targets:
        value = getattr(importlib.import_module(module_name), symbol_name)
        signature = _signature(value)
        if signature is None:
            raise RuntimeError(
                f"Cannot freeze signature for {module_name}.{symbol_name}."
            )
        result[f"{module_name}.{symbol_name}"] = signature
    return result


def _enum_snapshot() -> dict[str, dict[str, object]]:
    result: dict[str, dict[str, object]] = {}
    for module_name, symbol_name in ENUM_TARGETS:
        value = getattr(importlib.import_module(module_name), symbol_name)
        if not inspect.isclass(value) or not issubclass(value, Enum):
            raise RuntimeError(f"{module_name}.{symbol_name} is not an enum.")
        result[f"{module_name}.{symbol_name}"] = {
            member.name: member.value for member in value
        }
    return result


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
    for name in _v1_exports("pytransformkit.errors"):
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
    available = set(extras)
    expected = set(STABLE_RUNTIME_EXTRAS) | set(TOOLING_EXTRAS)
    missing = sorted(expected - available)
    if missing:
        raise RuntimeError(
            "Frozen V1 optional extra names disappeared: "
            f"missing={missing!r}, actual={sorted(available)!r}."
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
            module_name: _module_snapshot(module_name) for module_name in STABLE_MODULES
        },
        "signatures": _signature_snapshot(),
        "protocol_members": _protocol_snapshot(),
        "exception_hierarchy": _exception_snapshot(),
        "enum_members": _enum_snapshot(),
        "extras": _extras_snapshot(project_file),
        "engine_ids": sorted(profile.engine_id for profile in profiles),
        "wire_contracts": _wire_snapshot(),
        "root_legacy_compatibility": list(LEGACY_ROOT_NAMES),
        "forbidden_public_types": list(FORBIDDEN_PUBLIC_TYPES),
    }


def _direct_exception_parent(name: str) -> str:
    module = importlib.import_module("pytransformkit.errors")
    value = getattr(module, name)
    if not inspect.isclass(value) or not issubclass(value, BaseException):
        raise RuntimeError(f"{name} is not a public exception type.")
    return value.__bases__[0].__name__


def build_v1_1_successor_manifest(
    project_file: Path,
    baseline_file: Path,
) -> dict[str, object]:
    """Freeze additive 1.1 API while proving the 1.0 baseline is unchanged."""
    baseline = json.loads(baseline_file.read_text(encoding="utf-8"))
    # The historical V1 runtime freeze is qualified independently with
    # --line 1.0. The 1.1 successor references that immutable manifest so it
    # can be checked from a minimal declarative-only installation without
    # importing optional engine adapters.
    schema_io_exports = list(_exports("pytransformkit.schema_io"))
    errors_module = importlib.import_module("pytransformkit.errors")
    error_exports = set(_exports("pytransformkit.errors"))

    missing_errors = sorted(
        name for name in V1_1_DECLARATIVE_EXCEPTIONS if name not in error_exports
    )
    missing_values = sorted(
        name for name in V1_1_DECLARATIVE_SUPPORTING_VALUES if name not in error_exports
    )
    if missing_errors or missing_values:
        raise RuntimeError(
            "Declarative public error surface is incomplete: "
            f"missing_errors={missing_errors!r}, missing_values={missing_values!r}."
        )

    for name in (*V1_1_DECLARATIVE_EXCEPTIONS, *V1_1_DECLARATIVE_SUPPORTING_VALUES):
        if not hasattr(errors_module, name):
            raise RuntimeError(f"pytransformkit.errors is missing {name!r}.")

    with project_file.open("rb") as stream:
        project = tomllib.load(stream)["project"]
    available_extras = set(project["optional-dependencies"])
    missing_extras = sorted(set(V1_1_STABLE_RUNTIME_ADDITIONS) - available_extras)
    if missing_extras:
        raise RuntimeError(f"Missing stable 1.1 runtime extras: {missing_extras!r}.")

    baseline_extras = list(baseline["extras"]["stable_runtime"])
    stable_runtime_extras = [
        *baseline_extras,
        *V1_1_STABLE_RUNTIME_ADDITIONS,
    ]

    return {
        "snapshot_version": 2,
        "framework_line": "1.1.x",
        "predecessor": "contracts/public_api_v1.json",
        "v1_baseline_category_hashes": baseline["category_hashes"],
        "unchanged_v1": {
            "root_exports": baseline["root_exports"],
            "root_legacy_compatibility": baseline["root_legacy_compatibility"],
            "engine_ids": baseline["engine_ids"],
            "wire_contracts": baseline["wire_contracts"],
            "stable_runtime_extras": baseline_extras,
        },
        "additions": {
            "modules": {
                module_name: {"exports": list(_exports(module_name))}
                for module_name in V1_1_ADDITIVE_MODULES
            },
            "signatures": _signature_snapshot(V1_1_SIGNATURE_TARGETS),
            "exception_hierarchy": {
                name: _direct_exception_parent(name)
                for name in V1_1_DECLARATIVE_EXCEPTIONS
            },
            "supporting_values": list(V1_1_DECLARATIVE_SUPPORTING_VALUES),
            "stable_runtime_extras": list(V1_1_STABLE_RUNTIME_ADDITIONS),
        },
        "stable_runtime_extras": stable_runtime_extras,
        "schema_io_exports": schema_io_exports,
    }


def _category_digest(value: object) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def freeze_manifest(snapshot: dict[str, object]) -> dict[str, object]:
    """Reduce the full API snapshot to a reviewable cryptographic manifest."""
    category_names = (
        "modules",
        "signatures",
        "protocol_members",
        "exception_hierarchy",
        "enum_members",
        "extras",
        "engine_ids",
        "wire_contracts",
        "root_legacy_compatibility",
        "forbidden_public_types",
    )
    return {
        "snapshot_version": snapshot["snapshot_version"],
        "framework_line": snapshot["framework_line"],
        "category_hashes": {
            name: _category_digest(snapshot[name]) for name in category_names
        },
        "root_exports": snapshot["modules"]["pytransformkit"]["exports"],
        "extras": snapshot["extras"],
        "engine_ids": snapshot["engine_ids"],
        "wire_contracts": snapshot["wire_contracts"],
        "root_legacy_compatibility": snapshot["root_legacy_compatibility"],
        "forbidden_public_types": snapshot["forbidden_public_types"],
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
    parser.add_argument(
        "--line",
        choices=("1.0", "1.1"),
        default="1.0",
    )
    parser.add_argument(
        "--baseline",
        type=Path,
        default=Path("contracts/public_api_v1.json"),
    )
    return parser.parse_args()


def main() -> int:
    args = _arguments()
    if args.line == "1.0":
        actual = freeze_manifest(build_snapshot(args.project))
        pass_message = "Public API freeze: PASS"
    else:
        actual = build_v1_1_successor_manifest(args.project, args.baseline)
        pass_message = "Public API 1.1 successor freeze: PASS"

    if args.write is not None:
        args.write.parent.mkdir(parents=True, exist_ok=True)
        args.write.write_text(
            json.dumps(actual, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(f"Wrote public API freeze manifest to {args.write}")
        return 0

    expected = json.loads(args.check.read_text(encoding="utf-8"))
    if actual == expected:
        print(pass_message)
        return 0

    print("Public API freeze: FAIL", file=sys.stderr)
    if args.line == "1.0":
        expected_hashes = expected.get("category_hashes", {})
        actual_hashes = actual.get("category_hashes", {})
        changed = sorted(
            name
            for name in set(expected_hashes) | set(actual_hashes)
            if expected_hashes.get(name) != actual_hashes.get(name)
        )
        print(f"Changed categories: {changed!r}", file=sys.stderr)
    print("--- expected manifest", file=sys.stderr)
    print(json.dumps(expected, indent=2, sort_keys=True), file=sys.stderr)
    print("--- actual manifest", file=sys.stderr)
    print(json.dumps(actual, indent=2, sort_keys=True), file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
