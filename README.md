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

The repository bootstrap (**LOT-00**) is in place and the Shared Kernel (**LOT-01**) has started with:

- typed UUID-backed domain identifiers;
- immutable `Version` value object;
- immutable `Fingerprint` value object;
- unit tests for the Shared Kernel.

The next implementation lot is **LOT-02 — Type System & Schema Core**.

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
- No hidden engine fallback.
- Optional engines remain optional dependencies.
- Public semantic behavior is test-driven.
- A capability is not `SUPPORTED` until its contract tests pass.

## Documentation

Architecture and functional specifications belong under `docs/specifications/` as they are added to the repository.

## License

License selection is pending and should be made explicitly before a public stable release.
