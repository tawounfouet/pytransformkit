from __future__ import annotations

import pytest

from pytransformkit import TransformationPlan, quality
from pytransformkit.application.execution import EngineCapabilityAnalyzer
from pytransformkit.domain.data.data_types import (
    FloatType,
    IntegerType,
    StringType,
    StructField,
    StructType,
)
from pytransformkit.domain.data.field import Field
from pytransformkit.domain.data.schema import Schema
from pytransformkit.domain.engines import EngineCapability
from pytransformkit.domain.quality import (
    ValidationPolicy,
    ValidationResult,
    ValidationRuleResult,
    ValidationSpec,
    ValidationThreshold,
)
from pytransformkit.domain.transformations.quality import QualityGate
from pytransformkit.errors.expression import ExpressionTypeError
from pytransformkit.errors.transformation import InvalidTransformationError
from pytransformkit.functions import col
from pytransformkit.planning import TransformationCompiler


@pytest.fixture
def schema() -> Schema:
    return Schema(
        fields=(
            Field("customer_id", IntegerType(), nullable=False),
            Field("email", StringType(), nullable=True),
            Field("score", FloatType(), nullable=True),
            Field(
                "profile",
                StructType(fields=(StructField("city", StringType(), nullable=False),)),
                nullable=True,
            ),
        )
    )


def test_validation_threshold_supports_count_and_rate_budgets() -> None:
    strict = ValidationThreshold()
    rate_only = ValidationThreshold(
        max_violations=None,
        max_violation_rate=0.25,
    )

    assert strict.accepts(violation_count=0, evaluated_count=10)
    assert not strict.accepts(violation_count=1, evaluated_count=10)
    assert rate_only.accepts(violation_count=2, evaluated_count=10)
    assert not rate_only.accepts(violation_count=3, evaluated_count=10)


def test_validation_result_is_structured_and_computes_failed_rule_count() -> None:
    threshold = ValidationThreshold()
    failed = ValidationRuleResult(
        rule_name="email_required",
        rule_type="quality.not_null",
        passed=False,
        violation_count=1,
        evaluated_count=3,
        threshold=threshold,
    )
    passed = ValidationRuleResult(
        rule_name="row_count",
        rule_type="quality.row_count",
        passed=True,
        violation_count=0,
        evaluated_count=1,
        threshold=threshold,
    )

    result = ValidationResult(
        gate_name="customers_quality",
        policy=ValidationPolicy.WARN_ONLY,
        passed=False,
        rule_results=(failed, passed),
    )

    assert result.failed_rule_count == 1
    assert failed.violation_rate == pytest.approx(1 / 3)


def test_public_quality_dsl_builds_portable_rules(schema: Schema) -> None:
    spec = ValidationSpec(
        name="customers_quality",
        policy=ValidationPolicy.WARN_ONLY,
        rules=(
            quality.not_null("email"),
            quality.unique("customer_id"),
            quality.range_("score", minimum=0.0, maximum=100.0),
            quality.allowed_values("customer_id", (1, 2, 3)),
            quality.regex("email", r".+@.+"),
            quality.schema(schema),
            quality.row_count(minimum=1),
            quality.expression(
                col("score") >= 0,
                name="score_non_negative",
            ),
        ),
    )

    assert len(spec.rules) == 8
    assert spec.rules[0].identifier == "quality.not_null"
    assert spec.rules[-1].identifier == "quality.expression"


def test_builder_quality_gate_preserves_schema(schema: Schema) -> None:
    builder = TransformationPlan.builder("customers")
    source = builder.input("customers", schema=schema)
    validated = builder.validate(
        "validate_customers",
        source=source,
        spec=ValidationSpec(
            name="customers_quality",
            rules=(quality.not_null("customer_id"),),
        ),
    )
    plan = builder.output("result", validated).build()

    assert validated.schema == schema
    assert isinstance(
        plan.transformation_nodes[0].transformation,
        QualityGate,
    )


def test_regex_rule_requires_string_field(schema: Schema) -> None:
    builder = TransformationPlan.builder("invalid_regex")
    source = builder.input("customers", schema=schema)

    with pytest.raises(InvalidTransformationError, match="StringType"):
        builder.validate(
            "validate",
            source=source,
            spec=ValidationSpec(
                name="invalid",
                rules=(quality.regex("score", r"\d+"),),
            ),
        )


def test_expression_rule_requires_boolean_expression(schema: Schema) -> None:
    builder = TransformationPlan.builder("invalid_expression")
    source = builder.input("customers", schema=schema)

    with pytest.raises(ExpressionTypeError, match="BooleanType"):
        builder.validate(
            "validate",
            source=source,
            spec=ValidationSpec(
                name="invalid",
                rules=(
                    quality.expression(
                        col("score") + 1,
                        name="not_boolean",
                    ),
                ),
            ),
        )


def test_quality_capabilities_include_nested_rule_dependencies(
    schema: Schema,
) -> None:
    builder = TransformationPlan.builder("nested_quality")
    source = builder.input("customers", schema=schema)
    validated = builder.validate(
        "validate",
        source=source,
        spec=ValidationSpec(
            name="nested_quality",
            rules=(quality.not_null("profile.city"),),
        ),
    )
    plan = builder.output("result", validated).build()

    required = EngineCapabilityAnalyzer().required_capabilities(
        TransformationCompiler().compile(plan)
    )

    assert EngineCapability.QUALITY in required
    assert EngineCapability.NESTED in required
