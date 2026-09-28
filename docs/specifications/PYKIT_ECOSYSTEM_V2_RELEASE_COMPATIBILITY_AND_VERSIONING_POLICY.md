# PyKit Ecosystem V2 - Release, Compatibility and Versioning Policy

> **Status:** NORMATIVE RELEASE AND COMPATIBILITY BASELINE
> **Architecture generation:** V2
> **Date:** 2026-09-28
> **Scope:** PyTransformKit, PyIngestKit, PyWorkflowKit
> **Release posture:** independent package releases with explicit compatibility contracts

## 1. Purpose

This document defines how the PyKit V2 ecosystem versions, releases and evolves its public surfaces.

It governs package versions, public API compatibility, wire-contract compatibility, plugin compatibility, sibling integrations, release candidates, deprecation, migration, security releases and release evidence.

> **Compatibility is a contract backed by evidence, not an assumption inferred from similar version numbers.**

## 2. Independent package versioning

The three distributions are versioned independently.

~~~text
PyTransformKit
    pre-1.0 evolution
    -> 1.0.0 stable

PyIngestKit
    1.x legacy
    -> 2.0.0 V2

PyWorkflowKit
    1.x legacy
    -> 2.0.0 V2
~~~

Matching package versions are not required for compatibility.

## 3. No ecosystem lockstep

The ecosystem MUST NOT require simultaneous releases merely to align version numbers.

Each framework releases according to its own API, contracts, fixes, features, security posture and integration support.

## 4. Semantic versioning baseline

Stable package lines SHOULD follow MAJOR.MINOR.PATCH semantics.

~~~text
MAJOR
    incompatible change to a stable public contract

MINOR
    backward-compatible public capability

PATCH
    backward-compatible bug, security or quality fix
~~~

Pre-release identifiers MAY use alpha, beta and release-candidate stages.

## 5. Public compatibility surface

A stable compatibility surface may include:

- package-root exports;
- public classes and functions;
- constructor and method signatures;
- Protocol members;
- exception hierarchy;
- enum values;
- CLI contracts;
- optional-extra names;
- plugin entry-point groups;
- wire contracts;
- event contracts;
- diagnostic codes;
- metric contracts;
- manifests and references;
- persisted-state semantics;
- official integration behavior.

A breaking change to a declared stable surface is a compatibility event.

## 6. Private implementation

Private helpers, internal graph storage, private persistence schemas, optimizer internals and caches are not public compatibility surfaces unless documentation explicitly promotes them.

Private implementation may evolve freely while public semantics remain stable.

## 7. Stability levels

Public surfaces SHOULD use explicit maturity levels:

~~~text
EXPERIMENTAL
PROVISIONAL
STABLE
DEPRECATED
REMOVED
~~~

Experimental and provisional surfaces receive weaker compatibility guarantees than stable surfaces.

## 8. Stable means governed

STABLE means the semantics are documented, conformance-tested and subject to compatibility policy.

It does not mean frozen forever.

Ordinary incompatible change to a stable surface requires a MAJOR release.

## 9. PyTransformKit pre-1.0 posture

Before 1.0.0, PyTransformKit may make deliberate breaking changes while the V2 ecosystem vocabulary is incorporated.

As 1.0 approaches, compatibility discipline MUST increase.

Preferred progression:

~~~text
alpha -> beta -> release candidate -> 1.0.0
~~~

## 10. PyTransformKit 1.0 freeze

PyTransformKit 1.0.0 SHOULD freeze at least:

- package-root exports;
- core domain vocabulary;
- TransformationPlan authoring surface;
- Dataset, schema and expression contracts;
- runtime execution and result contracts;
- stable engine-adapter extension points;
- stable reference and wire contracts;
- public error categories;
- stable optional-extra names.

Any intentionally provisional surface MUST remain clearly marked rather than becoming stable accidentally.

## 11. PyIngestKit 2.0 posture

PyIngestKit 2.0.0 is a clean-slate architecture line.

Version 1.x is historical evidence, not a source-level compatibility constraint on V2.

The migration path SHOULD be documented, but V2 is not required to preserve V1 architectural mistakes.

## 12. PyWorkflowKit 2.0 posture

PyWorkflowKit 2.0.0 is likewise a clean-slate architecture line.

V2 state, retry, recovery and integration semantics take precedence over source-level backward compatibility with 1.x.

## 13. Package version is not wire version

~~~text
package_version != contract_version
~~~

A package may release several minor or patch versions while continuing to use the same stable wire contract version.

## 14. Package version is not event version

Event schemas evolve independently from package versions.

A patch release does not imply a new EventVersion.

## 15. Package version is not plugin protocol version

Plugin and extension-point protocols may also have their own compatibility versions.

A plugin must declare host/package and protocol compatibility according to the relevant extension contract.

## 16. Compatibility dimensions

Compatibility SHOULD be evaluated separately for:

~~~text
PYTHON API
WIRE CONTRACTS
PLUGIN PROTOCOLS
PACKAGE DEPENDENCY RANGES
CLI CONTRACTS
CONFIGURATION
PERSISTED STATE
EVENTS AND METRICS
REFERENCE APPLICATION
~~~

A release may be compatible in one dimension and incompatible in another.

## 17. Consumer-provider compatibility

Official sibling integrations MUST declare both provider package ranges and supported contract versions.

Conceptually:

~~~text
PyWorkflowKit consumer
    supports PyTransformKit package range X
    supports TransformationExecutionReference v1
~~~

The exact values are release-specific.

## 18. Compatibility matrix

Each stable consumer SHOULD maintain a tested compatibility matrix for official sibling integrations.

| Consumer | Provider | Package range | Contract versions |
|---|---|---|---|
| PyIngestKit 2.x | PyTransformKit | tested range | dataset/transformation refs |
| PyWorkflowKit 2.x | PyIngestKit | tested range | ingestion refs |
| PyWorkflowKit 2.x | PyTransformKit | tested range | transformation refs |

## 19. Dependency range evidence

The minimum supported dependency version and the latest compatible version are tested claims.

CI SHOULD test both edges of the declared range.

An installable combination is not automatically a supported combination.

## 20. Upper compatibility bounds

Official integration dependencies SHOULD have explicit upper compatibility boundaries when major or pre-1.0 evolution may break contracts.

For a stable major line, a range such as >=1.0,<2 is appropriate only when conformance evidence supports it.

## 21. No compatibility by version coincidence

The following reasoning is invalid:

~~~text
PyIngestKit 2.2
PyWorkflowKit 2.2
therefore compatible
~~~

Compatibility is established only by declared ranges, contract versions and tests.

## 22. Backward compatibility

A release is backward compatible when existing users of declared stable public contracts can upgrade without changing their code or persisted contracts, subject to documented dependency constraints.

Compatibility promises apply only to stable surfaces.

## 23. Forward compatibility

Old consumers MAY tolerate newer producers when wire contracts permit additive optional fields and the package range includes the producer.

Unknown required or safety-sensitive semantics MUST fail closed.

## 24. Wire reader and writer policy

A package MAY support:

~~~text
read:  v1, v2
write: v2
~~~

Historical read support may outlive historical write support.

Lossy downgrade MUST fail explicitly.

## 25. Historical state compatibility

Workflow state, manifests, lineage records and references may outlive the release that created them.

Stateful packages MUST define supported historical read versions, migrations and unsupported-old-state behavior.

## 26. Migration policy

Breaking releases SHOULD provide migration guidance for affected public surfaces.

Migration may cover API, configuration, wire contracts, persisted state, database schema, plugins or CLI usage.

Not every migration must be automatic, but incompatibility MUST be documented.

## 27. Deprecation policy

For stable APIs, the ordinary path is:

~~~text
introduce replacement
    -> mark deprecated
    -> document migration
    -> retain for a reasonable window
    -> remove in next major release
~~~

Deprecation is not removal.

## 28. Deprecation metadata

A deprecated surface SHOULD document:

- deprecated since;
- replacement;
- migration notes;
- planned removal version or major-line boundary.

## 29. Pre-1.0 deprecation

Pre-1.0 projects may use shorter deprecation windows.

Once release-candidate qualification begins, unnecessary API churn SHOULD stop.

## 30. Breaking change examples

Breaking changes include:

- removing a stable root export;
- changing required parameter semantics;
- changing a stable exception category;
- removing or repurposing a stable enum value;
- changing required wire-field meaning;
- incompatibly changing a plugin protocol;
- renaming a stable optional extra;
- incompatibly changing persisted-state semantics;
- breaking a stable machine-readable CLI contract.

## 31. Backward-compatible additions

Normally compatible additions include:

- new optional parameters with safe defaults;
- new public helpers;
- new optional wire fields;
- new event types;
- new metrics;
- new optional extras;
- new diagnostic codes;
- semantic-preserving performance improvements.

Each still requires tests and documentation.

## 32. Bug fix versus contract change

Correcting behavior that contradicted the documented stable contract is normally a bug fix.

Changing the documented contract itself is a compatibility event.

## 33. Security exceptions

Security hardening MAY intentionally reject previously accepted unsafe inputs.

Such changes MUST be documented, scoped and accompanied by remediation guidance.

Unsafe behavior is not preserved solely for backward compatibility.

## 34. Release channels

Recommended maturity semantics:

~~~text
alpha
    active architecture and API evolution

beta
    broader validation with mostly formed public surface

release candidate
    intended stable contract

stable
    compatibility guarantees active
~~~

## 35. Release candidate contract

After rc1, public API and wire-contract churn SHOULD be minimized.

Release candidates SHOULD use release-grade package metadata and undergo the same artifact qualification path expected for stable publication.

## 36. RC correction

If a release candidate requires a breaking correction, a new RC is acceptable.

The full qualification matrix MUST run again.

## 37. Stable release qualification

A stable release SHOULD require green:

~~~text
public API freeze tests
architecture conformance
wire golden fixtures
migration tests
supported Python matrix
minimum dependency profile
latest compatible dependency profile
sibling integration matrix
Customer 360 reference application
wheel installation tests
sdist tests when published
security checks
documentation smoke tests
~~~

## 38. Built artifacts are the release unit

The exact wheel or source distribution intended for publication MUST be qualified.

Source-tree-only success is insufficient.

Release automation SHOULD retain artifact hashes.

## 39. Release evidence

A stable release SHOULD be able to report:

~~~text
package/version
commit
artifact hashes
Python versions
dependency ranges tested
public API baseline
wire versions
integration matrix
reference scenarios
known limitations
~~~

## 40. Compatibility freeze snapshots

Stable releases SHOULD maintain snapshots for intentionally stable surfaces such as exports, signatures, exception hierarchy, enums, schemas, wire fixtures, entry-point groups, extras names and stable CLI structure.

Snapshots detect drift but do not replace semantic tests.

## 41. Release notes

Release notes SHOULD classify user-visible changes using categories such as Added, Changed, Deprecated, Removed, Fixed, Security, Compatibility and Migration.

Integration-range changes MUST be called out explicitly.

## 42. Python support changes

Raising the minimum Python version is a public compatibility change and MUST be documented.

## 43. Dependency-floor changes

Raising third-party dependency minimums affects installation compatibility even when the Python API does not change.

Such changes belong in release notes.

## 44. Optional-extra compatibility

Stable extra names are part of the public installation API.

Renaming or removing transform, ingest, polars, postgres or another stable extra is a compatibility event.

## 45. Plugin compatibility

Stable entry-point groups and Protocols are extension contracts.

Incompatible changes require deliberate protocol evolution, migration guidance and compatibility-range updates.

## 46. CLI and configuration compatibility

If declared stable, command names, option names, exit-code semantics, machine-readable CLI output and configuration keys become public contracts.

Human formatting may remain flexible unless explicitly frozen.

## 47. Metric, event and diagnostic compatibility

Stable metric names, units and label semantics MUST NOT be repurposed.

Persisted/external event changes require EventVersion discipline.

Stable error and diagnostic codes used by automation MUST NOT change meaning silently.

## 48. Exception compatibility

Stable public exception classes and categories are part of the Python API.

Provider-specific internal exceptions may evolve as long as cross-framework failure semantics remain stable.

## 49. Database and persisted-state migrations

Private database schemas may evolve internally, but migration tooling SHOULD own those changes.

If users are instructed to query or manage a schema directly, it may become a de facto public surface.

Upgrade and rollback compatibility are separate properties and MUST be documented when migrations prevent downgrade.

## 50. Reference application as compatibility probe

Customer 360 SHOULD execute against selected supported sibling combinations.

At minimum, the matrix SHOULD include the consumer minimum supported provider, latest supported provider and current development pairing where practical.

## 51. Historical fixtures

Stable wire and persisted-state fixtures from significant releases SHOULD be retained for migration and regression testing.

Examples include 1.0.0 and 2.0.0 baseline references, manifests and workflow-state fixtures.

## 52. Release tags

Recommended repository tags are:

~~~text
v1.0.0
v1.1.0
v2.0.0
v1.0.0rc1
~~~

A published artifact MUST map back to an identifiable commit.

## 53. Immutable publication

Published package artifacts SHOULD be immutable by version.

If a release contains a defect, publish a new version rather than replacing bytes under the same version.

## 54. Yank and emergency release policy

A severely defective version MAY be yanked while remaining historically identifiable.

Emergency patch releases may be expedited, but critical conformance and packaging gates still apply.

## 55. Maintenance lines

Projects MAY maintain older stable lines for security or critical fixes.

Support periods SHOULD be explicit rather than implied indefinitely.

## 56. End of support

An end-of-support announcement SHOULD identify the final supported version, migration target and compatibility implications.

Historical installability does not equal active support.

## 57. Release readiness review

Before a stable release, reviewers SHOULD answer:

1. Which public surfaces changed?
2. Which changes are additive?
3. Which changes are breaking?
4. Which wire contracts changed?
5. Which sibling ranges changed?
6. Which migrations are required?
7. Which deprecations start or end?
8. Which Python or dependency floors changed?
9. Which Customer 360 scenarios passed?
10. Which built artifact hashes were qualified?

## 58. Major release gate

A MAJOR release is the normal vehicle for incompatible changes to stable surfaces.

It may remove accumulated deprecations and simplify design, but SHOULD avoid gratuitous churn.

## 59. Minor release gate

A MINOR release SHOULD remain backward compatible on stable surfaces while adding capabilities, integrations and deprecations.

## 60. Patch release gate

A PATCH release SHOULD fix bugs, security, performance or diagnostics without introducing ordinary stable breaking changes.

## 61. Compatibility exceptions

If a release intentionally violates normal compatibility policy because of security or severe correctness concerns, the exception MUST be explicit in release notes and migration guidance.

## 62. Normative invariants

### REL-INV-01 - Package versions are independent

The three frameworks do not version in lockstep.

### REL-INV-02 - Compatibility is multi-dimensional

Python API, wire contracts, plugins, persistence, CLI and integrations are evaluated separately.

### REL-INV-03 - Stable means governed

Stable public surfaces do not break outside a major release except explicit emergency exceptions.

### REL-INV-04 - Package version is not contract version

Wire and event versions evolve independently.

### REL-INV-05 - Declared ranges are tested

Dependency and sibling compatibility ranges require CI evidence.

### REL-INV-06 - Deprecation precedes ordinary removal

Stable surfaces follow migration and major-release governance.

### REL-INV-07 - Historical state is a compatibility concern

Persisted contracts and execution state have explicit reader and migration support.

### REL-INV-08 - Release candidates represent intended stable contracts

RC churn is minimized and any correction is fully requalified.

### REL-INV-09 - Built artifacts are qualified

The exact wheel or sdist intended for publication is tested.

### REL-INV-10 - Release evidence is auditable

Stable releases identify tested matrices, contracts, artifacts and scenarios.

### REL-INV-11 - Security may tighten compatibility

Unsafe behavior is not preserved merely for compatibility.

### REL-INV-12 - Customer 360 proves ecosystem compatibility

The reference application remains an executable compatibility probe.

## 63. Canonical release lifecycle

~~~text
Architecture and Feature Work
        -> Alpha
        -> Beta
        -> Public Contract Freeze
        -> RC1
        -> Full Qualification
        -> RCn when required
        -> Stable Release
        -> Patch and Minor Evolution
        -> Deprecation Cycle
        -> Next Major when incompatible change is required
~~~

## 64. Canonical ecosystem version picture

~~~text
PyTransformKit
    0.x pre-stable -> 1.x stable

PyIngestKit
    1.x legacy -> 2.x V2 stable

PyWorkflowKit
    1.x legacy -> 2.x V2 stable

Compatibility
    = package ranges
    + contract versions
    + conformance evidence
    + Customer 360
~~~

## 65. Acceptance criteria

This policy is implemented correctly when:

1. each package versions independently;
2. stable public surfaces are explicitly identified;
3. provisional surfaces remain clearly marked;
4. package and wire versions remain distinct;
5. sibling compatibility uses tested ranges and contract versions;
6. minimum and latest supported versions are tested;
7. stable removals follow deprecation and major-release policy;
8. historical wire/state readers declare support;
9. incompatible persisted state has explicit migration behavior;
10. stable optional-extra names are treated as public installation API;
11. plugin contracts evolve deliberately;
12. CLI, config, events and metrics are governed when stable;
13. release candidates run release-grade qualification;
14. exact built artifacts are tested;
15. release notes explain compatibility impact;
16. security exceptions are explicit;
17. published artifacts are immutable by version;
18. important historical fixtures are retained;
19. Customer 360 participates in compatibility qualification;
20. stable releases produce auditable evidence.

## 66. Final architecture statement

PyKit V2 compatibility is not defined by synchronized version numbers.

It is defined by:

~~~text
independent package versions
    + stable public surfaces
    + versioned wire contracts
    + tested dependency ranges
    + explicit migrations
    + release qualification evidence
~~~

> **A version number communicates change; compatibility is proven by contracts and conformance evidence.**

This specification is the baseline for:

- PYKIT_ECOSYSTEM_V2_IMPLEMENTATION_SEQUENCE_AND_MIGRATION_PLAN.md
- PYKIT_ECOSYSTEM_V2_END_TO_END_ACCEPTANCE_CRITERIA.md
- PYTRANSFORMKIT_V1_TARGET_ARCHITECTURE.md
- PYINGESTKIT_V2_TARGET_ARCHITECTURE.md
- PYWORKFLOWKIT_V2_TARGET_ARCHITECTURE.md
- PYTRANSFORMKIT_V1_PUBLIC_API_SPEC.md
- PYINGESTKIT_V2_PUBLIC_API_SPEC.md
- PYWORKFLOWKIT_V2_PUBLIC_API_SPEC.md