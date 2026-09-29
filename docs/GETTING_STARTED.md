# Getting Started with PyTransformKit

PyTransformKit lets you define engine-neutral transformation semantics once, compile them into a LogicalPlan, and execute them explicitly through supported physical engines.

The current development line targets **0.2.0a1** and includes LOT-11: the V1 public model migration plus portable relational transformations.

The canonical path is:

~~~text
Schema
  ↓
TransformationPlan
  ↓
TransformationCompiler
  ↓
LogicalPlan
  ↓
TransformationRuntime
  ↓
InputBinding
  ↓
EngineRegistry
  ├── PandasEngineAdapter
  └── PolarsEngineAdapter
  ↓
TransformationResult
~~~

The former Pipeline / RunPipelineService path is retained only as a pre-V1 compatibility surface.

---

## 1. Clone the repository

~~~bash
git clone https://github.com/tawounfouet/pytransformkit.git
cd pytransformkit
~~~

---

## 2. Create a virtual environment

### Linux / macOS

~~~bash
python -m venv .venv
source .venv/bin/activate
~~~

### Windows PowerShell

~~~powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
~~~

Then upgrade pip:

~~~bash
python -m pip install --upgrade pip
~~~

---

## 3. Install PyTransformKit locally

### Core development environment

~~~bash
pip install -e ".[dev]"
~~~

### Pandas

~~~bash
pip install -e ".[dev,pandas]"
~~~

### Polars

~~~bash
pip install -e ".[dev,polars]"
~~~

### Pandas + Polars

Recommended for local experimentation:

~~~bash
pip install -e ".[dev,pandas,polars]"
~~~

The core package has no mandatory physical-engine dependency.

---

## 4. First TransformationPlan

Start with a logical Schema:

~~~python
from pytransformkit.domain.data.data_types import IntegerType, StringType
from pytransformkit.domain.data.field import Field
from pytransformkit.domain.data.schema import Schema

schema = Schema(
    fields=(
        Field("customer_id", IntegerType(), nullable=False),
        Field("email", StringType(), nullable=True),
        Field("status", StringType(), nullable=False),
    )
)
~~~

Build the transformation declaration:

~~~python
from pytransformkit import TransformationPlan
from pytransformkit.functions import col, lower, trim

builder = TransformationPlan.builder("customers")

customers = builder.input(
    "customers",
    schema=schema,
)

active = builder.filter(
    "active_customers",
    source=customers,
    where=col("status") == "ACTIVE",
)

normalized = builder.derive(
    "normalize_email",
    source=active,
    field_name="normalized_email",
    expression=lower(trim(col("email"))),
)

selected = builder.select(
    "customer_view",
    source=normalized,
    columns=("customer_id", "normalized_email"),
)

plan = builder.output(
    "customers_out",
    selected,
).build()
~~~

TransformationPlan is immutable after build. The authoring builder is only a construction helper.

---

## 5. Inspect the LogicalPlan before execution

Compilation validates graph structure and propagates Schemas without touching physical data:

~~~python
from pytransformkit.planning import TransformationCompiler

logical_plan = TransformationCompiler().compile(plan)

print(logical_plan.plan_name)
print(logical_plan.input_names)
print(logical_plan.output_names)
print(logical_plan.output_schema.names())
print([node.kind.value for node in logical_plan.nodes])
~~~

LogicalPlan is engine-neutral. It describes what must happen, not how Pandas or Polars will perform it.

---

## 6. Execute with Pandas

Create physical data:

~~~python
import pandas as pd

pandas_df = pd.DataFrame(
    {
        "customer_id": [1, 2, 3],
        "email": [
            " JOHN@EXAMPLE.COM ",
            None,
            " BOB@EXAMPLE.COM ",
        ],
        "status": [
            "ACTIVE",
            "INACTIVE",
            "ACTIVE",
        ],
    }
)
~~~

Register the adapter and create the canonical runtime:

~~~python
from pytransformkit import InputBinding, TransformationRuntime
from pytransformkit.adapters.pandas import PandasEngineAdapter
from pytransformkit.engines import EngineRegistry

registry = EngineRegistry()
registry.register(PandasEngineAdapter())

runtime = TransformationRuntime(
    engines=registry,
)
~~~

Execute explicitly:

~~~python
pandas_result = runtime.execute(
    plan,
    engine="pandas",
    inputs={
        "customers": InputBinding.from_native(
            "customers",
            pandas_df,
            engine="pandas",
        )
    },
)

print(pandas_result.execution_id)
print(pandas_result.engine.id)
print(pandas_result.output_schema.names())
print(pandas_result.output_handle.dataframe)
~~~

There is no implicit engine fallback. If the requested engine is not registered or lacks a required capability, execution fails before physical transformation begins.

---

## 7. Execute the same TransformationPlan with Polars

The logical declaration does not change:

~~~python
import polars as pl

from pytransformkit.adapters.polars import PolarsEngineAdapter

registry.register(PolarsEngineAdapter())

polars_df = pl.DataFrame(
    {
        "customer_id": [1, 2, 3],
        "email": [
            " JOHN@EXAMPLE.COM ",
            None,
            " BOB@EXAMPLE.COM ",
        ],
        "status": [
            "ACTIVE",
            "INACTIVE",
            "ACTIVE",
        ],
    }
)

polars_result = runtime.execute(
    plan,
    engine="polars",
    inputs={
        "customers": InputBinding.from_native(
            "customers",
            polars_df,
            engine="polars",
        )
    },
)

print(polars_result.output_handle.frame)
~~~

The same TransformationPlan, Expression AST and LogicalPlan semantics are reused.

---

## 8. Polars lazy execution

Polars explicitly advertises lazy capability:

~~~python
from pytransformkit.runtime import ExecutionMode

lazy_result = runtime.execute(
    plan,
    engine="polars",
    inputs={
        "customers": InputBinding.from_native(
            "customers",
            polars_df.lazy(),
            engine="polars",
        )
    },
    mode=ExecutionMode.LAZY,
)

lazy_frame = lazy_result.output_handle.frame

print(lazy_frame)
print(lazy_frame.collect())
~~~

PyTransformKit preserves the lazy physical result instead of materializing it implicitly.

---

## 9. Multi-input relational transformations

LOT-11 introduces portable multi-input relational semantics.

### Join

~~~python
orders_schema = Schema(
    fields=(
        Field("order_id", IntegerType(), nullable=False),
        Field("customer_id", IntegerType(), nullable=False),
        Field("amount", IntegerType(), nullable=False),
    )
)

builder = TransformationPlan.builder("customer_orders")

customers = builder.input(
    "customers",
    schema=schema,
)

orders = builder.input(
    "orders",
    schema=orders_schema,
)

joined = builder.join(
    "customer_orders",
    left=customers,
    right=orders,
    how="left",
    on=(("customer_id", "customer_id"),),
    right_suffix="_order",
)

relational_plan = builder.output(
    "result",
    joined,
).build()
~~~

Supported join types currently include:

- inner;
- left;
- right;
- full;
- semi;
- anti;
- cross.

Join semantics include explicit key mapping, deterministic output-schema collision handling and configurable NULL key behavior.

### Set operations

TransformationPlanBuilder also exposes:

~~~text
union
intersect
except_
~~~

Set operations require compatible logical Schemas.

---

## 10. InputBinding, ResourceReference and OutputBinding

InputBinding separates the logical Dataset model from physical data supplied at runtime.

The current LOT-11 execution path supports native in-memory bindings:

~~~python
binding = InputBinding.from_native(
    "customers",
    pandas_df,
    engine="pandas",
)
~~~

Portable ResourceReference and OutputBinding contracts are already part of the V1 public model, but their physical resolution/materialization semantics belong to **LOT-20 — Physical I/O Boundary**.

This distinction prevents PyTransformKit from accidentally taking ownership of ingestion lifecycle or publication semantics.

---

## 11. Transformations currently available

Current portable Transformation semantics include:

- select;
- drop;
- rename;
- filter;
- limit;
- distinct;
- cast;
- derive;
- sort;
- deduplicate;
- join;
- union;
- intersect;
- except.

The Expression DSL currently includes:

- col();
- lit();
- comparisons;
- arithmetic operators;
- logical operators;
- is_null();
- is_not_null();
- lower();
- upper();
- trim();
- concat().

---

## 12. Run the local experimentation script

The repository includes:

~~~text
scripts/
└── 00_local_experimentation.py
~~~

Run it from the repository root:

~~~bash
python "scripts/00_local_experimentation.py"
~~~

It demonstrates:

- Schema creation;
- TransformationPlan authoring;
- LogicalPlan compilation;
- Pandas execution;
- Polars eager execution;
- cross-engine result comparison;
- Polars lazy execution.

---

## 13. Run the notebook

An interactive equivalent is available at:

~~~text
notebooks/
└── 00 - Local Experimentation.ipynb
~~~

Start your preferred Jupyter frontend and open the notebook from the repository root.

---

## 14. Run the test suites

### Complete default suite

~~~bash
pytest
~~~

### Pandas contracts

~~~bash
pytest tests/contract/engines/pandas -ra
~~~

### Polars contracts

~~~bash
pytest tests/contract/engines/polars -ra
~~~

### Cross-engine contracts

~~~bash
pytest tests/contract/cross_engine -ra
~~~

### Static quality checks

~~~bash
ruff check .
ruff format --check .
mypy src/pytransformkit
python -m build
~~~

The CI matrix currently verifies Python 3.11, 3.12, 3.13 and 3.14 plus dedicated Pandas, Polars and cross-engine contracts.

---

## 15. What comes next

The revised V1 roadmap continues with:

- **LOT-12** — Aggregation and Grouping;
- **LOT-13** — Analytical Windows;
- **LOT-14** — Reshape / Temporal / Nested;
- **LOT-15** — Data Quality;
- **LOT-16** — Logical and Field Lineage;
- **LOT-17** — Runtime Evidence / Identity / Observability;
- **LOT-18** — PyArrow;
- **LOT-19** — DuckDB;
- **LOT-20** — Physical I/O Boundary;
- **LOT-21** — Serialization / Canonical IR;
- **LOT-22** — Logical Optimizer;
- **LOT-23** — Plugins / Extension Contracts;
- **LOT-24** — Cross-Engine Conformance + Customer 360;
- **LOT-25** — Performance Qualification;
- **LOT-26** — Public API / Security / Migration Freeze;
- **LOT-27** — 1.0 Release Candidate;
- **LOT-28** — 1.0.0 Stable.

The normative roadmap is:

~~~text
docs/specifications/PYTRANSFORMKIT_V1_REVISED_IMPLEMENTATION_ROADMAP.md
~~~

---

## 16. Recommended experimentation workflow

While PyTransformKit is pre-1.0:

1. define the logical input Schema;
2. author a TransformationPlan without native engine objects;
3. compile it into LogicalPlan;
4. inspect propagated output Schemas;
5. bind physical inputs explicitly;
6. execute against Pandas;
7. execute the same plan against Polars;
8. compare normalized semantic results;
9. turn every discovered ambiguity into a regression or conformance test.

This keeps PyTransformKit driven by transformation meaning rather than by any single physical engine API.
