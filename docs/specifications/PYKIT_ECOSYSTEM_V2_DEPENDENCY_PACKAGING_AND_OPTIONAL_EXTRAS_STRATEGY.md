# PyKit Ecosystem V2 — Dependency, Packaging and Optional Extras Strategy

> **Status:** NORMATIVE PACKAGING AND DEPENDENCY BASELINE  
> **Architecture generation:** V2  
> **Date:** 2026-09-28  
> **Scope:** PyIngestKit, PyTransformKit, PyWorkflowKit  
> **Compatibility posture:** independently versioned packages with explicit optional integration edges  
> **Depends on:** PYKIT_ECOSYSTEM_V2_ARCHITECTURE_AND_CANONICAL_VOCABULARY.md  
> **Depends on:** PYKIT_ECOSYSTEM_V2_PUBLIC_API_DESIGN_PRINCIPLES.md  
> **Depends on:** PYKIT_ECOSYSTEM_V2_SHARED_CONTRACTS_AND_REFERENCE_MODEL.md  
> **Depends on:** PYKIT_ECOSYSTEM_V2_INTEGRATION_AND_ANTI_CORRUPTION_LAYER_MODEL.md

---

# 1. Purpose

This document converts the PyKit V2 architecture into concrete Python packaging and dependency rules.

It defines:

- package dependency direction;
- core versus optional dependencies;
- optional extras;
- integration extras;
- backend extras;
- plugin discovery;
- entry-point namespaces;
- version ranges;
- package-version independence;
- contract-version compatibility;
- import isolation;
- development dependencies;
- test matrices;
- release compatibility;
- cycle prevention;
- installation profiles.

The governing principle is:

> **Architecture boundaries must be enforceable by the package graph, not merely documented in diagrams.**

---

# 2. Canonical package graph

The allowed sibling dependency graph is:

~~~text
PyWorkflowKit
    ├── optional ─► PyIngestKit
    └── optional ─► PyTransformKit

PyIngestKit
    └── optional ─► PyTransformKit

PyTransformKit
    └── no sibling dependency
~~~

The graph MUST remain acyclic.

---

# 3. Core package independence

Each package MUST install and operate in its core use cases without sibling frameworks.

~~~text
pip install pytransformkit
    does not install pyingestkit
    does not install pyworkflowkit

pip install pyingestkit
    does not install pytransformkit by default
    does not install pyworkflowkit

pip install pyworkflowkit
    does not install pyingestkit
    does not install pytransformkit
~~~

Sibling frameworks become dependencies only through explicit integration extras or application-level composition.

---

# 4. No mandatory ecosystem meta-package

V2 does not require a package such as:

~~~text
pykit
pykit-core
pykit-common
pykit-runtime
pykit-all
~~~

A future convenience meta-package MAY exist, but it MUST NOT become a dependency of the three core frameworks.

---

# 5. No mandatory shared-contract package

Shared contract specifications do not currently require a fourth runtime package.

Therefore V2 does not initially require:

~~~text
pykit-contracts
pykit-types
pykit-common
~~~

Shared semantics remain specification-first.

A shared contracts package may be extracted only after repeated implementation proves stable cross-framework semantics.

---

# 6. Dependency classes

Each project SHOULD distinguish:

~~~text
CORE DEPENDENCIES
OPTIONAL FEATURE DEPENDENCIES
INTEGRATION DEPENDENCIES
DEVELOPMENT DEPENDENCIES
~~~

These classes MUST NOT be mixed indiscriminately.

---

# 7. Core dependencies

A dependency belongs in core only when:

1. ordinary package behavior genuinely requires it;
2. most installations need it;
3. making it optional would create excessive complexity;
4. it does not violate bounded-context independence.

Core dependency sets SHOULD remain small.

---

# 8. Optional feature dependencies

Optional dependencies enable capabilities not required by every installation.

PyTransformKit examples:

~~~text
pandas
polars
pyarrow
duckdb
provider-specific engines
~~~

PyIngestKit examples:

~~~text
Excel parser
Parquet support
S3 client
PostgreSQL driver
provider-specific source/target clients
~~~

PyWorkflowKit examples:

~~~text
PostgreSQL metadata store
OpenTelemetry integration
optional executor dependencies
~~~

---

# 9. Integration dependencies

Integration dependencies are sibling packages required only for an explicit bridge.

Canonical edges are:

~~~text
PyIngestKit → PyTransformKit

PyWorkflowKit → PyIngestKit

PyWorkflowKit → PyTransformKit
~~~

They MUST NOT leak into core dependencies.

---

# 10. Development dependencies

Development dependencies include:

~~~text
pytest
coverage tooling
ruff
mypy
build
twine
documentation tooling
benchmark tooling
release tooling
~~~

They MUST NOT become runtime dependencies unless runtime semantics genuinely require them.

---

# 11. Standard project metadata

Projects SHOULD use standard pyproject.toml project metadata.

Illustrative structure:

~~~toml
[project]
name = "pytransformkit"
version = "..."
requires-python = ">=3.11"
dependencies = []
~~~

User-facing optional features belong in the project's optional dependency metadata.

---

# 12. Build backend

The ecosystem does not require all three projects to use the same PEP 517 build backend.

Hatchling, setuptools, Flit, PDM backend or another standards-compatible backend may be used.

Architecture semantics MUST NOT depend on build-backend-specific behavior.

---

# 13. Python version alignment

The three frameworks SHOULD maintain an overlapping supported Python range whenever practical.

If all three support Python 3.11+, ecosystem composition is straightforward.

If one package raises its minimum Python version, the integration compatibility range must reflect the actual intersection.

---

# 14. No hidden sibling imports

Core modules MUST NOT conditionally import siblings merely because they happen to be installed.

Sibling awareness belongs in explicit integration namespaces.

Rejected architectural pattern:

~~~text
pyingestkit.domain
    tries to import pytransformkit
~~~

even if wrapped in an ImportError handler.

---

# 15. Integration namespace isolation

Recommended structure:

~~~text
pyingestkit/
├── domain/
├── application/
├── runtime/
├── infrastructure/
└── integrations/
    └── pytransformkit/

pyworkflowkit/
├── domain/
├── application/
├── runtime/
├── infrastructure/
└── integrations/
    ├── pyingestkit/
    └── pytransformkit/
~~~

PyTransformKit requires no sibling integration namespace for the canonical dependency direction.

---

# 16. Canonical integration extras

Preferred conceptual extras are:

~~~text
pyingestkit[transform]

pyworkflowkit[ingest]
pyworkflowkit[transform]
~~~

Combined use remains possible:

~~~text
pyworkflowkit[ingest,transform]
~~~

These names SHOULD remain stable once public and mature.

---

# 17. PyIngestKit transform extra

Illustrative metadata:

~~~toml
[project.optional-dependencies]
transform = [
    "pytransformkit>=SUPPORTED_MIN,<SUPPORTED_MAX",
]
~~~

Installing:

~~~text
pip install "pyingestkit[transform]"
~~~

enables the official PyIngestKit → PyTransformKit integration.

It MUST NOT install PyWorkflowKit.

---

# 18. PyWorkflowKit ingest extra

Illustrative metadata:

~~~toml
[project.optional-dependencies]
ingest = [
    "pyingestkit>=SUPPORTED_MIN,<SUPPORTED_MAX",
]
~~~

This enables the official WorkflowKit → IngestKit adapter.

---

# 19. PyWorkflowKit transform extra

Illustrative metadata:

~~~toml
[project.optional-dependencies]
transform = [
    "pytransformkit>=SUPPORTED_MIN,<SUPPORTED_MAX",
]
~~~

This enables the official WorkflowKit → TransformKit adapter.

---

# 20. Combined installation

A full ecosystem application may install all required capabilities explicitly.

Example:

~~~text
pip install "pyworkflowkit[ingest,transform]" "pyingestkit[transform]"
~~~

Application-level pinning may be stricter than published library ranges.

---

# 21. No transitive feature assumption

If WorkflowKit installs IngestKit through its ingest extra, it MUST NOT assume PyTransformKit integration is also available.

Feature availability is explicit.

Installed package presence alone does not imply every optional capability.

---

# 22. Feature detection

Integration preflight SHOULD distinguish:

~~~text
package installed?
supported package version?
required extra dependencies installed?
adapter available?
contract version supported?
provider capability available?
~~~

These are separate checks.

---

# 23. Missing dependency errors

Unavailable optional integrations SHOULD fail with actionable guidance.

Preferred:

~~~text
PyTransformKit integration is unavailable.
Install the optional integration with:

    pip install "pyingestkit[transform]"
~~~

Avoid exposing only an unrelated nested ModuleNotFoundError.

---

# 24. Lazy optional imports

Optional engines, cloud clients, telemetry systems and sibling packages SHOULD be imported only when their integration is activated or used.

Core package import SHOULD remain lightweight.

---

# 25. Package-root import safety

The following imports MUST succeed in minimal supported environments:

~~~python
import pytransformkit
import pyingestkit
import pyworkflowkit
~~~

Optional backends and sibling frameworks MUST NOT be required solely for package-root import.

---

# 26. PyTransformKit backend extras

PyTransformKit SHOULD use engine extras where dependencies are non-core.

Conceptually:

~~~text
pytransformkit[pandas]
pytransformkit[polars]
pytransformkit[arrow]
pytransformkit[duckdb]
~~~

The exact set must track implemented capabilities.

---

# 27. PyIngestKit feature extras

Potential extras may include:

~~~text
pyingestkit[http]
pyingestkit[excel]
pyingestkit[parquet]
pyingestkit[postgres]
pyingestkit[s3]
~~~

Only supported capabilities should receive published extras.

Do not publish aspirational empty extras.

---

# 28. PyWorkflowKit infrastructure extras

Potential extras may include:

~~~text
pyworkflowkit[postgres]
pyworkflowkit[otel]
~~~

Again, extras correspond to implemented stable capabilities.

---

# 29. Convenience all extras

An all extra MAY exist, but SHOULD NOT be the default recommendation.

Large convenience extras increase:

- installation size;
- dependency conflicts;
- supply-chain surface;
- resolver pressure;
- accidental coupling.

Small profile-specific installation is preferred.

---

# 30. Recommended installation profiles

Documentation SHOULD show focused installation paths.

~~~text
Core transformation
    pip install pytransformkit

Polars transformation
    pip install "pytransformkit[polars]"

Ingestion with transformation
    pip install "pyingestkit[transform]"

Workflow with ingestion
    pip install "pyworkflowkit[ingest]"

Workflow with transformation
    pip install "pyworkflowkit[transform]"
~~~

---

# 31. Independent package versions

The packages are independently versioned.

The ecosystem MUST NOT require matching release numbers.

~~~text
PyTransformKit 0.x/1.x
PyIngestKit 2.x
PyWorkflowKit 2.x
~~~

may compose when their declared contracts are compatible.

---

# 32. Compatibility basis

Integration compatibility is determined by both:

~~~text
PACKAGE VERSION RANGE
+
BOUNDARY CONTRACT VERSION
~~~

Equal package versions do not prove compatibility.

Different package versions do not imply incompatibility.

---

# 33. Dependency range principle

Official integration extras SHOULD declare:

- a tested minimum version;
- an explicit upper compatibility boundary.

Avoid unbounded dependency declarations for evolving public contracts.

Avoid exact pins in reusable library metadata unless necessary.

---

# 34. Pre-1.0 provider ranges

A pre-1.0 dependency such as PyTransformKit requires deliberately narrow ranges until compatibility guarantees mature.

Illustrative only:

~~~text
pytransformkit>=0.8,<0.9
~~~

or a broader range only if tests and policy justify it.

The exact bound is release-specific and MUST be evidence-based.

---

# 35. Stable-major ranges

For a stable SemVer-like major line, an integration MAY support a range such as:

~~~text
pyingestkit>=2.1,<3
~~~

only when that major line is actually tested and contract-compatible.

This is a pattern, not a frozen concrete dependency.

---

# 36. Dependency resolution is not compatibility proof

A successful pip resolution proves that declared constraints can coexist.

It does not prove semantic compatibility.

Official sibling integrations therefore require producer-consumer contract tests.

---

# 37. Library ranges versus application lock

Published libraries SHOULD expose supported version ranges.

Applications and reference environments MAY pin exact versions.

Therefore:

~~~text
library metadata
    compatibility range

application lock
    reproducible environment
~~~

serve different purposes.

---

# 38. Development lock files

A project lock file MAY support local development and CI.

It MUST NOT be imposed as the package consumer's dependency resolution contract.

---

# 39. Minimum dependency testing

Declared minimum versions SHOULD be tested periodically.

If the project no longer works with a declared lower bound, either:

- fix compatibility;
- or raise the minimum deliberately.

A fictional lower bound is a packaging bug.

---

# 40. Latest compatible dependency testing

CI SHOULD test relevant latest compatible versions to detect upstream changes.

This is especially important for engines, drivers, cloud SDKs and telemetry libraries.

---

# 41. Layered CI matrix

Use a layered matrix rather than every Cartesian combination.

~~~text
CORE MATRIX
    all supported Python versions

FEATURE MATRIX
    each major optional feature

INTEGRATION MATRIX
    supported sibling ranges

REFERENCE MATRIX
    full three-framework application
~~~

---

# 42. Built wheel testing

Release CI SHOULD test installed artifacts, not only source checkout.

Recommended gate:

~~~text
build wheel
install wheel in clean environment
import package
run package smoke tests
install selected extras
run optional feature smoke tests
~~~

This detects missing package data and undeclared dependencies.

---

# 43. Source distribution testing

If sdist is published, it SHOULD also be installed and smoke-tested.

A valid wheel does not automatically prove a valid source distribution.

---

# 44. Minimal-environment test

Each package needs at least one CI job containing only:

- Python;
- the built package;
- declared core dependencies.

Core import and core smoke tests must pass there.

Development dependencies must not mask undeclared runtime dependencies.

---

# 45. Import graph enforcement

Architecture tests MUST reject forbidden sibling imports.

~~~text
pytransformkit
    MUST NOT import pyingestkit
    MUST NOT import pyworkflowkit

pyingestkit core
    MUST NOT import pyworkflowkit

pyworkflowkit core
    MUST NOT import pyingestkit
    MUST NOT import pytransformkit
~~~

Explicit integration namespaces are allowed exceptions according to the canonical dependency graph.

---

# 46. Optional absence tests

Every optional capability SHOULD be tested with its dependency absent.

Expected behavior:

~~~text
core import succeeds
unrelated features work
optional feature activation fails clearly
~~~

---

# 47. Optional installed tests

Every published extra SHOULD have at least one smoke or conformance test after installation.

A broken optional extra is a release defect.

---

# 48. Extra naming rules

Extras SHOULD be:

- lowercase;
- concise;
- semantic;
- stable after maturity;
- tied to a clear capability.

Preferred:

~~~text
polars
duckdb
postgres
transform
ingest
otel
~~~

Discouraged:

~~~text
extra
advanced
misc
runtime-plus
full2
~~~

---

# 49. Development dependency groups

Contributor dependencies MAY be separated conceptually into:

~~~text
dev
test
lint
typecheck
docs
bench
release
~~~

These are contributor concerns, not necessarily published user-facing extras.

---

# 50. Type-only imports

Static type checking SHOULD NOT accidentally force optional dependencies at runtime.

Projects MAY use type-only imports and postponed annotation evaluation where appropriate.

Public annotations must remain valid under the supported Python and type-checking strategy.

---

# 51. Plugin definition

A plugin is an independently installable extension implementing a documented public extension point.

Examples:

~~~text
PyTransformKit engine adapter
PyIngestKit source connector
PyIngestKit target connector
PyWorkflowKit executor
telemetry exporter
reference resolver
~~~

A plugin is distinct from code already shipped in the host package behind an extra.

---

# 52. Built-in optional feature versus plugin

~~~text
BUILT-IN OPTIONAL FEATURE
    code ships in host distribution
    dependency enabled by extra

PLUGIN
    code ships in another distribution
    implements public extension contract
~~~

Documentation MUST distinguish these models.

---

# 53. Plugin entry-point namespaces

Potential entry-point groups include:

~~~text
pytransformkit.engines
pytransformkit.readers
pytransformkit.writers

pyingestkit.sources
pyingestkit.targets
pyingestkit.artifact_stores

pyworkflowkit.executors
pyworkflowkit.metadata_stores
~~~

Only stable real extension points should receive public entry-point groups.

---

# 54. No universal plugin bucket

Avoid a single catch-all:

~~~text
pykit.plugins
~~~

for unrelated capabilities.

Domain-specific entry-point groups preserve ownership and capability meaning.

---

# 55. Discovery versus activation

Plugin lifecycle is:

~~~text
installed distribution
    ↓
metadata discovery
    ↓
compatibility validation
    ↓
explicit activation
~~~

Discovery MUST NOT automatically imply trust or runtime activation.

---

# 56. No import-time plugin activation

Importing a host package MUST NOT automatically:

- scan and import every plugin;
- mutate a process-global registry;
- start plugin threads;
- open network connections.

Activation belongs to explicit runtime composition.

---

# 57. Plugin compatibility

A plugin SHOULD declare enough information to validate:

~~~text
host package range
extension-point compatibility
plugin version
capabilities
optional dependencies
~~~

Installed does not mean compatible.

Compatible does not mean activated.

---

# 58. Plugin dependency direction

A plugin depends on its host contract.

The host MUST NOT depend on every plugin.

~~~text
third-party extension
    → host package
~~~

never the reverse.

---

# 59. Official adapters

Official sibling adapters SHOULD initially live inside the consuming project when practical.

This keeps:

- installation simple;
- release ownership clear;
- fewer distributions;
- fewer version joins.

Extraction into a separate package is justified only by demonstrated operational need.

---

# 60. Adapter extraction criteria

An official integration MAY become its own distribution when:

1. dependency weight is substantial;
2. release cadence differs materially;
3. adapter API is independently stable;
4. dependency resolution becomes difficult;
5. extraction does not create cycles;
6. maintaining it inside the consumer package is measurably harmful.

---

# 61. Top-level import names

Distribution and import names SHOULD remain predictable.

Preferred:

~~~text
distribution: pytransformkit
import:       pytransformkit
~~~

The ecosystem does not require a shared namespace package.

Independent top-level imports preserve semantic ownership.

---

# 62. No utility package by reflex

Shared third-party dependencies or small duplicated helpers do not justify:

~~~text
pykit-utils
pykit-common
pykit-base
~~~

Small duplication is preferable to premature shared semantic coupling.

---

# 63. Runtime dependency restraint

Each runtime dependency increases:

- supply-chain surface;
- vulnerability exposure;
- installation size;
- resolver complexity;
- upgrade pressure.

Heavy engine, cloud and telemetry dependencies SHOULD remain optional when possible.

---

# 64. Binary dependency caution

Dependencies requiring native binaries are particularly expensive operationally.

They SHOULD remain optional unless indispensable to core semantics.

This applies especially to analytical engines and database clients.

---

# 65. Environment markers

Environment markers MAY represent real Python/platform compatibility.

They SHOULD NOT be abused to encode hidden feature semantics that belong in explicit extras.

---

# 66. Release independence

A release of one framework does not require simultaneous sibling releases.

A sibling release is necessary only when:

- compatibility ranges change;
- an integration changes;
- a shared boundary contract changes;
- support for a provider version changes.

Independent cadence is a deliberate architecture property.

---

# 67. Compatibility manifest

Stable packages SHOULD eventually publish a compatibility manifest or equivalent generated metadata.

Conceptually:

~~~text
package
package_version
supported Python versions

integrations:
    provider package range
    supported contract versions
    capabilities
~~~

Exact representation belongs to implementation/release specifications.

---

# 68. Machine-readable compatibility example

Conceptually:

~~~yaml
package: pyworkflowkit
version: 2.1.0
integrations:
  pyingestkit:
    package: ">=2.0,<3"
    contracts:
      ingestion_execution_reference: [1]
  pytransformkit:
    package: ">=0.9,<1.1"
    contracts:
      transformation_execution_reference: [1]
~~~

This is illustrative, not a frozen current range.

---

# 69. Historical wire compatibility

Python package compatibility and wire-contract compatibility differ.

Historical persisted references, manifests and queue messages may need to remain readable after the original sibling package is gone.

Readers SHOULD declare which historical contract versions they support.

---

# 70. Upgrade direction

When a provider contract changes:

~~~text
provider
    ↓ publishes new contract/version
consumer integration
    ↓ adapts and tests
higher-level consumers
    ↓ adapt if needed
~~~

The acyclic package graph makes upgrade reasoning tractable.

---

# 71. Breaking integration change

A breaking provider contract change SHOULD include:

- a new contract version;
- migration documentation;
- updated package compatibility ranges;
- new golden fixtures;
- updated consumer conformance tests.

Silent semantic reinterpretation is prohibited.

---

# 72. No auto-install at runtime

No PyKit framework may invoke pip or another package manager automatically to satisfy a missing optional dependency.

The runtime should report what is missing and how the environment can be configured.

Environment mutation belongs to users and deployment tooling.

---

# 73. No registry lookup at import time

Package import MUST NOT contact PyPI, GitHub or another external package registry to determine compatibility.

Installed metadata and local contract information are sufficient for runtime preflight.

---

# 74. Installed metadata inspection

Integration preflight MAY inspect installed package metadata for diagnostics and compatibility checks.

This belongs to integration/runtime infrastructure, not the domain model.

---

# 75. Package version is not capability

A package version does not alone prove that a feature is usable.

A capability may additionally require:

~~~text
optional dependency
adapter registration
provider capability
contract support
runtime configuration
credential provider
~~~

Capability checks remain explicit.

---

# 76. Circular extras are forbidden

Extras MUST NOT create hidden cycles.

Rejected:

~~~text
pyingestkit[transform]
    → pytransformkit[some-integration]
        → pyingestkit
~~~

The canonical dependency direction remains binding even inside extras.

---

# 77. Plugin cycles are also forbidden

Third-party plugins can create dependency cycles too.

Plugin graphs should be reviewed for the same acyclicity guarantees as official packages.

---

# 78. Core-only profiles

CI SHOULD maintain these minimum profiles:

~~~text
PROFILE A
    PyTransformKit core only

PROFILE B
    PyIngestKit core only

PROFILE C
    PyWorkflowKit core only
~~~

Each must pass without sibling frameworks.

---

# 79. Integration profiles

CI SHOULD also maintain:

~~~text
PROFILE D
    PyIngestKit + PyTransformKit

PROFILE E
    PyWorkflowKit + PyIngestKit

PROFILE F
    PyWorkflowKit + PyTransformKit

PROFILE G
    full three-framework reference application
~~~

These profiles verify the actual package graph.

---

# 80. Reference application lock

The end-to-end reference application MAY pin exact tested versions.

That lock belongs to the application.

It MUST NOT be copied into reusable library dependency metadata as exact pins without reason.

---

# 81. Editable local development

Maintainers MAY use editable installs or a workspace manager for local ecosystem development.

CI must still test built distributions so local path relationships do not hide packaging defects.

---

# 82. Monorepo neutrality

The ecosystem may remain multi-repository.

If a monorepo or workspace is introduced later, published distributions and dependency boundaries MUST remain independent.

Repository topology does not redefine package ownership.

---

# 83. Release-candidate integration tests

Before stable releases that affect integrations, release candidates SHOULD be tested against supported sibling versions.

Possible mechanisms include:

- built wheel artifacts;
- temporary indexes;
- release-candidate tags;
- explicit constraints.

The objective is pre-publication compatibility evidence.

---

# 84. Packaging error categories

Useful setup/integration errors include:

~~~text
OPTIONAL_DEPENDENCY_MISSING
UNSUPPORTED_PACKAGE_VERSION
UNSUPPORTED_CONTRACT_VERSION
PLUGIN_INCOMPATIBLE
PLUGIN_ACTIVATION_FAILED
ENTRY_POINT_INVALID
DEPENDENCY_CYCLE_DETECTED
CAPABILITY_NOT_INSTALLED
~~~

They belong under the owning framework's error hierarchy.

---

# 85. Documentation synchronization

Every public extra, plugin entry-point group and supported sibling integration MUST be documented.

Release CI SHOULD verify metadata/documentation drift where practical.

---

# 86. Release notes

Release notes SHOULD explicitly call out:

- new extras;
- removed extras;
- changed minimum dependencies;
- changed compatibility upper bounds;
- Python support changes;
- new plugin entry points;
- sibling integration changes;
- wire-contract changes.

Dependency metadata is part of the public user experience.

---

# 87. Security updates

Security fixes may justify raising a dependency minimum quickly.

Metadata, compatibility tests and release notes MUST then move together.

Security requirements can override convenience, but semantic compatibility should still be tested.

---

# 88. Supply-chain restraint

Official extras SHOULD install only what their advertised capability requires.

Avoid broad dependency bundles when smaller focused clients are sufficient.

This keeps deployments lean and auditable.

---

# 89. License review

New runtime dependencies SHOULD undergo appropriate license review before adoption.

Packaging convenience does not override redistribution or usage constraints.

---

# 90. Import-time performance

Core package import SHOULD remain lightweight.

Avoid eager import of:

~~~text
DataFrame engines
database drivers
cloud SDKs
telemetry stacks
sibling frameworks
plugin implementations
~~~

This benefits CLI startup, notebooks, tests and serverless environments.

---

# 91. Packaging architecture review

Every new runtime dependency MUST answer:

1. Is it core, feature, integration or development?
2. Which bounded context needs it?
3. Can it remain optional?
4. Does it add a sibling dependency?
5. Does it introduce a cycle?
6. Which extra owns it?
7. Which versions are supported?
8. Which contract version is required?
9. Does package-root import require it?
10. Is missing-dependency failure clear?
11. Is the claimed range tested?
12. What supply-chain or binary weight does it add?

If these questions cannot be answered, the dependency is not architecture-ready.

---

# 92. Packaging architecture tests

Automated checks SHOULD cover:

~~~text
forbidden sibling imports
undeclared runtime imports
minimal core import
optional absence behavior
optional installed behavior
extra smoke tests
wheel contents
sdist contents when published
entry-point metadata
plugin discovery without activation
package metadata correctness
~~~

---

# 93. Static dependency graph

CI SHOULD inspect or generate module/package dependency graphs.

Forbidden edges and cycles should fail the architecture gate.

The dependency architecture should be executable as a test.

---

# 94. Runtime dependency graph

Dynamic imports can bypass static checks.

Integration activation tests SHOULD therefore exercise runtime import paths as well.

Static and runtime dependency verification complement each other.

---

# 95. Integration compatibility tests

Consumer packages SHOULD own tests proving support for provider public contracts.

Examples:

~~~text
PyTransformKit integration
    consumes DatasetVersionReference v1

PyWorkflowKit integration
    consumes TransformationExecutionReference v1
~~~

Provider private implementation must not appear in these tests.

---

# 96. Golden contract fixtures

Stable serialized boundary fixtures SHOULD be tested across supported versions.

Fixtures SHOULD cover:

- required fields;
- contract version;
- namespace;
- identity;
- optional-field tolerance;
- redaction.

---

# 97. Plugin tests

Stable plugin interfaces SHOULD test:

~~~text
metadata discovery
compatibility rejection
explicit activation
duplicate registration
lifecycle
shutdown
error propagation
no import-time side effects
~~~

---

# 98. Full packaging conformance gate

Before stable ecosystem release, the following SHOULD be green:

~~~text
Core import isolation
Forbidden dependency graph
Supported Python versions
Minimum dependencies
Latest compatible dependencies
Optional extras
Sibling integrations
Plugin discovery and activation
Wheel install
Sdist install if published
Golden contracts
Reference application
~~~

---

# 99. Human-readable compatibility table

Documentation SHOULD eventually expose:

| Consumer | Provider | Dependency mode | Compatibility basis |
|---|---|---|---|
| PyIngestKit | PyTransformKit | optional extra | package range + contract versions |
| PyWorkflowKit | PyIngestKit | optional extra | package range + contract versions |
| PyWorkflowKit | PyTransformKit | optional extra | package range + contract versions |

Actual version values remain release-specific.

---

# 100. Acceptance criteria

This strategy is implemented correctly when:

1. all three core distributions install independently;
2. PyTransformKit has no sibling dependency;
3. PyIngestKit reaches PyTransformKit only through explicit optional integration;
4. PyWorkflowKit reaches siblings only through explicit optional integrations;
5. no package dependency cycle exists;
6. package-root imports do not require optional capabilities;
7. missing optional dependencies fail with clear guidance;
8. heavy engines and provider SDKs remain optional where possible;
9. integration extras have smoke/conformance tests;
10. package versions remain independent;
11. compatibility uses tested package ranges and contract versions;
12. reusable libraries publish ranges rather than application lock pins;
13. minimum and latest dependency profiles are tested;
14. built wheels are tested in clean environments;
15. plugin discovery remains separate from activation;
16. import does not auto-register plugins;
17. libraries do not auto-install packages;
18. architecture tests detect forbidden imports and cycles;
19. a full three-framework reference profile is tested;
20. package metadata and documentation remain synchronized.

---

# 101. Normative invariants

### PKG-INV-01 — The package graph mirrors the architecture graph

Dependencies never contradict bounded-context direction.

### PKG-INV-02 — Core packages are independently installable

Sibling frameworks are optional.

### PKG-INV-03 — PyTransformKit has no sibling dependency

It remains the lowest-level framework in the canonical integration graph.

### PKG-INV-04 — Integration dependencies are explicit extras

Cross-framework composition is never hidden in core requirements.

### PKG-INV-05 — Optional means import-optional

Missing optional dependencies do not break unrelated package imports.

### PKG-INV-06 — Release numbers are independent

Compatibility is not inferred from equal versions.

### PKG-INV-07 — Package and contract compatibility are distinct

Both must be declared and tested.

### PKG-INV-08 — Plugins are discovered before activation

Installation does not imply activation or trust.

### PKG-INV-09 — Import has no plugin side effects

Package import does not mutate global registries through plugin activation.

### PKG-INV-10 — Published ranges are tested claims

Version constraints must reflect conformance evidence.

### PKG-INV-11 — Development tooling stays out of runtime dependencies

Contributor convenience does not inflate consumer environments.

### PKG-INV-12 — Libraries do not mutate the environment

Missing packages are reported, not installed automatically.

---

# 102. Canonical packaging model

~~~text
                           APPLICATION
                               │
             ┌─────────────────┼─────────────────┐
             │                 │                 │
             ▼                 ▼                 ▼
      PyWorkflowKit       PyIngestKit      PyTransformKit
           core               core               core
             │                 │
             │                 └──[transform]──────────► PyTransformKit
             │
             ├──[ingest]──────────────────► PyIngestKit
             │
             └──[transform]────────────────► PyTransformKit

Package-local optional capabilities:

PyTransformKit[pandas|polars|arrow|duckdb|...]
PyIngestKit[http|excel|postgres|s3|...]
PyWorkflowKit[postgres|otel|...]

Third-party plugins
    ↓
depend on documented host extension points
    ↓
never become host-package dependencies
~~~

No cycle is allowed.

---

# 103. Final architecture statement

The PyKit ecosystem should compose through Python packaging exactly as it composes conceptually.

The desired model is:

~~~text
small core
+
explicit optional capabilities
+
explicit sibling integrations
+
independent releases
+
tested compatibility contracts
~~~

not:

~~~text
one giant environment
+
implicit sibling imports
+
matching version numbers
+
hidden plugin activation
+
dependency cycles
~~~

The central rule is:

> **If a capability is optional in the architecture, it must also be optional in installation, import and runtime activation.**

This specification is the baseline for:

~~~text
PYKIT_ECOSYSTEM_V2_SERIALIZATION_AND_WIRE_CONTRACTS.md
PYKIT_ECOSYSTEM_V2_ARCHITECTURE_CONFORMANCE_AND_TEST_STRATEGY.md
PYKIT_ECOSYSTEM_V2_SECURITY_AND_TRUST_BOUNDARIES.md
PYKIT_ECOSYSTEM_V2_REFERENCE_APPLICATION_SPEC.md
PYKIT_ECOSYSTEM_V2_RELEASE_COMPATIBILITY_AND_VERSIONING_POLICY.md
~~~
