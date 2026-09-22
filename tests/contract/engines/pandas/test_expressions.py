from __future__ import annotations

import pytest

pd = pytest.importorskip("pandas")

from pytransformkit.functions import col, concat, lit, lower, trim
from pytransformkit.infrastructure.engines.pandas import (
    PandasExpressionCompiler,
)


def test_string_expression_compiles_without_engine_types_in_ast() -> None:
    dataframe = pd.DataFrame(
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

    result = PandasExpressionCompiler().compile(
        expression,
        dataframe,
    )

    assert result.tolist() == ["ada Lovelace", "grace Hopper"]


def test_trim_preserves_missing_values() -> None:
    dataframe = pd.DataFrame(
        {
            "email": pd.Series(
                ["  A@EXAMPLE.COM ", None],
                dtype="string",
            )
        }
    )
    expression = lower(trim(col("email")))

    result = PandasExpressionCompiler().compile(
        expression,
        dataframe,
    )

    assert result.iloc[0] == "a@example.com"
    assert pd.isna(result.iloc[1])


def test_comparison_with_null_literal_yields_unknown() -> None:
    dataframe = pd.DataFrame({"email": ["a", None]})
    expression = col("email") == lit(None)

    result = PandasExpressionCompiler().compile(
        expression,
        dataframe,
    )

    assert str(result.dtype) == "boolean"
    assert result.isna().all()


def test_boolean_expression_uses_vectorized_pandas_semantics() -> None:
    dataframe = pd.DataFrame(
        {
            "amount": [10.0, -1.0, 5.0],
            "active": [True, True, False],
        }
    )
    expression = (col("amount") > 0) & col("active")

    result = PandasExpressionCompiler().compile(
        expression,
        dataframe,
    )

    assert result.tolist() == [True, False, False]
