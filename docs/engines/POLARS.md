# Polars Engine Guide

Install the stable Polars extra:

~~~bash
pip install "pytransformkit[polars]"
~~~

Use only the canonical adapter import:

~~~python
from pytransformkit.adapters.polars import PolarsEngineAdapter
~~~

Register it explicitly:

~~~python
from pytransformkit.engines import EngineRegistry

registry = EngineRegistry()
registry.register(PolarsEngineAdapter())
~~~

Polars supports both eager and qualified lazy execution. Lazy selection is explicit:

~~~python
from pytransformkit.runtime import ExecutionMode

result = runtime.execute(
    plan,
    engine="polars",
    inputs=inputs,
    mode=ExecutionMode.LAZY,
)
~~~

A lazy physical output remains process-local until collection/materialization is
explicitly required by the caller or an output boundary.

Polars is a **STABLE mandatory V1 engine**. Its semantic qualification is published in
`docs/ENGINE_CONFORMANCE_MATRIX.md`.

The executable installed-wheel version of this guide is:

~~~text
examples/installed/polars_engine.py
~~~

CI executes that file against the built wheel with the Polars dependency installed.
