"""Public versioned codecs for portable PyTransformKit contracts."""

from __future__ import annotations

from pytransformkit.application.planning import (
    TransformationCompiler,
    logical_plan_fingerprint,
)
from pytransformkit.domain.data.data_types import DataType
from pytransformkit.domain.data.field import Field
from pytransformkit.domain.data.schema import Schema
from pytransformkit.domain.expressions import Expression, expression_fingerprint
from pytransformkit.domain.lineage import TransformationLineage
from pytransformkit.domain.pipelines.plan import LogicalPlan
from pytransformkit.domain.plans import TransformationPlan
from pytransformkit.domain.resources import ResourceReference
from pytransformkit.domain.runtime import Diagnostic, ExecutionManifest
from pytransformkit.domain.runtime.references import (
    TransformationExecutionReference,
)
from pytransformkit.domain.shared.fingerprint import Fingerprint
from pytransformkit.serialization.codec import ContractCodec


class DataTypeCodec(ContractCodec[DataType]):
    contract = "pytransformkit.data_type"
    python_type = DataType


class FieldCodec(ContractCodec[Field]):
    contract = "pytransformkit.field"
    python_type = Field


class SchemaCodec(ContractCodec[Schema]):
    contract = "pytransformkit.schema"
    python_type = Schema


class ExpressionCodec(ContractCodec[Expression]):
    contract = "pytransformkit.expression"
    python_type = Expression

    def fingerprint(self, value: Expression) -> Fingerprint:
        self._validate_python_type(value)
        return expression_fingerprint(value)


class TransformationPlanCodec(ContractCodec[TransformationPlan]):
    contract = "pytransformkit.transformation_plan"
    python_type = TransformationPlan

    def fingerprint(self, value: TransformationPlan) -> Fingerprint:
        self._validate_python_type(value)
        logical_plan = TransformationCompiler().compile(value)
        return logical_plan_fingerprint(logical_plan)


class LogicalPlanCodec(ContractCodec[LogicalPlan]):
    contract = "pytransformkit.logical_plan"
    python_type = LogicalPlan

    def fingerprint(self, value: LogicalPlan) -> Fingerprint:
        self._validate_python_type(value)
        return logical_plan_fingerprint(value)


class ResourceReferenceCodec(ContractCodec[ResourceReference]):
    contract = "pykit.resource_reference"
    python_type = ResourceReference


class TransformationExecutionReferenceCodec(
    ContractCodec[TransformationExecutionReference]
):
    contract = "pykit.transformation_execution_reference"
    python_type = TransformationExecutionReference


class LineageCodec(ContractCodec[TransformationLineage]):
    contract = "pytransformkit.transformation_lineage"
    python_type = TransformationLineage


class DiagnosticCodec(ContractCodec[Diagnostic]):
    contract = "pytransformkit.diagnostic"
    python_type = Diagnostic


class ExecutionManifestCodec(ContractCodec[ExecutionManifest]):
    contract = "pytransformkit.execution_manifest"
    python_type = ExecutionManifest
