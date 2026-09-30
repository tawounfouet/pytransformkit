"""Pandas evaluation of portable data-quality rules."""

from __future__ import annotations

from typing import Any

import pandas as pd

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
from pytransformkit.infrastructure.engines.pandas.expressions import (
    PandasExpressionCompiler,
)


class PandasQualityEvaluator:
    """Evaluate engine-neutral quality rules against one Pandas DataFrame."""

    def __init__(
        self,
        expression_compiler: PandasExpressionCompiler | None = None,
    ) -> None:
        self._expression_compiler = expression_compiler or PandasExpressionCompiler()

    def evaluate(
        self,
        spec: ValidationSpec,
        dataframe: Any,
        schema: Schema,
    ) -> ValidationResult:
        if not isinstance(dataframe, pd.DataFrame):
            raise TypeError("Pandas quality evaluation requires a DataFrame.")

        if spec.policy is ValidationPolicy.IGNORE:
            return ValidationResult(
                gate_name=spec.name,
                policy=spec.policy,
                passed=True,
                rule_results=(),
                ignored=True,
            )

        rule_results: list[ValidationRuleResult] = []
        for rule in spec.rules:
            result = self._evaluate_rule(
                rule,
                dataframe,
                schema,
            )
            rule_results.append(result)

            if spec.policy is ValidationPolicy.FAIL_FAST and not result.passed:
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

        if spec.policy is ValidationPolicy.FAIL_AT_END and not validation.passed:
            raise QualityGateError(validation)

        return validation

    def _evaluate_rule(
        self,
        rule: ValidationRule,
        dataframe: Any,
        schema: Schema,
    ) -> ValidationRuleResult:
        if isinstance(rule, NotNull):
            series = self._field(dataframe, rule.field)
            return _result(
                rule,
                violation_count=int(series.isna().sum()),
                evaluated_count=len(dataframe),
            )

        if isinstance(rule, Unique):
            columns = {
                f"field_{index}": self._field(dataframe, field)
                for index, field in enumerate(rule.fields)
            }
            keys = pd.DataFrame(columns)
            return _result(
                rule,
                violation_count=int(keys.duplicated(keep="first").sum()),
                evaluated_count=len(dataframe),
            )

        if isinstance(rule, Range):
            series = self._field(dataframe, rule.field)
            present = series.notna()
            invalid = pd.Series(False, index=dataframe.index)
            if rule.minimum is not None:
                if rule.include_minimum:
                    invalid = invalid | (present & (series < rule.minimum))
                else:
                    invalid = invalid | (present & (series <= rule.minimum))
            if rule.maximum is not None:
                if rule.include_maximum:
                    invalid = invalid | (present & (series > rule.maximum))
                else:
                    invalid = invalid | (present & (series >= rule.maximum))
            return _result(
                rule,
                violation_count=int(invalid.fillna(False).sum()),
                evaluated_count=len(dataframe),
            )

        if isinstance(rule, AllowedValues):
            series = self._field(dataframe, rule.field)
            invalid = series.notna() & ~series.isin(rule.values)
            return _result(
                rule,
                violation_count=int(invalid.fillna(False).sum()),
                evaluated_count=len(dataframe),
            )

        if isinstance(rule, Regex):
            series = self._field(dataframe, rule.field)
            present = series.notna()
            matches = series.astype("string").str.fullmatch(
                rule.pattern,
                na=False,
            )
            invalid = present & ~matches
            return _result(
                rule,
                violation_count=int(invalid.sum()),
                evaluated_count=len(dataframe),
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
            count = len(dataframe)
            valid = (rule.minimum is None or count >= rule.minimum) and (
                rule.maximum is None or count <= rule.maximum
            )
            return _result(
                rule,
                violation_count=0 if valid else 1,
                evaluated_count=1,
            )

        if isinstance(rule, ExpressionValidation):
            condition = self._expression_compiler.compile(
                rule.expression,
                dataframe,
            )
            if isinstance(condition, pd.Series):
                valid = condition.fillna(False).astype(bool)
                violations = int((~valid).sum())
            else:
                try:
                    valid_scalar = bool(condition)
                except (TypeError, ValueError):
                    valid_scalar = False
                violations = 0 if valid_scalar else len(dataframe)
            return _result(
                rule,
                violation_count=violations,
                evaluated_count=len(dataframe),
            )

        raise TypeError(f"Unsupported ValidationRule {type(rule).__name__!r}.")

    def _field(self, dataframe: Any, path: object) -> Any:
        return self._expression_compiler.compile(
            ColumnReference(path),  # type: ignore[arg-type]
            dataframe,
        )


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
