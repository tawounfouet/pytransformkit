"""Engine-neutral data-quality contracts.

Result types are imported eagerly because they are dependency-light. Rule types are
resolved lazily to avoid circular imports while Schema itself imports the public
error package.
"""

from __future__ import annotations

from typing import Any

from pytransformkit.domain.quality.results import (
    ValidationPolicy,
    ValidationResult,
    ValidationRuleResult,
    ValidationThreshold,
)

_RULE_EXPORTS = {
    "AllowedValues",
    "ExpressionValidation",
    "NotNull",
    "Range",
    "Regex",
    "RowCount",
    "SchemaValidation",
    "Unique",
    "ValidationRule",
    "ValidationSpec",
}

__all__ = [
    "AllowedValues",
    "ExpressionValidation",
    "NotNull",
    "Range",
    "Regex",
    "RowCount",
    "SchemaValidation",
    "Unique",
    "ValidationPolicy",
    "ValidationResult",
    "ValidationRule",
    "ValidationRuleResult",
    "ValidationSpec",
    "ValidationThreshold",
]


def __getattr__(name: str) -> Any:
    if name in _RULE_EXPORTS:
        from pytransformkit.domain.quality import rules

        return getattr(rules, name)
    raise AttributeError(
        f"module 'pytransformkit.domain.quality' has no attribute {name!r}"
    )
