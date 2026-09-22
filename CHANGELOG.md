# Changelog

All notable changes to PyTransformKit will be documented in this file.

The project follows Semantic Versioning and PEP 440 for pre-release versions.

## [Unreleased]

### Added

- Repository bootstrap.
- Python package skeleton using a `src/` layout.
- Static quality, test, build, and CI configuration.
- Typed UUID-backed Shared Kernel identifiers.
- Immutable Domain `Version` and `Fingerprint` value objects.
- Initial public PyTransformKit error hierarchy and stable Schema error codes.
- Engine-independent logical DataTypes for strings, booleans, integers, floats, decimals, dates, times, timestamps, binary values, and unknown values.
- Immutable `FieldPath`, `Field`, and ordered `Schema` models.
- Schema operations for lookup, selection, drop, rename, append, and replacement.
- Immutable `DatasetMetadata` and lightweight `DatasetStatistics`.
- Portable `DatasetReference` and `LogicalDatasetReference`.
- Logical immutable `Dataset` aggregate with identity-based equality and no physical data payload.
- Unit tests for Shared Kernel, DataTypes, FieldPath, Field, Schema, Dataset metadata/statistics/references, Dataset identity, and Schema errors.
- Architecture tests preventing Domain imports from engine libraries or Infrastructure.
- Engine-independent immutable Expression AST with column references, literals, binary/unary operators, NULL predicates, and logical function calls.
- Public Expression DSL with `col()`, `lit()`, `lower()`, `upper()`, `trim()`, and `concat()`.
- Python operator overloading for comparisons, arithmetic, boolean composition, and unary logical/negation operations.
- Expression static type resolution with nullability propagation and basic numeric promotion.
- Expression dependency extraction for future lineage, projection analysis, and optimization.
- Canonical SHA-256 structural Expression fingerprints.
- Expression error hierarchy with stable `PTK-EXPR-*` error codes.
- Tests covering AST construction, bool-coercion protection, literal inference, functions, dependencies, fingerprints, and non-finite Decimal rejection.

### Changed

### Deprecated

### Removed

### Fixed

### Security
