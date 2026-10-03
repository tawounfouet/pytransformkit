# AGENTS.md

# PyTransformKit — Repository Instructions for Coding Agents

This file defines the canonical repository-level instructions for AI coding agents and automated contributors working on PyTransformKit.

It applies to the entire repository unless a more specific `AGENTS.md` exists in a subdirectory.

Human-maintained specifications, public contracts, tests, and release evidence remain authoritative over agent assumptions.

## 1. Repository identity

```text
Project: PyTransformKit
Package: pytransformkit
Repository: tawounfouet/pytransformkit
Current stable baseline: 1.2.0
Python support: 3.11 / 3.12 / 3.13 / 3.14
```

PyTransformKit is an engine-agnostic framework for defining typed, composable data transformations independently from physical execution engines.

Canonical model:

```text
TransformationPlan
        ↓
TransformationCompiler
        ↓
LogicalPlan
        ↓
TransformationRuntime
        ↓
explicit EngineAdapter
        ↓
TransformationResult
```

## 2. Non-negotiable architecture invariants

### Domain is engine-independent

The Domain MUST NOT depend on pandas, polars, pyarrow, duckdb, Typer, Rich, or any physical execution technology.

### Logical Dataset contains no native engine data

A logical `Dataset` never stores a Pandas DataFrame, Polars DataFrame, Arrow Table, DuckDB relation, or equivalent.

### TransformationPlan is not workflow orchestration

Do not move scheduling, task queues, workflow retries, run calendars or workflow state into `TransformationPlan`.

### LogicalPlan stays engine-neutral

No SQL strings, Pandas operations, Polars expressions, Arrow compute objects or DuckDB relations in the canonical `LogicalPlan`.

### Engine selection is explicit

No hidden engine fallback.

Unsupported capability MUST fail explicitly.

## 3. Schema authority

`Schema` is the canonical semantic model.

```text
Declarative YAML
      ↓
pytransformkit.schema_io
      ↓
Schema
      ↓
SchemaCodec JSON
```

YAML is a human authoring format. SchemaCodec JSON is the machine wire format.

Do not create a second semantic schema model.

The stable `pytransformkit.schema_io` surface includes:

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

Do not casually rename, move, change signatures, or promote these to package-root exports.

SchemaCodec keeps:

```text
contract = pytransformkit.schema
contract_version = 1
```

## 4. Security invariants

Preserve:

```text
safe YAML parsing
no arbitrary constructors
no implicit includes
no implicit file reads
no URL fetching
no environment expansion
alias amplification protection
closed semantic registries
unknown semantic tags fail closed
no plugin activation during parsing/deserialization
```

Never use `eval`, `exec`, unsafe YAML, or untrusted pickle to deserialize user-controlled content.

## 5. Optional dependencies

The core must remain importable without optional features.

```python
import pytransformkit
```

must not require:

```text
PyYAML
Pandas
Polars
PyArrow
DuckDB
Typer
Rich
```

Optional dependency families remain optional.

## 6. Plugins

Plugin metadata discovery and plugin activation are different operations.

Do not activate plugins implicitly during:

```text
imports
deserialization
schema parsing
help rendering
doctor checks
engine listing
```

Serialized content must never trigger plugin execution.

## 7. Public API and contracts

The package root is curated. Before changing root exports, check compatibility contracts.

Historical contract snapshots under `contracts/` are evidence and MUST NOT be rewritten merely to make CI green.

Important families include:

```text
public_api_v1.json
public_api_v1_1.json
error_codes_v1.json
error_codes_v1_1.json
stable_release_v1.json
stable_release_v1_1.json
```

Correct evolution is additive: preserve historical snapshots and introduce successor evidence when required.

Never fix a compatibility regression by rewriting history.

## 8. Specifications

Primary design documents live under:

```text
docs/specifications/
```

Before implementing a named LOT, read its relevant specification documents and existing tests.

Do not implement from a LOT title alone.

## 9. Developer CLI 1.2

The next planned line is PyTransformKit 1.2 Developer CLI.

Canonical target:

```text
ptk
├── version
├── doctor
├── schema
│   ├── validate
│   ├── inspect
│   ├── format
│   └── convert
├── engines
│   ├── list
│   └── inspect
└── contract
    └── inspect
```

CLI rules:

```text
Typer = routing
Rich = human rendering
CLI services = coordination
PyTransformKit public APIs = semantic authority
```

The CLI is a primary/driving adapter. Domain and core packages MUST NOT depend on it.

Report commands:

```text
version
doctor
schema.validate
schema.inspect
engines.list
engines.inspect
contract.inspect
```

Payload commands:

```text
schema.format
schema.convert
```

Remember:

```text
Reports are rendered.
Payloads are emitted.
```

Canonical YAML remains owned by `schema_io`; canonical wire JSON remains owned by `SchemaCodec`.

## 10. CLI scope exclusions

Do NOT introduce during 1.2:

```text
pytransformkit.yml
ProjectDefinition
ProjectManifest
Profile
Target
project discovery
ptk project
ptk run
ptk compile
ptk plan
ptk build
ptk test
workflow orchestration
scheduling
run history
```

Reserved future command names:

```text
project
run
compile
plan
build
test
```

## 11. CLI packaging

The intended model is:

```bash
pip install pytransformkit
pip install "pytransformkit[yaml]"
pip install "pytransformkit[cli]"
pip install "pytransformkit[cli,yaml]"
```

The console entrypoint should pass through:

```text
pytransformkit.cli.bootstrap:main
```

so absence of optional CLI dependencies can be handled without a raw import failure.

## 12. CLI process errors

Keep framework error identity separate from process exit codes.

Candidate CLI v1 codes:

```text
SUCCESS                       0
GENERAL_ERROR                 1
INVALID_USAGE                 2
INVALID_SCHEMA               10
MISSING_OPTIONAL_DEPENDENCY  11
FILESYSTEM_ERROR             12
UNSUPPORTED_OPERATION        13
INTERNAL_ERROR               70
INTERRUPTED                 130
BROKEN_PIPE                141
```

Do not scatter numeric literals through handlers.

Existing `PTK-*` codes must survive the CLI boundary.

## 13. CLI filesystem rule

```text
Read only what the user explicitly names.
Write only what the user explicitly authorizes.
```

No recursive discovery, no implicit remote loading, no silent overwrite.

For replacement writes prefer:

```text
validate
→ build complete payload
→ temporary sibling
→ flush / close
→ atomic replace
```

Mutable output symlinks fail closed by default.

## 14. Source layout

```text
src/pytransformkit/      package
tests/                   tests
docs/specifications/     specifications
contracts/               machine-readable compatibility evidence
scripts/                 release / verification tooling
```

Preferred dependency direction:

```text
Domain
   ↑
Application / Runtime
   ↑
Adapters
   ↑
CLI / integrations
```

Use public APIs before internals.

If a needed capability has no appropriate public API, identify the architectural gap rather than silently coupling a new feature to private modules.

## 15. Coding style

Repository quality stack:

```text
Ruff
Ruff formatter
mypy
pytest
```

Line length: 88.

Python baseline: 3.11+.

Do not weaken type-checking configuration to make new code pass.

Avoid broad `# type: ignore` suppressions unless the underlying issue is understood and the suppression is narrow.

## 16. Determinism

Public and contract-sensitive behavior must not rely on:

```text
set iteration
unordered registry traversal
random IDs
timestamps
memory addresses
filesystem discovery order
```

Do not casually change canonical fingerprint inputs.

## 17. Error handling

Prefer structured, typed errors over generic exceptions.

Do not use message-string matching where exception types or public error codes exist.

Preserve `PTK-*` identifiers across adapters and interfaces.

## 18. Testing

Tests are part of the feature.

Repository markers include:

```text
unit
architecture
contract
cross_engine
integration
performance
external
slow
```

Run the relevant subset first, then broader regression.

Minimum local quality commands:

```bash
ruff check .
ruff format --check .
mypy src/pytransformkit
pytest
```

For packaging/release-sensitive changes:

```bash
python -m build
python -m twine check dist/*
```

Do not claim full Python compatibility from a single interpreter. Stable qualification covers 3.11–3.14.

Engine behavior changes require conformance/cross-engine evidence.

Serialization changes require contract/golden evidence.

Declarative Schema changes require round-trip and security evidence.

## 19. No false green

Never claim:

```text
all green
CI green
LOT complete
release qualified
stable
```

without actually observing the required tests/jobs.

A skipped required test is not evidence.

A pending/cancelled job is not green.

An agent statement is not evidence.

## 20. LOT-based development

Preferred flow:

```text
inspect baseline
→ read specification
→ focused branch
→ implement
→ add tests
→ targeted qualification
→ broader regression
→ version checkpoint
→ requalify
→ PR
→ required CI green
→ merge
→ main verification
```

Avoid unrelated refactors inside a focused LOT.

Version checkpoints represent real qualification milestones.

Stable release closure is promotion-only.

## 21. Current CLI roadmap

```text
LOT-44  CLI Package Bootstrap            → 1.2.0a1
LOT-45  CLI Foundations                  → 1.2.0a2
LOT-46  ptk version                      → 1.2.0a3
LOT-47  ptk doctor                       → 1.2.0a4
LOT-48  schema validate                  → 1.2.0a5
LOT-49  schema inspect                   → 1.2.0a6
LOT-50  schema format                    → 1.2.0a7
LOT-51  schema convert                   → 1.2.0a8
LOT-52  engines list / inspect           → 1.2.0b1
LOT-53  contract inspect                 → 1.2.0b2
LOT-54  machine output hardening         → 1.2.0b3
LOT-55  CLI public contract freeze       → 1.2.0b4
LOT-56  security / filesystem closure    → 1.2.0rc1
LOT-57  artifact qualification           → 1.2.0rc2
LOT-58  docs / RC closure                → 1.2.0rc3
LOT-59  stable release                   → 1.2.0
```

Do not skip foundational LOTs.

## 22. Documentation accuracy

Do not document a command/API as available if it is only planned.

Use explicit terms such as `planned`, `target`, `candidate`, or `future` for unreleased behavior.

Images are explanatory only and never override code, contracts, specs, or tests.

## 23. Tool-independent instructions

This file is canonical for all coding agents.

Tool-specific overlays such as `CLAUDE.md` must stay thin and must not introduce a parallel architecture.

Authority order:

```text
specifications / contracts / tests
        ↓
AGENTS.md
        ↓
tool-specific overlay
```

## 24. Before editing

Before changing code, inspect:

```text
current branch
current version
relevant package
existing tests
relevant contracts
relevant specification
recent adjacent implementation patterns
```

Do not assume live repository state from conversation history.

Prefer existing protocols, services, registries, errors, serializers, and test helpers when appropriate.

Avoid premature abstraction and reflection-heavy magic.

## 25. Definition of Done

Ordinary feature:

```text
Specified
→ Implemented
→ Tested
→ Qualified
```

Public/release work:

```text
Specified
→ Implemented
→ Tested
→ Contract-qualified
→ Security-qualified
→ Artifact-qualified
→ Published
→ Consumer-validated
```

## 26. Core checklist

Before declaring work finished:

```text
[ ] relevant specification read
[ ] live repo state checked
[ ] Domain/adapter boundaries preserved
[ ] public APIs reused where available
[ ] no hidden fallback introduced
[ ] optional dependencies remain optional
[ ] public contract impact reviewed
[ ] historical snapshots preserved
[ ] tests added/updated
[ ] Ruff green
[ ] Ruff format green
[ ] mypy green
[ ] relevant pytest green
[ ] artifact tests run when packaging changed
[ ] no unobserved CI success claimed
[ ] docs reflect implementation reality
```

## 27. Final rule

```text
Semantics first.
Contracts explicit.
Adapters thin.
Dependencies optional.
Evidence before release.
```

When convenience conflicts with architecture, preserve architecture.

When behavior is ambiguous, fail explicitly.

When implementation speed conflicts with compatibility, preserve the public contract.

When an agent assumption conflicts with executable evidence, trust the evidence.
