# Getting Started with PyTransformKit

PyTransformKit lets you define a logical transformation pipeline once and execute it
through different physical engines.

The current implementation supports the first engine-agnostic cycle with:

- typed logical Schemas;
- an immutable Expression AST;
- logical Transformations;
- Pipeline / DAG planning;
- static output-Schema propagation;
- explicit engine registration;
- Pandas eager execution;
- Polars eager and lazy execution;
- Pandas / Polars cross-engine semantic contracts.

The current development line targets **0.1.0a1**.

---

## 1. Clone the repository

```bash
git clone https://github.com/tawounfouet/pytransformkit.git
cd pytransformkit
```

---

## 2. Create a virtual environment

### Linux / macOS

```bash
python -m venv .venv
source .venv/bin/activate
```

### Windows PowerShell

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Upgrade pip:

```bash
python -m pip install --upgrade pip
```

---

## 3. Install PyTransformKit locally

### Core development environment

```bash
pip install -e ".[dev]"
```

This keeps the physical engines optional.

### Pandas

```bash
pip install -e ".[dev,pandas]"
```

### Polars

```bash
pip install -e ".[dev,polars]"
```

### Pandas + Polars

Recommended for the current experimentation examples:

```bash
pip install -e ".[dev,pandas,polars]"
```

Because the package is installed in editable mode, local source-code changes are
immediately visible without reinstalling the project.

---

## 4. Run the first local script

The repository includes:

```text
scripts/
└── 00_local_experimentation.py
```

Run it from the repository root:

```bash
python "scripts/00_local_experimentation.py"
```

The script demonstrates the complete current execution path:

```text
Schema
  ↓
Pipeline
  ↓
Expression AST
  ↓
Transformations
  ↓
PipelinePlanner
  ↓
LogicalPlan
  ↓
RunPipelineService
  ↓
EngineRegistry
  ├── PandasAdapter
  └── PolarsAdapter
```

It also checks that Pandas and Polars produce the same logical result.

---

## 5. Run the notebook

An equivalent interactive notebook is available at:

```text
notebooks/
└── 00 - Local Experimentation.ipynb
```

Start Jupyter from the repository root:

```bash
jupyter notebook
```

Then open:

```text
notebooks/00 - Local Experimentation.ipynb
```

If Jupyter is not already installed, install your preferred notebook frontend
separately, for example:

```bash
pip install jupyter
```

---

## 6. Minimal Pandas example

```python
import pandas as pd

from pytransformkit import EngineRegistry, RunPipelineService
from pytransformkit.domain.data.data_types import IntegerType, StringType
from pytransformkit.domain.data.field import Field
from pytransformkit.domain.data.schema import Schema
from pytransformkit.domain.pipelines import Pipeline
from pytransformkit.functions import col, lower, trim
from pytransformkit.infrastructure.engines.pandas import (
    PandasAdapter,
    PandasDatasetHandle,
)

schema = Schema(
    fields=(
        Field("customer_id", IntegerType(), nullable=False),
        Field("email", StringType(), nullable=True),
        Field("status", StringType(), nullable=False),
    )
)

pipeline = (
    Pipeline.create("customers", schema)
    .filter(col("status") == "ACTIVE")
    .derive(
        "normalized_email",
        lower(trim(col("email"))),
    )
    .select(
        "customer_id",
        "normalized_email",
    )
)

dataframe = pd.DataFrame(
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

registry = EngineRegistry()
registry.register(PandasAdapter())

result = RunPipelineService(registry).run(
    pipeline,
    PandasDatasetHandle(dataframe),
    engine_id="pandas",
)

print(result.output_handle.dataframe)
```

---

## 7. Inspect a LogicalPlan before execution

Planning is independent from physical data execution:

```python
from pytransformkit.domain.pipelines import PipelinePlanner

plan = PipelinePlanner().plan(pipeline)

print(plan.pipeline_name)
print(plan.output_schema.names())
print([node.kind.value for node in plan.nodes])
```

This validates the transformation chain and output Schema before an engine processes
any rows.

---

## 8. Execute the same Pipeline with Polars

The logical Pipeline does not change:

```python
import polars as pl

from pytransformkit.infrastructure.engines.polars import (
    PolarsAdapter,
    PolarsDatasetHandle,
)

registry.register(PolarsAdapter())

polars_frame = pl.DataFrame(
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

result = RunPipelineService(registry).run(
    pipeline,
    PolarsDatasetHandle(polars_frame),
    engine_id="polars",
)

print(result.output_handle.frame)
```

---

## 9. Polars lazy execution

Polars explicitly advertises the `LAZY` capability:

```python
from pytransformkit import ExecutionContext, ExecutionMode

lazy_result = RunPipelineService(registry).run(
    pipeline,
    PolarsDatasetHandle(polars_frame.lazy()),
    engine_id="polars",
    context=ExecutionContext(
        mode=ExecutionMode.LAZY,
    ),
)

lazy_frame = lazy_result.output_handle.frame

print(lazy_frame)
print(lazy_frame.collect())
```

PyTransformKit keeps the result lazy until the caller explicitly materializes it.

---

## 10. Transformations currently available

The initial portable Transformation set includes:

- `select`;
- `drop`;
- `rename`;
- `filter`;
- `limit`;
- `distinct`;
- `cast`;
- `derive`;
- `sort`;
- `deduplicate`.

The Expression DSL currently includes:

- `col()`;
- `lit()`;
- comparisons;
- arithmetic operators;
- logical operators;
- `is_null()`;
- `is_not_null()`;
- `lower()`;
- `upper()`;
- `trim()`;
- `concat()`.

---

## 11. Run the test suites

### Complete default suite

```bash
pytest
```

### Pandas contracts

```bash
pytest tests/contract/engines/pandas -ra
```

### Polars contracts

```bash
pytest tests/contract/engines/polars -ra
```

### Cross-engine contracts

```bash
pytest tests/contract/cross_engine -ra
```

### Static quality checks

```bash
ruff check .
ruff format --check .
mypy src/pytransformkit
python -m build
```

---

## 12. What is not implemented yet

The next capabilities belong to the frozen roadmap toward 1.0.0:

- Join / Union / Intersect / Except → **LOT-11**;
- aggregations and grouping → **LOT-12**;
- analytical windows → **LOT-13**;
- reshaping, temporal and nested transformations → **LOT-14**;
- Data Quality → **LOT-15**;
- Lineage → **LOT-16**;
- Observability and Audit → **LOT-17**;
- PyArrow → **LOT-18**;
- DuckDB → **LOT-19**;
- I/O and Connectors → **LOT-20**;
- portable Serialization / IR → **LOT-21**;
- optimizer → **LOT-22**;
- plugin architecture → **LOT-23**.

The full normative roadmap is available in:

```text
docs/ROADMAP_LOT_11_TO_1_0.md
```

---

## 13. Recommended experimentation workflow

While PyTransformKit is pre-1.0:

1. reproduce a transformation need with a small dataset;
2. define the expected logical Schema;
3. build the Pipeline without engine-specific code;
4. inspect its LogicalPlan;
5. execute it through Pandas;
6. execute the same Pipeline through Polars;
7. compare the semantic results;
8. turn discovered ambiguity or bugs into regression/contract tests.

This keeps the framework driven by observable semantics rather than by the API of any
single physical engine.
