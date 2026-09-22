from __future__ import annotations

import sys

import pytransformkit


def test_package_imports() -> None:
    assert pytransformkit.__version__


def test_core_import_does_not_load_optional_engines() -> None:
    forbidden_modules = {"pandas", "polars", "pyarrow", "duckdb"}
    assert forbidden_modules.isdisjoint(sys.modules)
