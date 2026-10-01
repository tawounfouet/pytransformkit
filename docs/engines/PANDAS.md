# Pandas Engine Guide

Pandas is a **STABLE** mandatory V1 engine.

Install:

~~~bash
pip install "pytransformkit[pandas]"
~~~

Register it explicitly:

~~~python
from pytransformkit.adapters.pandas import PandasEngineAdapter
from pytransformkit.engines import EngineRegistry

engines = EngineRegistry()
engines.register(PandasEngineAdapter())
~~~

Native values enter through `InputBinding.from_native(..., engine="pandas")`.
PyTransformKit never chooses Pandas merely because it is installed.

The complete executable example for this guide is:

~~~text
scripts/guides/pandas_engine.py
~~~

LOT-26 runs that script against the **built wheel** in CI, so the guide is coupled
to the frozen public API rather than to internal source imports.

Pandas is the eager reference adapter. See `docs/ENGINE_CONFORMANCE_MATRIX.md`
for the exact semantic dimensions qualified in the current release line.
