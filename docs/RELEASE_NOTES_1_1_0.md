# PyTransformKit 1.1.0 Release Notes

PyTransformKit `1.1.0` is the stable Declarative Schema release.

It promotes the fully qualified `1.1.0rc2` line without introducing new
runtime behavior. The 1.0 public, wire, plugin and compatibility baselines remain
preserved while 1.1 adds a stable human-authoring layer for canonical
`Schema` values.

## Stable 1.1 addition

The stable public namespace is:

```python
pytransformkit.schema_io
```

with exactly eight helpers:

```text
load_schema
loads_schema
load_schemas
loads_schemas
dump_schema
dumps_schema
dump_schemas
dumps_schemas
```

Declarative YAML is installed through the optional runtime extra:

```bash
pip install "pytransformkit[yaml]"
```

PyYAML is not a mandatory core dependency.

## Semantic authority

The contract remains:

```text
Declarative YAML
      ↓
 hardened parser
      ↓
declarative definitions
      ↓
semantic validator
      ↓
compiler
      ↓
canonical Schema
```

`Schema` remains the semantic authority. YAML is an authoring format, not a
second runtime model.

## Wire compatibility

The existing machine wire contract is unchanged:

```text
SchemaCodec.contract         = pytransformkit.schema
SchemaCodec.contract_version = 1
```

The historical JSON golden fixtures and V1 wire identities are preserved.

## Stable declarative errors

The public declarative exception family is frozen under:

```text
PTK-DECL-000 → PTK-DECL-013
```

The 53 historical V1 error identities remain unchanged. The 1.1 successor
catalogue contains 67 stable public errors in total.

## Security boundary

The stable parser rejects or prevents:

- unsafe Python/object tags;
- custom YAML tags;
- anchors and aliases;
- merge keys;
- duplicate mapping keys;
- multi-document streams;
- non-finite values;
- resource-limit violations;
- environment interpolation;
- implicit filesystem includes;
- network access;
- plugin or execution-engine activation.

## Built-artifact qualification

The stable release reruns the complete repository qualification and the
Declarative Schema artifact matrix on Python 3.11, 3.12, 3.13 and 3.14.

Qualified artifact scenarios include:

```text
wheel core-only
wheel + yaml
sdist core-only
sdist + yaml
```

Core-only installations prove that `schema_io` remains importable and that YAML
operations fail explicitly with `PTK-DECL-010` when PyYAML is absent.

## Documentation

The stable documentation set includes:

- `41_PYTRANSFORMKIT_DECLARATIVE_SCHEMA_GETTING_STARTED.md`;
- `42_PYTRANSFORMKIT_DECLARATIVE_SCHEMA_REFERENCE_EXAMPLES.md`;
- executable examples in `scripts/guides/declarative_schema.py`.

The examples are executed from an installed wheel in CI.

## Compatibility evidence

The 1.1 stable line is frozen by:

```text
contracts/public_api_v1.json
contracts/public_api_v1_1.json
contracts/error_codes_v1.json
contracts/error_codes_v1_1.json
contracts/consumer_compatibility_v1.json
contracts/release_qualification_v1.json
contracts/stable_release_v1.json
contracts/stable_release_v1_1.json
```

## Intended release tag

```text
v1.1.0
```

The repository's `publish-pypi.yml` workflow is configured to build and
publish distributions through PyPI Trusted Publishing when a matching GitHub
Release is published.
