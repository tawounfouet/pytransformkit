# PyTransformKit Engine Conformance Matrix

> Baseline: PyTransformKit 0.6.0  
> Qualification lot: LOT-24 — Cross-Engine Conformance and Customer 360 Transformation Gate

This document publishes the release-level semantic conformance status of the
official PyTransformKit execution adapters.

The machine-readable source of truth is:

```text
pytransformkit.conformance
```

and the executable evidence lives under:

```text
tests/contract/conformance/
tests/contract/cross_engine/
tests/contract/engines/
```

## Stability policy

`STABLE` means the adapter is part of the mandatory V1 common semantic
denominator and is qualified by cross-engine contract tests.

`PROVISIONAL` means the adapter is usable for its explicitly advertised
capabilities, but it is not required to satisfy the complete V1 semantic
surface. Unsupported behavior must fail explicitly rather than silently
falling back.

| Engine | Release status | Mandatory for V1 | Execution posture |
| --- | --- | ---: | --- |
| Pandas | STABLE | yes | eager reference adapter |
| Polars | STABLE | yes | eager + qualified lazy execution |
| PyArrow | PROVISIONAL | no | eager columnar subset |
| DuckDB | PROVISIONAL | no | eager + lazy relational SQL subset |

## Semantic dimensions

Legend:

- **Q** — QUALIFIED
- **P** — PROVISIONAL
- **U** — UNSUPPORTED

| Dimension | Pandas | Polars | PyArrow | DuckDB |
| --- | :---: | :---: | :---: | :---: |
| NULL / NaN | Q | Q | P | P |
| Numeric promotion | Q | Q | P | P |
| Decimal | Q | Q | P | Q |
| Timezone | Q | Q | P | P |
| Nested data | Q | Q | P | U |
| Unicode | Q | Q | P | Q |
| Ordering | Q | Q | Q | Q |
| Duplicates | Q | Q | U | Q |
| Empty data | Q | Q | Q | Q |
| Joins | Q | Q | U | Q |
| Aggregates | Q | Q | U | Q |
| Windows | Q | Q | U | Q |
| Quality | Q | Q | U | U |
| Lineage | Q | Q | Q | Q |
| Serialization | Q | Q | Q | Q |
| Capability failure | Q | Q | Q | Q |
| No hidden fallback | Q | Q | Q | Q |

The table is intentionally conservative. A capability being technically
possible in a native engine does not make it qualified in PyTransformKit.

## Mandatory V1 capability set

The stable Pandas and Polars adapters both advertise and qualify the common
V1 capability set:

```text
select
drop
rename
filter
limit
distinct
cast
derive
sort
deduplicate

join_inner
join_left
join_right
join_full
join_semi
join_anti
join_cross

union
intersect
except

aggregate

window
window_rows_cumulative
window_rows_moving

pivot
unpivot
explode
flatten

nested
temporal
duration
quality
```

Polars additionally advertises `lazy`. Lazy execution is additive; it does not
change the logical semantics required by the stable V1 contract.

## LOT-24 semantic evidence

The conformance gate explicitly exercises:

- SQL-like NULL comparison semantics;
- distinction between logical NULL and preserved floating-point NaN;
- integer/float numeric promotion;
- fixed-precision Decimal casts and aggregation;
- timezone-aware temporal operations;
- nested Struct access;
- Unicode string normalization;
- deterministic ordering;
- duplicate elimination;
- empty datasets;
- relational joins and set operations;
- grouped/global aggregates;
- analytical windows;
- quality gates;
- engine-independent logical and field lineage;
- canonical serialization;
- unsupported-capability failure before execution;
- explicit engine selection with no hidden fallback.

Pandas Decimal values use Python `Decimal` at the process-local adapter
boundary. Precision and scale are checked during casts. This preserves logical
Decimal semantics without pretending that Pandas has a native fixed-precision
dtype.

For NULL versus NaN, PyTransformKit preserves the distinction when the native
input representation still carries it. If an upstream Pandas construction has
already collapsed a Python `None` into IEEE NaN before binding, that lost
information cannot be reconstructed by the framework.

## Customer 360 reference gate

LOT-24 includes one canonical multi-input TransformationPlan:

```text
customers ------------------------------┐
                                        │
orders                                  │
  ↓ filter PAID                         │
  ↓ aggregate by customer_id            │
    paid_order_count                    │
    paid_revenue                        │
  └───────────────────────────────┐     │
                                  ↓     ↓
                                LEFT JOIN
                                  ↓
                         normalize email
                                  ↓
                           quality gate
                                  ↓
                              project
                                  ↓
                               order
                                  ↓
                           customer_360
```

The exact same TransformationPlan is qualified on:

- Pandas eager;
- Polars eager;
- Polars lazy.

The gate verifies:

- normalized result equivalence;
- successful quality evidence;
- transitive field lineage from `orders.amount` to `paid_revenue`;
- transitive field lineage from `customers.email` to `normalized_email`;
- canonical TransformationPlan serialization;
- output materialization to Parquet;
- a resulting output `ResourceReference` in transformation lineage.

The resulting ResourceReference is a physical handoff suitable for a
consumer-side PyIngestKit publication flow. PyTransformKit itself does not
create or claim ownership of a governed DatasetVersion.

## Optional engine posture

### PyArrow — PROVISIONAL

PyArrow remains a qualified eager columnar subset. Its type/interchange support
is broader than its transformation execution surface. Relational joins,
aggregates, analytical windows, duplicate semantics and quality gates are not
advertised as stable PyArrow execution capabilities in 0.6.0.

### DuckDB — PROVISIONAL

DuckDB has a strong relational SQL surface including joins, set operations,
aggregates, windows and lazy relational execution. It remains provisional for
the V1 release because nested-data and quality semantics are not yet part of
its qualified PyTransformKit capability set, and several scalar edge cases
remain conservatively marked provisional.

## Release rule

A future adapter may move from PROVISIONAL to STABLE only when:

1. its advertised capabilities are backed by contract tests;
2. its mandatory semantic dimensions are qualified against stable engines;
3. unsupported behavior fails explicitly;
4. it does not introduce hidden engine fallback;
5. its conformance profile is updated together with executable evidence.
