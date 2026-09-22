# PyTransformKit

**Define transformations once. Execute them anywhere.**

PyTransformKit is an engine-agnostic Python framework for defining typed, composable data transformations independently from their physical execution engine.

> Status: early pre-1.0 implementation. Public APIs may evolve while the core contracts are being qualified.

## Goals

- Define logical transformations independently from Pandas, Polars, PyArrow, DuckDB, or future engines.
- Keep the Domain model free from engine-specific types.
- Make schema propagation, validation, lineage, observability, and optimization first-class concerns.
- Prove semantic consistency through contract and cross-engine tests.

## Initial roadmap

The first implementation milestone establishes the repository, typed Domain primitives, logical schemas, expressions, transformations, pipelines, and a logical plan before adding the Pandas reference adapter.

## Development status

Repository bootstrap is in progress. The first release line targets `0.1.0a1`.

## License

License selection is pending.
