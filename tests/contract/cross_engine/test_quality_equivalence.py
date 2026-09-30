# ruff: noqa: E402

from __future__ import annotations

import pytest

pd = pytest.importorskip("pandas")
pl = pytest.importorskip("polars")

from pytransformkit import (
    InputBinding,
    TransformationPlan,
    TransformationRuntime,
    quality,
)
from pytransformkit.adapters.pandas import PandasEngineAdapter
from pytransformkit.adapters.polars import PolarsEngineAdapter
from pytransformkit.domain.data.data_types import (
    FloatType,
    IntegerType,
    StringType,
)
from pytransformkit.domain.data.field import Field
from pytransformkit.domain.data.schema import Schema
from pytransformkit.domain.quality import (
    ValidationPolicy,
    ValidationSpec,
    ValidationThreshold,
)
from pytransformkit.engines import EngineRegistry
from pytransformkit.errors import QualityGateError
from pytransformkit.functions import col
from pytransformkit.runtime import ExecutionMode


def _schema() -> Schema:
    return Schema(
        fields=(
            Field("customer_id", IntegerType(), nullable=False),
            Field("email", StringType(), nullable=True),
            Field("status", StringType(), nullable=False),
            Field("score", FloatType(), nullable=True),
        )
    )


def _records() -> list[dict[str, object]]:
    return [
        {
            "customer_id": 1,
            "email": "alice@example.com",
            "status": "ACTIVE",
            "score": 10.0,
        },
        {
            "customer_id": 2,
            "email": "invalid",
            "status": "UNKNOWN",
            "score": 120.0,
        },
        {
            "customer_id": 2,
            "email": None,
            "status": "ACTIVE",
            "score": None,
        },
    ]


def _runtime(adapter: object) -> TransformationRuntime:
    registry = EngineRegistry()
    registry.register(adapter)  # type: ignore[arg-type]
    return TransformationRuntime(engines=registry)


def _spec(policy: ValidationPolicy) -> ValidationSpec:
    return ValidationSpec(
        name="customers_quality",
        policy=policy,
        rules=(
            quality.not_null(
                "email",
                name="email_required",
            ),
            quality.unique(
                "customer_id",
                name="customer_id_unique",
            ),
            quality.range_(
                "score",
                minimum=0.0,
                maximum=100.0,
                name="score_range",
            ),
            quality.allowed_values(
                "status",
                ("ACTIVE", "INACTIVE"),
                name="status_domain",
                threshold=ValidationThreshold(
                    max_violations=None,
                    max_violation_rate=0.34,
                ),
            ),
            quality.regex(
                "email",
                r"[^@]+@[^@]+\.[^@]+",
                name="email_shape",
            ),
            quality.schema(
                _schema(),
                name="logical_schema",
            ),
            quality.row_count(
                minimum=3,
                maximum=3,
                name="expected_rows",
            ),
            quality.expression(
                col("score") >= 0,
                name="score_non_negative",
            ),
        ),
    )


def _plan(policy: ValidationPolicy) -> TransformationPlan:
    builder = TransformationPlan.builder("quality_customers")
    customers = builder.input("customers", schema=_schema())
    validated = builder.validate(
        "validate_customers",
        source=customers,
        spec=_spec(policy),
    )
    return builder.output("result", validated).build()


def _execute(
    *,
    engine: str,
    adapter: object,
    policy: ValidationPolicy,
    mode: ExecutionMode = ExecutionMode.EAGER,
):
    native: object
    if engine == "pandas":
        native = pd.DataFrame(_records())
    else:
        frame = pl.DataFrame(_records())
        native = frame.lazy() if mode is ExecutionMode.LAZY else frame

    return _runtime(adapter).execute(
        _plan(policy),
        engine=engine,
        inputs={
            "customers": InputBinding.from_native(
                "customers",
                native,
                engine=engine,
            )
        },
        mode=mode,
    )


def _normalized_output(result: object) -> list[dict[str, object]]:
    handle = result.output_handle  # type: ignore[attr-defined]
    if hasattr(handle, "dataframe"):
        return handle.dataframe.to_dict(orient="records")
    frame = handle.frame
    if isinstance(frame, pl.LazyFrame):
        frame = frame.collect()
    return frame.to_dicts()


def test_warn_only_quality_evidence_matches_pandas_and_polars() -> None:
    pandas_result = _execute(
        engine="pandas",
        adapter=PandasEngineAdapter(),
        policy=ValidationPolicy.WARN_ONLY,
    )
    polars_result = _execute(
        engine="polars",
        adapter=PolarsEngineAdapter(),
        policy=ValidationPolicy.WARN_ONLY,
    )

    assert pandas_result.validations == polars_result.validations
    validation = pandas_result.validation("customers_quality")

    assert validation.passed is False
    assert validation.failed_rule_count == 5

    by_name = {
        item.rule_name: item
        for item in validation.rule_results
    }
    assert by_name["email_required"].violation_count == 1
    assert by_name["customer_id_unique"].violation_count == 1
    assert by_name["score_range"].violation_count == 1
    assert by_name["status_domain"].violation_count == 1
    assert by_name["status_domain"].passed is True
    assert by_name["email_shape"].violation_count == 1
    assert by_name["logical_schema"].passed is True
    assert by_name["expected_rows"].passed is True
    assert by_name["score_non_negative"].violation_count == 1

    assert _normalized_output(pandas_result) == _records()
    assert _normalized_output(polars_result) == _records()


@pytest.mark.parametrize(
    ("engine", "adapter"),
    [
        ("pandas", PandasEngineAdapter()),
        ("polars", PolarsEngineAdapter()),
    ],
)
def test_fail_fast_raises_structured_quality_error(
    engine: str,
    adapter: object,
) -> None:
    with pytest.raises(QualityGateError) as captured:
        _execute(
            engine=engine,
            adapter=adapter,
            policy=ValidationPolicy.FAIL_FAST,
        )

    result = captured.value.result
    assert result.gate_name == "customers_quality"
    assert result.passed is False
    assert len(result.rule_results) == 1
    assert result.rule_results[0].rule_name == "email_required"


@pytest.mark.parametrize(
    ("engine", "adapter"),
    [
        ("pandas", PandasEngineAdapter()),
        ("polars", PolarsEngineAdapter()),
    ],
)
def test_fail_at_end_reports_all_rules_before_rejecting(
    engine: str,
    adapter: object,
) -> None:
    with pytest.raises(QualityGateError) as captured:
        _execute(
            engine=engine,
            adapter=adapter,
            policy=ValidationPolicy.FAIL_AT_END,
        )

    result = captured.value.result
    assert result.passed is False
    assert len(result.rule_results) == 8
    assert result.failed_rule_count == 5


@pytest.mark.parametrize(
    ("engine", "adapter"),
    [
        ("pandas", PandasEngineAdapter()),
        ("polars", PolarsEngineAdapter()),
    ],
)
def test_ignore_policy_skips_rule_evaluation(
    engine: str,
    adapter: object,
) -> None:
    result = _execute(
        engine=engine,
        adapter=adapter,
        policy=ValidationPolicy.IGNORE,
    )

    validation = result.validation("customers_quality")
    assert validation.ignored is True
    assert validation.passed is True
    assert validation.rule_results == ()


def test_polars_lazy_quality_gate_returns_real_evidence() -> None:
    result = _execute(
        engine="polars",
        adapter=PolarsEngineAdapter(),
        policy=ValidationPolicy.WARN_ONLY,
        mode=ExecutionMode.LAZY,
    )

    assert result.validation("customers_quality").failed_rule_count == 5
    assert isinstance(result.output_handle.frame, pl.LazyFrame)
    assert result.output_handle.frame.collect().height == 3
