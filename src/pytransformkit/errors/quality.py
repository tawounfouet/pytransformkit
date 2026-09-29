"""Data-quality related PyTransformKit errors."""

from typing import ClassVar

from pytransformkit.domain.quality.results import ValidationResult
from pytransformkit.errors.base import PyTransformKitError
from pytransformkit.errors.codes import ErrorCode


class QualityError(PyTransformKitError):
    """Base class for data-quality failures."""

    error_code: ClassVar[ErrorCode] = ErrorCode("PTK-QUALITY-000")


class InvalidValidationError(QualityError):
    """Raised when a validation definition is semantically invalid."""

    error_code: ClassVar[ErrorCode] = ErrorCode("PTK-QUALITY-001")


class QualityGateError(QualityError):
    """Raised when a blocking QualityGate rejects data."""

    error_code: ClassVar[ErrorCode] = ErrorCode("PTK-QUALITY-002")

    def __init__(self, result: ValidationResult) -> None:
        if not isinstance(result, ValidationResult):
            raise TypeError("QualityGateError result must be a ValidationResult.")
        self.result = result
        failed = ", ".join(
            item.rule_name
            for item in result.rule_results
            if not item.passed
        )
        super().__init__(
            f"QualityGate {result.gate_name!r} failed"
            + (f": {failed}." if failed else ".")
        )
