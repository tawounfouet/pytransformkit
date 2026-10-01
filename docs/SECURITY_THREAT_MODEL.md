# PyTransformKit V1 Security Review and Threat Model

> Security review baseline: LOT-26 / 0.8.0  
> Governing model: `PYKIT_ECOSYSTEM_V2_SECURITY_AND_TRUST_BOUNDARIES.md`

PyTransformKit transforms data. It does not provide an operating-system sandbox, a
multi-tenant authorization system or a secret store. Its security responsibility is to
keep declarative contracts non-executable, make physical authority explicit and prevent
portable evidence from accidentally carrying raw credentials.

## Trust-boundary inventory

| Surface | Untrusted input | Authority held | Side effects |
| --- | --- | --- | --- |
| TransformationPlan / Expression | caller declarations | none | none |
| wire decoder | JSON/bytes | local object construction from closed registry | none |
| ResourceReference | locator + metadata | none | none until resolved |
| Reader / Writer | resource requests | configured provider/filesystem authority | reads/writes |
| EngineAdapter | LogicalPlan + physical handles | engine/session authority | engine execution |
| plugin discovery | installed entry-point metadata | none | enumeration only |
| plugin activation | explicitly selected plugin | registry extension authority | arbitrary plugin code can run |
| telemetry sink | sanitized events/metrics/spans | sink authority | external telemetry delivery |

## 1. What input is untrusted?

Treat as untrusted:

- serialized wire payloads;
- resource locators and metadata;
- transformation declarations received across application boundaries;
- plugin metadata from installed distributions;
- provider/engine-returned errors and diagnostics;
- physical input data.

## 2. What authority does the framework hold?

Core logical objects hold no external authority. Runtime authority is supplied explicitly
through registered engines, Reader/Writer implementations, resource resolvers, telemetry
sinks and explicitly activated plugins.

There is no mandatory global registry or hidden default provider.

## 3. What external side effects are possible?

Side effects are limited to explicit runtime boundaries:

- engine execution;
- physical resource reads;
- physical resource writes;
- telemetry delivery;
- explicitly activated plugin code.

Planning, schema construction, expression construction, serialization and lineage
inspection perform no provider calls.

## 4. Which secrets are accessible?

Raw secrets are not part of portable contracts.

`CredentialReference` may identify a credential that an application/provider resolver
can obtain out of band. `ResourceReference` now rejects:

- URI userinfo credentials;
- credential-bearing query keys such as token/signature/password/API key;
- credential-bearing metadata keys.

This prevents signed URLs or embedded passwords from silently entering serialization,
lineage or manifests.

## 5. Which resources can be resolved?

Resolution is explicit and provider-specific.

The local filesystem profile confines resources to its configured root and rejects path
traversal. Other schemes require an explicitly registered resolver/Reader/Writer and
must implement their own authority checks.

## 6. Can arbitrary code execute?

Not from canonical wire payloads.

The safe serializer:

- uses strict JSON;
- uses a closed semantic type registry;
- rejects unknown semantic types;
- never imports a payload-selected Python module/class;
- rejects executable/process-local values;
- has no pickle/cloudpickle/dill/eval/exec fallback;
- enforces payload-size and nesting limits.

Arbitrary code can execute only through ordinary trusted Python integration such as an
explicit plugin activation or caller-supplied application code. Plugin discovery alone
does not load/activate plugin providers.

## 7. Can one user or tenant affect another?

PyTransformKit does not own tenant isolation. An embedding application must scope engine
sessions, filesystem roots, credential resolvers and plugin registries appropriately.
The framework must not be treated as a multi-tenant security boundary.

## 8. Can retries amplify harm?

TransformationRuntime does not own workflow retry policy. Provider retries are exposed as
evidence rather than silently stacked. Writes declare `RetrySafety`; uncertain writes
preserve `UNKNOWN_OUTCOME` / reconciliation requirements rather than claiming a safe
retry.

## 9. Can telemetry leak information?

Telemetry is best-effort and redacted before crossing the sink boundary. Sensitive key
fragments are redacted, and high-cardinality execution/correlation/resource locators are
not accepted as default metric labels.

Portable diagnostics/manifests must not contain raw credential values.

## 10. Which tests prove the boundary?

Primary LOT-26 security evidence:

~~~text
tests/contract/security/test_security_freeze.py
tests/contract/serialization/test_security_and_migrations.py
tests/contract/plugins/test_discovery_and_activation.py
tests/contract/io/test_local_file_io.py
tests/contract/api/test_public_api_freeze.py
~~~

These cover credential-bearing locators, path confinement, safe decoding, payload bounds,
non-executable serialization, explicit plugin activation, optional-engine import
isolation and public-surface exclusions.

## Security review gate

LOT-26 reviewed all security-sensitive features introduced before the freeze:

- credential references;
- local filesystem resource scheme;
- writes/unknown outcome;
- DuckDB SQL lowering;
- safe wire decoder;
- plugin architecture;
- telemetry redaction.

No new remote network protocol, subprocess surface, publication target or multi-tenant
privilege model is introduced by LOT-26 itself.

Future additions in any of those categories require a new explicit security review.
