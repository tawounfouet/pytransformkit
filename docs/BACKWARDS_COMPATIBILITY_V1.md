# PyTransformKit V1 Backwards Compatibility Freeze

> Historical baseline: `0.8.0`  
> Qualification line: `0.9.0`  
> Target: `1.0.0rc1` → `1.0.0`

LOT-27 turns upgrade compatibility into release evidence. The goal is not to
preserve every pre-1.0 implementation detail; it is to preserve the stable V1
contract frozen by LOT-26 and to make every deliberate pre-RC amendment visible.

## Machine-readable contracts

The compatibility gate uses three coordinated baselines:

```text
contracts/public_api_v1.json
contracts/error_codes_v1.json
contracts/consumer_compatibility_v1.json
```

They protect distinct dimensions:

- `public_api_v1.json`: imports, signatures, protocols, enums, extras, engines and wire contracts;
- `error_codes_v1.json`: public exception identity, parent hierarchy and stable machine-readable error code;
- `consumer_compatibility_v1.json`: upgrade-facing aliases, warning behavior, wire contracts, plugin protocol and a digest of the error catalogue.

## Historical consumer baseline

The consumer baseline starts from PyTransformKit `0.8.0`, the LOT-26 public
contract freeze. During the `0.9.0` qualification line, changes to that freeze
are allowed only when they correct a release blocker and are explicitly recorded
before `1.0.0rc1`.

Once `1.0.0rc1` is published, the policy becomes blocker-fixes-only.

## Error-code policy

Every public subclass of `PyTransformKitError` must have:

1. a unique code matching `PTK-<DOMAIN>-NNN`;
2. a stable public exception name;
3. a stable parent relationship for V1 consumers;
4. an entry in `contracts/error_codes_v1.json`.

Adding a new error may be compatible. Reusing, renumbering or silently moving an
existing code is a compatibility event and must fail the release gate.

## Legacy aliases

Pre-V1 root aliases such as `Pipeline`, `RunPipelineService`,
`ExecutionContext` and `WriteMode` remain non-canonical. While retained,
they must resolve successfully, remain absent from root `__all__`, and emit
exactly one `DeprecationWarning`.

Their presence is migration support, not permission to grow the legacy facade.

## Plugin protocol V1 pre-RC amendment

Qualification found a release blocker in the LOT-26 baseline: the default
`PluginCompatibility()` range ended at `<1.0.0`. That would make a plugin
using the default V1 compatibility declaration reject PyTransformKit `1.0.0`
stable.

LOT-27 corrects the default host range to:

```text
PyTransformKit >=0.5.0,<2.0.0
plugin protocol == 1
entry-point group == pytransformkit.plugins
```

This is a deliberate pre-RC compatibility correction, not an accidental API
drift. The API snapshot signature hash must therefore be amended once, together
with this document and the consumer snapshot, before `1.0.0rc1`.

## CI gate

The `backwards-compatibility-contract` job verifies:

```text
error catalogue
      +
consumer compatibility snapshot
      +
legacy alias behavior
      +
plugin V1 host/protocol range
      ↓
PASS / FAIL
```

It runs alongside the stricter built-wheel API freeze, serialization, plugin,
security, conformance and artifact qualification jobs.
