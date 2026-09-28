# PyKit Ecosystem V2 — Security and Trust Boundaries

> **Status:** NORMATIVE SECURITY AND TRUST BASELINE  
> **Architecture generation:** V2  
> **Date:** 2026-09-28  
> **Scope:** PyIngestKit, PyTransformKit, PyWorkflowKit  
> **Compatibility posture:** explicit trust boundaries, least privilege and secure-by-default composition

## 1. Purpose

This document defines the security and trust-boundary model for PyKit V2. It governs untrusted inputs, credentials, resource locators, plugins, subprocesses, external providers, telemetry, remote execution, serialized payloads and future multi-tenant deployments.

The governing principle is:

> **Trust is never implied by proximity, successful parsing, package installation or framework composition.**

The companion rule is:

> **A reference identifies an object; policy and scoped authority determine what may be done with it.**

## 2. Security objectives

PyKit V2 aims to preserve confidentiality, integrity, availability, authenticity, traceability, least privilege and isolation.

The ecosystem does not attempt to replace an IAM platform, identity provider, secret manager, firewall, container sandbox, SIEM or enterprise policy engine. Those remain deployment concerns exposed through explicit runtime boundaries.

## 3. Canonical trust boundaries

The following are trust boundaries by default:

- user input to public APIs;
- serialized payload to decoder;
- ResourceReference to ResourceResolver;
- CredentialReference to CredentialProvider;
- task definition to executor;
- workflow task to subprocess;
- framework to external database, object store or API;
- framework to plugin;
- framework to sibling integration adapter;
- runtime to telemetry backend;
- remote callback to runtime state transition.

At each boundary, structure validation, semantic validation, trust evaluation and authorization remain separate concerns.

## 4. Parsing is not trust

A value may be structurally valid while remaining unauthorized or unsafe.

A valid DatasetVersionReference does not grant dataset access. A valid ResourceReference does not make its target safe. A valid ExternalRunRef does not grant cancellation authority.

Identity and authorization therefore remain distinct.

## 5. Reference possession is not authority

References are not bearer credentials unless a specific contract explicitly says otherwise.

The preferred model is:

    portable reference
        identifies resource or execution

    current security context
        authorizes requested operation

This applies to reads, writes, publication, replay, inspection, cancellation and reconciliation.

## 6. Credential model

Raw credentials MUST remain outside ordinary public contracts.

PyKit implementations SHOULD use abstractions such as CredentialReference, SecretReference, CredentialProvider and SecretResolver.

A credential reference may identify a logical secret location, but MUST NOT contain the raw password, token, private key, cloud key or signed access token.

## 7. Secret lifecycle

Secrets SHOULD be resolved at runtime and as late as practical. They SHOULD remain in memory only for the lifetime needed by the provider operation.

Secrets MUST NOT be copied unnecessarily into:

- workflow state;
- execution manifests;
- lineage;
- CorrelationContext;
- logs;
- metrics;
- traces;
- durable FailureEvidence;
- resource metadata;
- package metadata.

Stable credential references SHOULD permit rotation without rewriting durable plans or references.

## 8. Least privilege

Every runtime integration SHOULD receive only the capabilities required for the operation.

Examples include read-only source access, publication-only target access, metadata-store access limited to workflow metadata, or engine access limited to the schemas needed for a transformation.

Where providers support capability separation, READ, WRITE, PUBLISH, INSPECT, CANCEL and RECONCILE SHOULD be independently authorized.

## 9. PyTransformKit trust boundary

PyTransformKit security-sensitive surfaces include TransformationPlan input, resource resolution, engine adapters, SQL generation, filesystem I/O, UDFs, plugins and output writes.

Declarative domain objects SHOULD remain side-effect free.

Expression AST values are data and SHOULD be compiled through controlled adapters. They MUST NOT rely on arbitrary Python evaluation of untrusted strings.

Raw SQL, UDFs and callbacks are explicit trust-sensitive escape hatches and must not be presented as equivalent to declarative expressions.

## 10. PyIngestKit trust boundary

PyIngestKit handles external source acquisition, RAW persistence, decoding, validation, versioning and publication.

External source bytes are untrusted by default.

Decoders SHOULD support bounded input size, nesting, record count, decompressed size and temporary-storage use.

Archive handling MUST prevent traversal outside the configured extraction root. Nested archives, symlinks and decompression ratios require explicit limits.

## 11. PyWorkflowKit trust boundary

PyWorkflowKit coordinates executable workloads.

Security-sensitive surfaces include TaskDefinition, executors, subprocesses, remote workers, environment propagation, cancellation, recovery, metadata stores and executor plugins.

Workflow orchestration does not make arbitrary untrusted code safe. Callbacks, shell commands, Python functions and plugins are executable-code surfaces and require a stronger trust model.

## 12. Resource locator validation

A resource locator is untrusted until interpreted by a scheme-aware resolver.

Resolvers SHOULD support explicit policy around:

- allowed schemes;
- allowed hosts or domains;
- allowed ports;
- HTTPS requirements;
- private-network access;
- filesystem roots;
- symlink behavior;
- overwrite modes;
- destination restrictions.

Applications that accept user-provided network references SHOULD be able to prevent requests to disallowed internal destinations.

Redirected network destinations MUST be revalidated under the same policy.

## 13. Filesystem safety

Filesystem resolvers SHOULD normalize paths and enforce configured roots.

Unsupported special file types such as devices, named pipes or sockets SHOULD be rejected unless explicitly allowed.

A local path claiming cross-host portability is invalid.

Temporary files SHOULD use safe permissions and should be cleaned up according to lifecycle policy.

## 14. SQL safety

Data values SHOULD use parameterized provider APIs where supported.

Identifiers and generated query fragments SHOULD be emitted by controlled compilers or validated quoting rules.

Untrusted values MUST NOT be concatenated directly into raw SQL strings.

Raw SQL support, if provided, is explicitly trusted application code with reduced portability and lineage guarantees.

## 15. Plugin trust model

Plugins are executable code.

The lifecycle is:

1. discover metadata;
2. validate compatibility;
3. approve or allow;
4. activate explicitly.

Installation does not imply activation.

Applications SHOULD be able to allow-list approved plugins. Untrusted wire payloads MUST NOT install, import, activate or trust a plugin merely by naming it.

In-process plugins execute with process privileges. PyKit MUST NOT describe ordinary Python plugins as sandboxed.

## 16. Plugin capabilities

Plugins SHOULD declare a specific capability such as engine adapter, source connector, target connector, executor, metadata store, telemetry exporter or resource resolver.

Hosts SHOULD activate only the requested capability.

Sensitive deployments requiring stronger isolation SHOULD place risky plugins behind a process, container, VM or remote-worker boundary.

## 17. Import-time safety

Importing a PyKit package MUST NOT:

- open network connections;
- resolve secrets;
- execute subprocesses;
- activate plugins;
- start workers;
- start telemetry exporters;
- mutate external state.

Import remains local and declarative.

## 18. Deserialization trust boundary

Every deserialization point is a trust boundary.

Readers MUST assume payloads may be malformed, oversized, stale, unsupported, malicious, inconsistent or unauthorized.

Durable/shared wire contracts MUST NOT rely on pickle, cloudpickle, dill, eval, exec or arbitrary module/class reconstruction.

Schema-driven parsing is mandatory.

## 19. Payload limits

Wire readers SHOULD support maximum byte size, nesting depth, string length, array length and metadata-key count.

If a reader cannot understand safety-sensitive semantics involving authorization, identity, idempotency, retry safety, uncertainty, ownership or secret handling, it MUST fail closed.

## 20. ExternalRunRef security

ExternalRunRef identifies an execution; it does not grant authority over it.

Before inspect, cancel or reconcile, an adapter SHOULD validate provider identity, reference kind, namespace, operation requested and current authorization.

Permission to inspect does not imply permission to cancel.

## 21. Subprocess execution

Subprocess APIs SHOULD prefer an executable plus argument vector rather than shell-string concatenation.

Shell mode should be explicit and treated as higher risk.

Child environments SHOULD receive only required variables. Blind propagation of the full parent environment is discouraged because it may expose cloud credentials, database passwords, CI tokens or API keys.

Captured stdout and stderr SHOULD be bounded, redacted and governed by retention policy.

A subprocess is not a full security sandbox.

## 22. Remote workers

Remote workers SHOULD receive only the task inputs, portable references, scoped credentials, correlation context and bounded configuration required for their assignment.

A compromised worker should not automatically gain access to unrelated datasets, workflows or credentials.

## 23. Artifact and metadata security

Workflow metadata, ingestion metadata, lineage and manifests may reveal sensitive dataset names, field names, locations, business concepts or operational topology.

Artifact and metadata stores therefore require access controls appropriate to their contents.

RAW may contain the most sensitive unprocessed source material and SHOULD receive explicit encryption, retention, immutability, access and deletion consideration.

## 24. Transformation intermediates

Temporary transformation outputs may contain sensitive data even when ephemeral.

Runtime implementations SHOULD address spill-file permissions, cleanup, retention, worker isolation and encryption where required.

Ephemeral does not mean non-sensitive.

## 25. Output and publication authority

Physical write authority and publication authority are distinct.

PyTransformKit may have permission to write a physical result without having authority to publish a governed DatasetVersion.

Publication requires an explicitly authorized target and security context.

Overwrite behavior SHOULD be explicit through modes such as create-new, fail-if-exists, replace-explicit, append-explicit or merge-explicit.

## 26. Integrity evidence

DatasetVersions and durable artifacts SHOULD preserve available integrity evidence such as content fingerprints, checksums, schema fingerprints and publication manifests.

Checksum verifies content integrity, not producer authenticity.

Signed contracts or signed artifacts MAY be used when deployments need stronger authenticity guarantees.

## 27. Cross-framework trust

A sibling framework result remains external input to the consumer boundary.

Consumer anti-corruption layers SHOULD validate contract kind, contract version, identity, namespace, reference safety and failure semantics before mapping into local domain objects.

The consumer owns authorization required for its protected operation.

## 28. Retry as a security concern

Retries can amplify load and side effects.

Retry policy MUST remain bounded by attempt budgets and deadlines and SHOULD respect rate limits, idempotency, provider guidance and authorization.

Unbounded retry is both a reliability defect and a denial-of-service risk.

## 29. Reconciliation and replay

Reconciliation SHOULD use the least privilege needed to inspect provider truth.

It MUST NOT silently mutate provider state unless the contract explicitly defines that behavior.

Replay may reprocess historical sensitive data. Replay authorization SHOULD therefore be explicit and distinct from ordinary current-run execution.

## 30. Exfiltration boundaries

Output sinks, publication targets, plugins and telemetry destinations can become data-exfiltration channels.

Applications SHOULD be able to restrict destination schemes, hosts, target namespaces and external telemetry destinations.

Arbitrary output URLs are inappropriate defaults for multi-user services.

## 31. Telemetry trust boundary

Telemetry may leave the primary runtime environment.

Before export, apply redaction, attribute allow-listing, tenant isolation where relevant, payload limits, destination policy and transport security.

Logs, metrics, traces and FailureEvidence MUST NOT expose raw credentials, signed URLs, secret environment variables or unrestricted payload values.

## 32. Multi-tenancy posture

Multi-tenancy is not required by PyKit core.

If introduced, tenant context MUST be explicit and MUST NOT be trusted solely because it appears in user-controlled metadata.

A multi-tenant deployment must isolate metadata, artifacts, credentials, resource resolution, telemetry, workflow state, publication and plugin configuration.

Tenant ID alone is not an authorization control.

## 33. PrincipalContext

A deployment MAY introduce PrincipalContext for security identity and claims.

PrincipalContext SHOULD remain distinct from CorrelationContext.

CorrelationContext traces work. PrincipalContext describes the security actor or delegated security context.

Authority delegated to child workloads SHOULD be explicit, scoped, auditable and time-limited where practical.

## 34. Authorization ownership

The component performing the protected operation owns the final authorization check.

Examples:

- ResourceResolver authorizes resource resolution;
- publication service authorizes publication;
- executor authorizes executable workload capability;
- SecretResolver authorizes secret resolution;
- external-run adapter authorizes cancellation or reconciliation.

Upstream validation does not remove downstream responsibility.

## 35. Secure defaults

Default behavior SHOULD prefer:

- no automatic plugin activation;
- no external telemetry unless configured;
- no shell mode unless explicit;
- no raw credential serialization;
- bounded payload parsing;
- no implicit overwrite;
- no cross-host assumption for local paths;
- no fallback to broader credentials;
- no execution of code named by untrusted payloads.

## 36. Fail closed

Security-sensitive ambiguity MUST fail closed.

Examples include unknown credential scheme, unsupported wire version, unknown plugin, invalid signature, unauthorized resource, unsafe path or ambiguous tenant context.

Telemetry exporter failure is different because it is normally an observability concern rather than an authorization decision.

## 37. Remote callbacks

Remote callbacks or webhooks SHOULD be authenticated and mapped to an existing execution identity.

Where callbacks mutate durable state, deployments SHOULD use provider-supported signature verification, freshness checks and event-ID deduplication where available.

An authenticated callback still must satisfy runtime state-machine rules.

## 38. Availability controls

Applications accepting untrusted workloads MAY impose quotas on DAG size, expression depth, input bytes, output bytes, concurrency, retries and execution duration.

This protects availability and multi-user fairness.

## 39. Retention and deletion

Sensitive classes may require separate retention rules for RAW, DatasetVersion data, temporary outputs, workflow metadata, logs, traces, manifests and lineage.

PyKit SHOULD describe deletion accurately. Removing metadata, tombstoning a reference, deleting an object and securely erasing physical media are different operations.

## 40. Audit-relevant actions

Actions such as manual reconciliation, manual state override, publication, plugin activation, cancellation and historical replay SHOULD be auditable where required.

Administrative override evidence SHOULD include actor, timestamp, target reference, previous state, new state and reason.

History must not be silently rewritten.

## 41. Security testing baseline

Conformance tests SHOULD include:

- secret redaction;
- credential-free reference serialization;
- path traversal rejection;
- archive traversal rejection;
- network target rejection under configured policy;
- wire payload size limits;
- duplicate-key rejection;
- non-executable deserialization;
- plugin activation controls;
- subprocess argument handling;
- environment allow-listing;
- callback state validation;
- cross-tenant denial when multi-tenancy is enabled.

## 42. Fuzzing targets

Security fuzzing SHOULD prioritize wire decoders, URI/reference parsers, archive parsers, expression parsers, plugin metadata and remote callback payloads.

Resource limits remain active during fuzzing.

## 43. Threat-model review

Major features SHOULD answer:

1. What input is untrusted?
2. What authority does this component hold?
3. What external side effects are possible?
4. Which secrets are accessible?
5. Which resources can be resolved?
6. Can arbitrary code execute?
7. Can one user or tenant affect another?
8. Can retries amplify harm?
9. Can telemetry leak information?
10. Which automated tests prove the boundary?

## 44. Security review gate

Explicit security review is required when introducing a new credential flow, remote protocol, executable-code surface, plugin type, resource scheme, publication target, subprocess capability, multi-tenant context, deserializer or privilege boundary.

## 45. Security and compatibility

Security hardening may intentionally reject previously accepted unsafe inputs.

Release notes SHOULD distinguish security hardening, breaking contract changes and ordinary bug fixes.

Security fixes may justify accelerated compatibility changes when necessary.

## 46. Acceptance criteria

This specification is implemented correctly when:

1. raw credentials never become ordinary public contract values;
2. references identify objects without granting authority;
3. parsing and authorization remain separate;
4. deserialization cannot execute arbitrary code;
5. plugin discovery does not activate code;
6. untrusted payloads cannot install or activate plugins;
7. resource targets are validated by scheme-aware resolvers;
8. filesystem access can enforce allowed roots;
9. network resolution can enforce target policy;
10. subprocess APIs distinguish argument-vector and shell modes;
11. child environments can be restricted;
12. telemetry, lineage and manifests are redacted;
13. RAW and temporary data receive explicit access and retention controls;
14. publication requires explicit authority;
15. retries remain bounded;
16. callbacks are authenticated and state-validated where used;
17. multi-tenant isolation is enforced beyond tenant identifiers;
18. security-sensitive overrides are auditable;
19. core imports have no privileged side effects;
20. security boundaries have automated conformance tests.

## 47. Normative invariants

### SEC-INV-01 — Trust is explicit

Successful parsing, installation or composition never implies trust.

### SEC-INV-02 — Identity is not authorization

References and IDs identify; runtime policy authorizes.

### SEC-INV-03 — Least privilege applies at provider boundaries

Components receive only the capabilities required for their work.

### SEC-INV-04 — Secrets are referenced, not serialized

Raw secret material stays outside ordinary contracts and telemetry.

### SEC-INV-05 — Deserialization is non-executable

Wire payloads cannot select arbitrary Python code.

### SEC-INV-06 — Plugins require explicit activation

Discovery and installation do not activate code.

### SEC-INV-07 — Resource resolution validates the target

Locator syntax alone does not make a destination safe.

### SEC-INV-08 — Executable-code surfaces are explicit

Callbacks, UDFs, subprocesses and plugins are not ordinary data.

### SEC-INV-09 — Untrusted payloads cannot activate code

Contracts and events cannot auto-load arbitrary modules or plugins.

### SEC-INV-10 — Telemetry is redacted before export

Downstream sinks are not trusted to remove secrets.

### SEC-INV-11 — Reference possession is not authority

Holding a reference does not grant read, publish, cancel or replay rights.

### SEC-INV-12 — Security checks fail closed

Unknown or ambiguous safety semantics do not default to permission.

## 48. Canonical trust flow

    Untrusted or External Input
            ↓
    Structural Validation
            ↓
    Semantic Validation
            ↓
    Trust and Policy Evaluation
            ↓
    Authorization
            ↓
    Credential Resolution
            ↓
    Scoped Runtime Capability
            ↓
    Protected Operation
            ↓
    Redacted Evidence or Audit

Skipping directly from parsing to privileged execution is prohibited.

## 49. Canonical ecosystem composition

    Application Security Context
              │
      ┌───────┼────────┐
      │       │        │
      ▼       ▼        ▼
    Workflow  Ingest   Transform
      │       │        │
      └── scoped external providers ──

Portable references cross framework boundaries.

Raw credentials do not.

Authorization is evaluated by the component performing the protected operation.

## 50. Final architecture statement

PyKit V2 treats security as a property of boundaries rather than a decorator added after implementation.

The canonical sequence is:

    validate structure
        ↓
    validate semantics
        ↓
    establish trust context
        ↓
    authorize capability
        ↓
    resolve credentials
        ↓
    perform scoped operation
        ↓
    emit redacted evidence

The central rule is:

> **A reference tells the system what object is meant; only policy and scoped authority decide what may be done with it.**

This specification is the baseline for:

- PYKIT_ECOSYSTEM_V2_REFERENCE_APPLICATION_SPEC.md
- PYKIT_ECOSYSTEM_V2_RELEASE_COMPATIBILITY_AND_VERSIONING_POLICY.md
- PYKIT_ECOSYSTEM_V2_IMPLEMENTATION_SEQUENCE_AND_MIGRATION_PLAN.md
- PYTRANSFORMKIT_V1_TARGET_ARCHITECTURE.md
- PYINGESTKIT_V2_TARGET_ARCHITECTURE.md
- PYWORKFLOWKIT_V2_TARGET_ARCHITECTURE.md
