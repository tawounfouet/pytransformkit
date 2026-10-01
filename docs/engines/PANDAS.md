# Pandas Engine Guide

Install the stable Pandas extra:

~~~bash
pip install "pytransformkit[pandas]"
~~~

Use only the canonical adapter import:

~~~python
from pytransformkit.adapters.pandas import PandasEngineAdapter
~~~

Register it explicitly:

~~~python
from pytransformkit.engines import EngineRegistry

registry = EngineRegistry()
registry.register(PandasEngineAdapter())
~~~

Native Pandas values are process-local bindings:

~~~python
InputBinding.from_native(
    "customers",
    customers_df,
    engine="pandas",
)
~~~

Pandas is a **STABLE mandatory V1 engine**. Its qualified semantic dimensions and
capabilities are published in `docs/ENGINE_CONFORMANCE_MATRIX.md`.

The executable installed-wheel version of this guide is:

~~~text
examples/installed/pandas_engine.py
~~~

CI executes that file against the built wheel with the Pandas dependency installed.
