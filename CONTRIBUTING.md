# Contributing to PyTransformKit

PyTransformKit is built around stable logical semantics first, then engine implementations.

## Development setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

## Required checks

```bash
ruff check .
ruff format --check .
mypy src/pytransformkit
pytest
python -m build
```

## Architecture rules

- Domain code must not import Pandas, Polars, PyArrow, DuckDB, or Infrastructure modules.
- Engine-specific behavior belongs under Infrastructure.
- Do not introduce silent fallbacks between engines.
- Do not add opaque Python callables to the portable transformation DSL.
- Do not expose secrets in errors, logs, lineage, or serialized specifications.
- New user-visible behavior requires tests.
- An engine capability may only be declared `SUPPORTED` after its contract suite passes.

## Pull requests

A feature PR should explain the logical capability, affected engines, tests, compatibility impact, and whether the capability matrix changes.
