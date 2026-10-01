# Polars Engine Guide

Polars is a **STABLE** mandatory V1 engine.

Install:

~~~bash
pip install "pytransformkit[polars]"
~~~

Register it explicitly:

~~~python
from pytransformkit.adapters.polars import PolarsEngineAdapter
from pytransformkit.engines import EngineRegistry

engines = EngineRegistry()
engines.register(PolarsEngineAdapter())
~~~

Polars supports the qualified eager V1 semantics and the qualified lazy path.
Lazy execution is requested explicitly with:

~~~python
from pytransformkit.runtime import ExecutionMode

result = runtime.execute(
    plan,
    engine="polars",
    inputs=bindings,
    mode=ExecutionMode.LAZY,
)
~~~

The complete executable guide is:

~~~text
scripts/guides/polars_engine.py
~~~

LOT-26 runs that script against the **built wheel** in CI. The example therefore
guards both the public imports and the engine execution path.

See `docs/ENGINE_CONFORMANCE_MATRIX.md` for the exact semantic qualification.
