"""Base exception for PyTransformKit."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from pytransformkit.errors.codes import ErrorCode

if TYPE_CHECKING:
    from pytransformkit.domain.runtime import (
        Diagnostic,
        ExecutionManifest,
        FailureEvidence,
        TransformationExecution,
    )


class PyTransformKitError(Exception):
    """Root exception for all expected PyTransformKit failures."""

    error_code: ClassVar[ErrorCode] = ErrorCode("PTK-CORE-000")

    def __init__(self, *args: object) -> None:
        super().__init__(*args)
        self.execution: TransformationExecution | None = None
        self.failure_evidence: FailureEvidence | None = None
        self.execution_manifest: ExecutionManifest | None = None
        self.diagnostics: tuple[Diagnostic, ...] = ()

    @property
    def code(self) -> ErrorCode:
        """Return the stable machine-readable error code."""
        return self.error_code

    def attach_runtime_evidence(
        self,
        *,
        execution: TransformationExecution,
        failure_evidence: FailureEvidence,
        manifest: ExecutionManifest,
        diagnostics: tuple[Diagnostic, ...],
    ) -> PyTransformKitError:
        """Attach structured execution evidence without changing error identity."""
        self.execution = execution
        self.failure_evidence = failure_evidence
        self.execution_manifest = manifest
        self.diagnostics = diagnostics
        return self
