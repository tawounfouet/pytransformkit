from __future__ import annotations

from pytransformkit.domain.expressions.fingerprint import (
    canonical_expression,
    expression_fingerprint,
)
from pytransformkit.functions import col, lower


def test_equal_expression_shapes_have_same_fingerprint() -> None:
    left = lower(col("email")) == "test@example.com"
    right = lower(col("email")) == "test@example.com"

    assert expression_fingerprint(left) == expression_fingerprint(right)
    assert left.structurally_equals(right)


def test_different_expression_shapes_have_different_fingerprints() -> None:
    left = col("amount") > 0
    right = col("amount") >= 0

    assert expression_fingerprint(left) != expression_fingerprint(right)
    assert left.structurally_equals(right) is False


def test_canonical_expression_is_deterministic() -> None:
    expression = (col("amount") > 0) & col("customer_id").is_not_null()

    assert canonical_expression(expression) == canonical_expression(expression)
