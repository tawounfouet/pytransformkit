# ruff: noqa: E402

from __future__ import annotations

import pytest

pl = pytest.importorskip("polars")

from pytransformkit.functions import col, concat, lit, lower, trim
from pytransformkit.infrastructure.engines.polars import (
    PolarsExpressionCompiler,
)


def _evaluate(expression, frame):
    compiled = PolarsExpressionCompiler().compile(expression, frame)
    return frame.select(compiled.alias("value"))["value"]


def test_string_functions_compile_to_polars_expr() -> None:
    frame = pl.DataFrame(
        {
            "first_name": ["Ada", "Grace"],
            "last_name": ["Lovelace", "Hopper"],
        }
    )
    expression = concat(
        lower(col("first_name")),
        " ",
        col("last_name"),
    )

    result = _evaluate(expression, frame)

    assert result.to_list() == ["ada Lovelace", "grace Hopper"]


def test_trim_and_lower_preserve_null() -> None:
    frame = pl.DataFrame(
        {
            "email": ["  A@EXAMPLE.COM ", None],
        }
    )
    expression = lower(trim(col("email")))

    result = _evaluate(expression, frame)

    assert result.to_list() == ["a@example.com", None]


def test_comparison_with_null_literal_yields_unknown() -> None:
    frame = pl.DataFrame({"email": ["a", None]})
    expression = col("email") == lit(None)

    result = _evaluate(expression, frame)

    assert result.dtype == pl.Boolean
    assert result.to_list() == [None, None]


def test_boolean_expression_uses_vectorized_semantics() -> None:
    frame = pl.DataFrame(
        {
            "amount": [10.0, -1.0, 5.0],
            "active": [True, True, False],
        }
    )
    expression = (col("amount") > 0) & col("active")

    result = _evaluate(expression, frame)

    assert result.to_list() == [True, False, False]
