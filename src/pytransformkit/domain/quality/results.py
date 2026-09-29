"""Engine-neutral data-quality result and policy model."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ValidationPolicy(StrEnum):
    """How a QualityGate reacts to violated rules."""

    FAIL_FAST = "fail_fast"
    FAIL_AT_END = "fail_at_end"
    WARN_ONLY = "warn_only"
    IGNORE = "ignore"


@dataclass(frozen=True, slots=True)
class ValidationThreshold:
    """Maximum violation budget accepted by one validation rule."""

    max_violations: int = 0
    max_violation_rate: float | None = None

    def __post_init__(self) -> None:
        if (
            not isinstance(self.max_violations, int)
            or isinstance(self.max_violations, bool)
            or self.max_violations < 0
        ):
            raise ValueError("max_violations must be a non-negative integer.")
        if self.max_violation_rate is not None and not (
            0.0 <= self.max_violation_rate <= 1.0
        ):
            raise ValueError("max_violation_rate must be between 0.0 and 1.0.")

    def accepts(
        self,
        *,
        violation_count: int,
        evaluated_count: int,
    ) -> bool:
        """Return whether the observed violations remain within this budget."""
        if violation_count < 0 or evaluated_count < 0:
            raise ValueError("Validation counts must be non-negative.")
        if violation_count > evaluated_count:
            raise ValueError("violation_count must not exceed evaluated_count.")

        if violation_count > self.max_violations:
            return False

        if self.max_violation_rate is None:
            return True

        violation_rate = (
            0.0
            if evaluated_count == 0
            else violation_count / evaluated_count
        )
        return violation_rate <= self.max_violation_rate


@dataclass(frozen=True, slots=True)
class ValidationRuleResult:
    """Structured evidence produced by one validation rule."""

    rule_name: str
    rule_type: str
    passed: bool
    violation_count: int
    evaluated_count: int
    threshold: ValidationThreshold

    def __post_init__(self) -> None:
        if not self.rule_name or not self.rule_name.strip():
            raise ValueError("Validation rule result name must not be empty.")
        if not self.rule_type or not self.rule_type.strip():
            raise ValueError("Validation rule result type must not be empty.")
        if self.violation_count < 0 or self.evaluated_count < 0:
            raise ValueError("Validation result counts must be non-negative.")
        if self.violation_count > self.evaluated_count:
            raise ValueError(
                "Validation result violation_count must not exceed evaluated_count."
            )
        expected = self.threshold.accepts(
            violation_count=self.violation_count,
            evaluated_count=self.evaluated_count,
        )
        if self.passed is not expected:
            raise ValueError(
                "Validation result passed flag must match its threshold."
            )

    @property
    def violation_rate(self) -> float:
        if self.evaluated_count == 0:
            return 0.0
        return self.violation_count / self.evaluated_count


@dataclass(frozen=True, slots=True)
class ValidationResult:
    """Structured result for one executed QualityGate."""

    gate_name: str
    policy: ValidationPolicy
    passed: bool
    rule_results: tuple[ValidationRuleResult, ...]
    ignored: bool = False

    def __post_init__(self) -> None:
        if not self.gate_name or not self.gate_name.strip():
            raise ValueError("ValidationResult gate_name must not be empty.")
        if not isinstance(self.policy, ValidationPolicy):
            raise TypeError("ValidationResult policy must be a ValidationPolicy.")
        if not isinstance(self.rule_results, tuple):
            raise TypeError("ValidationResult rule_results must be a tuple.")
        if any(
            not isinstance(result, ValidationRuleResult)
            for result in self.rule_results
        ):
            raise TypeError(
                "ValidationResult rule_results must contain ValidationRuleResult."
            )
        if self.ignored:
            if self.policy is not ValidationPolicy.IGNORE:
                raise ValueError(
                    "Only IGNORE validation policy may produce an ignored result."
                )
            if self.rule_results:
                raise ValueError("Ignored validation results must not evaluate rules.")
            if not self.passed:
                raise ValueError("Ignored validation results are non-blocking.")
        elif self.passed is not all(
            result.passed for result in self.rule_results
        ):
            raise ValueError(
                "ValidationResult passed flag must match its rule results."
            )

    @property
    def failed_rule_count(self) -> int:
        return sum(not result.passed for result in self.rule_results)
