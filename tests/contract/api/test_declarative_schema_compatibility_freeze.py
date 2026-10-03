from __future__ import annotations

import inspect
import json
from pathlib import Path

import pytransformkit
import pytransformkit.errors as errors
import pytransformkit.schema_io as schema_io

ROOT = Path(__file__).parents[3]
CONTRACTS = ROOT / "contracts"

_SCHEMA_IO_EXPORTS = [
    "dump_schema",
    "dump_schemas",
    "dumps_schema",
    "dumps_schemas",
    "load_schema",
    "load_schemas",
    "loads_schema",
    "loads_schemas",
]

_DECLARATIVE_CODES = {
    "DeclarativeSchemaError": "PTK-DECL-000",
    "DeclarativeSchemaParseError": "PTK-DECL-001",
    "DeclarativeSchemaVersionError": "PTK-DECL-002",
    "DeclarativeSchemaValidationError": "PTK-DECL-003",
    "DeclarativeSchemaUnknownPropertyError": "PTK-DECL-004",
    "DeclarativeSchemaTypeError": "PTK-DECL-005",
    "DeclarativeSchemaDuplicateKeyError": "PTK-DECL-006",
    "DeclarativeSchemaDuplicateFieldError": "PTK-DECL-007",
    "DeclarativeSchemaDuplicateSchemaError": "PTK-DECL-008",
    "DeclarativeSchemaCardinalityError": "PTK-DECL-009",
    "DeclarativeSchemaDependencyError": "PTK-DECL-010",
    "DeclarativeSchemaIOError": "PTK-DECL-011",
    "DeclarativeSchemaExportError": "PTK-DECL-012",
    "DeclarativeSchemaLimitError": "PTK-DECL-013",
}


def _load(name: str) -> dict[str, object]:
    value = json.loads((CONTRACTS / name).read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_v1_1_successor_keeps_v1_public_baseline_explicitly_unchanged() -> None:
    v1 = _load("public_api_v1.json")
    successor = _load("public_api_v1_1.json")
    unchanged = successor["unchanged_v1"]

    assert isinstance(unchanged, dict)
    assert successor["predecessor"] == "contracts/public_api_v1.json"
    assert successor["v1_baseline_category_hashes"] == v1["category_hashes"]
    assert unchanged["root_exports"] == v1["root_exports"]
    assert unchanged["root_legacy_compatibility"] == v1["root_legacy_compatibility"]
    assert unchanged["engine_ids"] == v1["engine_ids"]
    assert unchanged["wire_contracts"] == v1["wire_contracts"]
    assert unchanged["stable_runtime_extras"] == v1["extras"]["stable_runtime"]
    assert pytransformkit.__all__ == v1["root_exports"]


def test_v1_1_schema_io_exports_and_signatures_match_runtime() -> None:
    successor = _load("public_api_v1_1.json")
    additions = successor["additions"]

    assert isinstance(additions, dict)
    modules = additions["modules"]
    signatures = additions["signatures"]
    assert isinstance(modules, dict)
    assert isinstance(signatures, dict)

    assert schema_io.__all__ == _SCHEMA_IO_EXPORTS
    assert modules["pytransformkit.schema_io"] == {"exports": _SCHEMA_IO_EXPORTS}

    actual_signatures = {
        f"pytransformkit.schema_io.{name}": str(
            inspect.signature(getattr(schema_io, name))
        )
        for name in _SCHEMA_IO_EXPORTS
    }
    assert signatures == actual_signatures
    assert set(_SCHEMA_IO_EXPORTS).isdisjoint(pytransformkit.__all__)


def test_v1_1_declarative_error_catalogue_is_exact_and_additive() -> None:
    v1 = _load("error_codes_v1.json")
    successor = _load("error_codes_v1_1.json")
    v1_entries = v1["entries"]
    successor_entries = successor["entries"]

    assert isinstance(v1_entries, dict)
    assert isinstance(successor_entries, dict)
    assert successor["predecessor"] == "contracts/error_codes_v1.json"

    for name, entry in v1_entries.items():
        assert successor_entries[name] == entry

    declarative_entries = {
        name: entry
        for name, entry in successor_entries.items()
        if name.startswith("DeclarativeSchema")
    }
    assert set(declarative_entries) == set(_DECLARATIVE_CODES)
    assert {
        name: entry["code"] for name, entry in declarative_entries.items()
    } == _DECLARATIVE_CODES

    runtime_codes = {
        name: str(getattr(errors, name).error_code)
        for name in _DECLARATIVE_CODES
    }
    assert runtime_codes == _DECLARATIVE_CODES
    assert len(set(runtime_codes.values())) == len(runtime_codes)


def test_v1_1_declarative_exception_hierarchy_matches_runtime() -> None:
    successor = _load("public_api_v1_1.json")
    additions = successor["additions"]
    assert isinstance(additions, dict)
    hierarchy = additions["exception_hierarchy"]
    assert isinstance(hierarchy, dict)

    actual = {
        name: getattr(errors, name).__bases__[0].__name__
        for name in _DECLARATIVE_CODES
    }
    assert hierarchy == actual
    assert additions["supporting_values"] == ["DeclarativeErrorContext"]


def test_yaml_extra_is_additive_stable_runtime_capability() -> None:
    v1 = _load("public_api_v1.json")
    successor = _load("public_api_v1_1.json")

    previous = v1["extras"]["stable_runtime"]
    assert successor["unchanged_v1"]["stable_runtime_extras"] == previous
    assert successor["additions"]["stable_runtime_extras"] == ["yaml"]
    assert successor["stable_runtime_extras"] == [*previous, "yaml"]
