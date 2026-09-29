from __future__ import annotations

from pytransformkit import TransformationPlan
from pytransformkit import functions as fn
from pytransformkit.application.execution import EngineCapabilityAnalyzer
from pytransformkit.domain.data.data_types import (
    DateType,
    DurationType,
    IntegerType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)
from pytransformkit.domain.data.field import Field
from pytransformkit.domain.data.schema import Schema
from pytransformkit.domain.engines import EngineCapability
from pytransformkit.domain.expressions.typing import ExpressionTypeResolver
from pytransformkit.errors.expression import ExpressionTypeError
from pytransformkit.functions import col
from pytransformkit.planning import TransformationCompiler


def _schema() -> Schema:
    return Schema(
        fields=(
            Field(
                "profile",
                StructType(
                    fields=(
                        StructField("city", StringType(), nullable=False),
                    )
                ),
                nullable=True,
            ),
            Field(
                "event_at",
                TimestampType(unit="us", timezone="UTC"),
                nullable=False,
            ),
            Field(
                "previous_at",
                TimestampType(unit="us", timezone="UTC"),
                nullable=True,
            ),
            Field(
                "naive_at",
                TimestampType(unit="us"),
                nullable=False,
            ),
            Field("event_date", DateType(), nullable=False),
        )
    )


def test_nested_column_reference_uses_struct_path_type() -> None:
    resolved = ExpressionTypeResolver().resolve(
        col("profile.city"),
        _schema(),
    )

    assert resolved.data_type == StringType()
    assert resolved.nullable is True


def test_temporal_extractors_have_stable_int32_types() -> None:
    resolved = ExpressionTypeResolver().resolve(
        fn.year(col("event_at")),
        _schema(),
    )

    assert resolved.data_type == IntegerType(bits=32)
    assert resolved.nullable is False


def test_timestamp_normalization_declares_target_unit_and_timezone() -> None:
    resolved = ExpressionTypeResolver().resolve(
        fn.normalize_timestamp(
            col("event_at"),
            timezone="Europe/Paris",
            unit="ms",
        ),
        _schema(),
    )

    assert resolved.data_type == TimestampType(
        unit="ms",
        timezone="Europe/Paris",
    )


def test_timezone_conversion_requires_aware_timestamp() -> None:
    try:
        ExpressionTypeResolver().resolve(
            fn.convert_timezone(
                col("naive_at"),
                "Europe/Paris",
            ),
            _schema(),
        )
    except ExpressionTypeError as error:
        assert "timezone-aware" in str(error)
    else:
        raise AssertionError("Expected timezone-aware validation failure.")


def test_duration_between_has_explicit_duration_unit() -> None:
    resolved = ExpressionTypeResolver().resolve(
        fn.duration_between(
            col("previous_at"),
            col("event_at"),
            unit="s",
        ),
        _schema(),
    )

    assert resolved.data_type == DurationType(unit="s")
    assert resolved.nullable is True


def test_date_extraction_preserves_date_type() -> None:
    resolved = ExpressionTypeResolver().resolve(
        fn.to_date(col("event_at")),
        _schema(),
    )

    assert resolved.data_type == DateType()


def test_capability_analysis_detects_nested_temporal_and_duration_semantics() -> None:
    builder = TransformationPlan.builder("temporal_nested")
    source = builder.input("source", schema=_schema())

    nested = builder.derive(
        "nested",
        source=source,
        field_name="city",
        expression=col("profile.city"),
    )
    temporal = builder.derive(
        "temporal",
        source=nested,
        field_name="event_year",
        expression=fn.year(col("event_at")),
    )
    duration = builder.derive(
        "duration",
        source=temporal,
        field_name="elapsed",
        expression=fn.duration_between(
            col("previous_at"),
            col("event_at"),
            unit="s",
        ),
    )
    plan = builder.output("result", duration).build()

    required = EngineCapabilityAnalyzer().required_capabilities(
        TransformationCompiler().compile(plan)
    )

    assert EngineCapability.DERIVE in required
    assert EngineCapability.NESTED in required
    assert EngineCapability.TEMPORAL in required
    assert EngineCapability.DURATION in required
