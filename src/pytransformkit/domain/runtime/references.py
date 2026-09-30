"""Portable references to PyTransformKit runtime executions."""

from __future__ import annotations

from dataclasses import dataclass

from pytransformkit.domain.resources import ResourceReference
from pytransformkit.domain.runtime.execution import TransformationExecution
from pytransformkit.domain.shared.fingerprint import Fingerprint
from pytransformkit.domain.shared.identifiers import TransformationExecutionId


@dataclass(frozen=True, slots=True)
class TransformationExecutionReference:
    """Minimal cross-boundary reference to one transformation execution."""

    transformation_execution_id: TransformationExecutionId
    transformation_plan_fingerprint: Fingerprint | None = None
    engine_id: str | None = None
    output_reference: ResourceReference | None = None
    namespace: str = "pytransformkit.execution"

    def __post_init__(self) -> None:
        if not isinstance(
            self.transformation_execution_id,
            TransformationExecutionId,
        ):
            raise TypeError(
                "transformation_execution_id must be a TransformationExecutionId."
            )
        if self.transformation_plan_fingerprint is not None and not isinstance(
            self.transformation_plan_fingerprint, Fingerprint
        ):
            raise TypeError("transformation_plan_fingerprint must be a Fingerprint.")
        if self.engine_id is not None and not self.engine_id.strip():
            raise ValueError("engine_id must not be blank.")
        if self.output_reference is not None and not isinstance(
            self.output_reference,
            ResourceReference,
        ):
            raise TypeError("output_reference must be a ResourceReference.")
        if not self.namespace or not self.namespace.strip():
            raise ValueError("namespace must not be empty.")

    @classmethod
    def from_execution(
        cls,
        execution: TransformationExecution,
        *,
        output_reference: ResourceReference | None = None,
    ) -> TransformationExecutionReference:
        """Create a portable reference without retaining runtime-only evidence."""
        if not isinstance(execution, TransformationExecution):
            raise TypeError("execution must be a TransformationExecution.")
        return cls(
            transformation_execution_id=execution.execution_id,
            transformation_plan_fingerprint=execution.plan_fingerprint,
            engine_id=execution.engine.id if execution.engine is not None else None,
            output_reference=output_reference,
        )
