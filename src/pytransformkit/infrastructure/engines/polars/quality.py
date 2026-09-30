"""Polars evaluation of portable data-quality rules."""

from __future__ import annotations

import math
import re
from typing import Any

import polars as pl

from pytransformkit.domain.data.field_path import FieldPath
from pytransformkit.domain.data.schema import Schema
from pytransformkit.domain.expressions.references import ColumnReference
from pytransformkit.domain.quality.results import (
    ValidationPolicy,
    ValidationResult,
    ValidationRuleResult,
)
from pytransformkit.domain.quality.rules import (
    AllowedValues,
    ExpressionValidation,
    NotNull,
    Range,
    Regex,
    RowCount,
    SchemaValidation,
    Unique,
    ValidationRule,
    ValidationSpec,
)
from pytransformkit.errors.quality import QualityGateError
from pytransformkit.infrastructure.engines.polars.expressions import (
    PolarsExpressionCompiler,
)


class PolarsQualityEvaluator:
    """Evaluate engine-neutral quality rules against Polars data."""

    def __init__(
        self,
        expression_compiler: PolarsExpressionCompiler | None = None,
    ) -> None:
        self._expression_compiler = (
            expression_compiler or PolarsExpressionCompiler()
        )

    def evaluate(
        self,
        spec: ValidationSpec,
        frame: Any,
        schema: Schema,
    ) -> ValidationResult:
        if not isinstance(frame, (pl.DataFrame, pl.LazyFrame)):
            raise TypeError(
                "Polars quality evaluation requires DataFrame or LazyFrame."
            )

        if spec.policy is ValidationPolicy.IGNORE:
            return ValidationResult(
                gate_name=spec.name,
                policy=spec.policy,
                passed=True,
                rule_results=(),
                ignored=True,
            )

        materialized = frame.collect() if isinstance(frame, pl.LazyFrame) else frame
        rule_results: list[ValidationRuleResult] = []

        for rule in spec.rules:
            result = self._evaluate_rule(
                rule,
                materialized,
                schema,
            )
            rule_results.append(result)

            if (
                spec.policy is ValidationPolicy.FAIL_FAST
                and not result.passed
            ):
                validation = ValidationResult(
                    gate_name=spec.name,
                    policy=spec.policy,
                    passed=False,
                    rule_results=tuple(rule_results),
                )
                raise QualityGateError(validation)

        validation = ValidationResult(
            gate_name=spec.name,
            policy=spec.policy,
            passed=all(result.passed for result in rule_results),
            rule_results=tuple(rule_results),
        )

        if (
            spec.policy is ValidationPolicy.FAIL_AT_END
            and not validation.passed
        ):
            raise QualityGateError(validation)

        return validation

    def _evaluate_rule(
        self,
        rule: ValidationRule,
        frame: pl.DataFrame,
        schema: Schema,
    ) -> ValidationRuleResult:
        if isinstance(rule, NotNull):
            values = self._field_values(frame, rule.field)
            return _result(
                rule,
                violation_count=sum(_is_missing(value) for value in values),
                evaluated_count=len(values),
            )

        if isinstance(rule, Unique):
            columns = [
                self._field_values(frame, field)
                for field in rule.fields
            ]
            seen: set[tuple[object, ...]] = set()
            duplicates = 0
            for values in zip(*columns, strict=True):
                key = tuple(_hashable(value) for value in values)
                if key in seen:
                    duplicates += 1
                else:
                    seen.add(key)
            return _result(
                rule,
                violation_count=duplicates,
                evaluated_count=frame.height,
            )

        if isinstance(rule, Range):
            values = self._field_values(frame, rule.field)
            violations = 0
            for value in values:
                if _is_missing(value):
                    continue
                if rule.minimum is not None:
                    if rule.include_minimum and value < rule.minimum:
                        violations += 1
                        continue
                    if not rule.include_minimum and value <= rule.minimum:
                        violations += 1
                        continue
                if rule.maximum is not None:
                    if rule.include_maximum and value > rule.maximum:
                        violations += 1
                        continue
                    if not rule.include_maximum and value >= rule.maximum:
                        violations += 1
            return _result(
                rule,
                violation_count=violations,
                evaluated_count=len(values),
            )

        if isinstance(rule, AllowedValues):
            values = self._field_values(frame, rule.field)
            violations = sum(
                not _is_missing(value) and value not in rule.values
                for value in values
            )
            return _result(
                rule,
                violation_count=violations,
                evaluated_count=len(values),
            )

        if isinstance(rule, Regex):
            values = self._field_values(frame, rule.field)
            matcher = re.compile(rule.pattern)
            violations = sum(
                not _is_missing(value)
                and matcher.fullmatch(str(value)) is None
                for value in values
            )
            return _result(
                rule,
                violation_count=violations,
                evaluated_count=len(values),
            )

        if isinstance(rule, SchemaValidation):
            matches = _schema_matches(
                actual=schema,
                expected=rule.expected_schema,
                exact=rule.exact,
            )
            return _result(
                rule,
                violation_count=0 if matches else 1,
                evaluated_count=1,
            )

        if isinstance(rule, RowCount):
            count = frame.height
            valid = (
                (rule.minimum is None or count >= rule.minimum)
                and (rule.maximum is None or count <= rule.maximum)
            )
            return _result(
                rule,
                violation_count=0 if valid else 1,
                evaluated_count=1,
            )

        if isinstance(rule, ExpressionValidation):
            expression = self._expression_compiler.compile(
                rule.expression,
                frame,
            )
            values = frame.select(
                expression.alias("__pytransformkit_quality_condition__")
            ).to_series().to_list()
            violations = sum(value is not True for value in values)
            return _result(
                rule,
                violation_count=violations,
                evaluated_count=len(values),
            )

        raise TypeError(f"Unsupported ValidationRule {type(rule).__name__!r}.")

    def _field_values(
        self,
        frame: pl.DataFrame,
        path: FieldPath,
    ) -> list[object]:
        expression = self._expression_compiler.compile(
            ColumnReference(path),
            frame,
        )
        return frame.select(
            expression.alias("__pytransformkit_quality_value__")
        ).to_series().to_list()


def _result(
    rule: ValidationRule,
    *,
    violation_count: int,
    evaluated_count: int,
) -> ValidationRuleResult:
    threshold = rule.threshold  # type: ignore[attr-defined]
    return ValidationRuleResult(
        rule_name=rule.name,  # type: ignore[attr-defined]
        rule_type=rule.identifier,
        passed=threshold.accepts(
            violation_count=violation_count,
            evaluated_count=evaluated_count,
        ),
        violation_count=violation_count,
        evaluated_count=evaluated_count,
        threshold=threshold,
    )


def _schema_matches(
    *,
    actual: Schema,
    expected: Schema,
    exact: bool,
) -> bool:
    if exact:
        return actual == expected

    for expected_field in expected.fields:
        if not actual.has_field(expected_field.name):
            return False
        if actual.field(expected_field.name) != expected_field:
            return False
    return True


def _is_missing(value: object) -> bool:
    return value is None or (
        isinstance(value, float)
        and math.isnan(value)
    )


def _hashable(value: object) -> object:
    if isinstance(value, dict):
        return tuple(
            sorted(
                (key, _hashable(item))
                for key, item in value.items()
            )
        )
    if isinstance(value, list):
        return tuple(_hashable(item) for item in value)
    if isinstance(value, float) and math.isnan(value):
        return ("__nan__",)
    return value
