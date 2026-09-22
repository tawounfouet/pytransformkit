# PyTransformKit

**Define transformations once. Execute them anywhere.**

PyTransformKit is an engine-agnostic Python framework for defining typed, composable data transformations independently from their physical execution engine.

> Status: early pre-1.0 implementation. Public APIs may evolve while the core contracts are being qualified.

## Goals

- Define logical transformations independently from Pandas, Polars, PyArrow, DuckDB, or future engines.
- Keep the Domain model free from engine-specific types.
- Make schema propagation, validation, lineage, observability, and optimization first-class concerns.
- Prove semantic consistency through contract and cross-engine tests.

## Current implementation status

The following implementation lots are now in place:

- **LOT-00 — Repository Bootstrap**
- **LOT-01 — Shared Kernel**
- **LOT-02 — Type System & Schema Core**
- **LOT-03 — Dataset Domain Model**
- **LOT-04 — Expression AST Core**
- **LOT-05 — Transformation Model MVP**
- **LOT-06 — Pipeline & DAG Core**
- **LOT-07 — Engine Runtime Contracts**

The logical data layer now provides:

- engine-independent primitive DataTypes;
- immutable `FieldPath`, `Field`, and ordered `Schema`;
- `DatasetMetadata` and `DatasetStatistics`;
- `DatasetReference` and `LogicalDatasetReference`;
- an immutable logical `Dataset` whose identity is independent from any DataFrame, Table, Relation, or other physical engine object.

The Expression layer now provides a portable immutable AST, public `col/lit` DSL, string functions, static logical typing, NULL-aware nullability propagation, dependency extraction, and canonical structural fingerprints.

The Transformation layer now models projection, row selection, casting, derivation, sorting and deduplication as immutable engine-independent specifications. Output Schemas are resolved statically before any physical execution.

The Pipeline layer now provides an immutable single-input/single-output DAG, explicit dependencies, structural validation, deterministic topological ordering, static Schema propagation and an engine-independent LogicalPlan. The public package now exposes `Pipeline`.

The runtime boundary now defines portable engine capabilities and descriptors, opaque Dataset handles, an EngineAdapter protocol, immutable execution context/results, an explicit EngineRegistry and pre-execution capability compatibility checks. No physical engine is imported by the Core.

The next implementation lot is **LOT-08 — Pandas Reference Adapter**.

The first release line targets `0.1.0a1`.

## Development

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"

ruff check .
ruff format --check .
mypy src/pytransformkit
pytest
python -m build
```

On Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

## Architectural invariants

- No engine-specific types in the Domain.
- A logical Dataset never stores native engine data.
- No hidden engine fallback.
- Optional engines remain optional dependencies.
- Public semantic behavior is test-driven.
- A capability is not `SUPPORTED` until its contract tests pass.

## Documentation

Architecture and functional specifications belong under `docs/specifications/` as they are added to the repository.

## License

License selection is pending and should be made explicitly before a public stable release.
