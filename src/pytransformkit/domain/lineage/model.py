"""Engine-neutral logical and field-lineage contracts."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from pytransformkit.domain.data.field_path import FieldPath
from pytransformkit.domain.data.references import DatasetReference
from pytransformkit.domain.resources import ResourceReference
from pytransformkit.domain.shared.identifiers import (
    StepId,
    TransformationPlanId,
)


class LineageConfidence(StrEnum):
    """Confidence attached to one lineage assertion."""

    EXACT = "exact"
    DECLARED = "declared"
    INFERRED = "inferred"
    PARTIAL = "partial"
    UNKNOWN = "unknown"


class FieldDerivationKind(StrEnum):
    """How one output field is semantically derived from an input field."""

    DIRECT = "direct"
    RENAMED = "renamed"
    CAST = "cast"
    DERIVED = "derived"
    AGGREGATED = "aggregated"
    WINDOWED = "windowed"
    RESHAPED = "reshaped"
    EXPLODED = "exploded"
    FLATTENED = "flattened"
    SET_COMBINED = "set_combined"


class FieldDependencyKind(StrEnum):
    """Non-value field dependency affecting rows, grouping, order, or checks."""

    FILTER = "filter"
    GROUPING = "grouping"
    JOIN = "join"
    ORDERING = "ordering"
    WINDOW = "window"
    WINDOW_PARTITION = "window_partition"
    WINDOW_ORDERING = "window_ordering"
    DEDUPLICATION = "deduplication"
    DISTINCT = "distinct"
    QUALITY = "quality"
    PIVOT = "pivot"
    SET_MEMBERSHIP = "set_membership"


class ResourceLineageRole(StrEnum):
    """Role played by a portable physical resource in lineage."""

    INPUT = "input"
    OUTPUT = "output"


@dataclass(frozen=True, slots=True)
class FieldReference:
    """Portable reference to one logical field within one logical Dataset."""

    dataset: DatasetReference
    field_path: FieldPath

    def __post_init__(self) -> None:
        if not isinstance(self.dataset, DatasetReference):
            raise TypeError("FieldReference dataset must be a DatasetReference.")
        if not isinstance(self.field_path, FieldPath):
            raise TypeError("FieldReference field_path must be a FieldPath.")

    @classmethod
    def of(
        cls,
        dataset: DatasetReference,
        field: str | FieldPath,
    ) -> FieldReference:
        return cls(
            dataset=dataset,
            field_path=field if isinstance(field, FieldPath) else FieldPath.of(field),
        )


@dataclass(frozen=True, slots=True)
class DatasetLineageEdge:
    """One logical dataset derivation edge produced by a transformation step."""

    source: DatasetReference
    target: DatasetReference
    operation: str
    step_id: StepId
    confidence: LineageConfidence = LineageConfidence.EXACT

    def __post_init__(self) -> None:
        if not isinstance(self.source, DatasetReference):
            raise TypeError("DatasetLineageEdge source must be a DatasetReference.")
        if not isinstance(self.target, DatasetReference):
            raise TypeError("DatasetLineageEdge target must be a DatasetReference.")
        if not self.operation or not self.operation.strip():
            raise ValueError("DatasetLineageEdge operation must not be empty.")
        if not isinstance(self.step_id, StepId):
            raise TypeError("DatasetLineageEdge step_id must be a StepId.")
        if not isinstance(self.confidence, LineageConfidence):
            raise TypeError(
                "DatasetLineageEdge confidence must be a LineageConfidence."
            )


@dataclass(frozen=True, slots=True)
class FieldLineageEdge:
    """One field-level value-derivation edge."""

    source: FieldReference
    target: FieldReference
    derivation: FieldDerivationKind
    step_id: StepId
    confidence: LineageConfidence = LineageConfidence.EXACT

    def __post_init__(self) -> None:
        if not isinstance(self.source, FieldReference):
            raise TypeError("FieldLineageEdge source must be a FieldReference.")
        if not isinstance(self.target, FieldReference):
            raise TypeError("FieldLineageEdge target must be a FieldReference.")
        if not isinstance(self.derivation, FieldDerivationKind):
            raise TypeError(
                "FieldLineageEdge derivation must be a FieldDerivationKind."
            )
        if not isinstance(self.step_id, StepId):
            raise TypeError("FieldLineageEdge step_id must be a StepId.")
        if not isinstance(self.confidence, LineageConfidence):
            raise TypeError(
                "FieldLineageEdge confidence must be a LineageConfidence."
            )


@dataclass(frozen=True, slots=True)
class FieldDependency:
    """One operational field dependency for a transformation step."""

    field: FieldReference
    target_dataset: DatasetReference
    kind: FieldDependencyKind
    step_id: StepId
    confidence: LineageConfidence = LineageConfidence.EXACT

    def __post_init__(self) -> None:
        if not isinstance(self.field, FieldReference):
            raise TypeError("FieldDependency field must be a FieldReference.")
        if not isinstance(self.target_dataset, DatasetReference):
            raise TypeError(
                "FieldDependency target_dataset must be a DatasetReference."
            )
        if not isinstance(self.kind, FieldDependencyKind):
            raise TypeError("FieldDependency kind must be a FieldDependencyKind.")
        if not isinstance(self.step_id, StepId):
            raise TypeError("FieldDependency step_id must be a StepId.")
        if not isinstance(self.confidence, LineageConfidence):
            raise TypeError("FieldDependency confidence must be a LineageConfidence.")


@dataclass(frozen=True, slots=True)
class ResourceLineageLink:
    """Link one logical Dataset to a portable physical ResourceReference."""

    name: str
    dataset: DatasetReference
    resource: ResourceReference
    role: ResourceLineageRole

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("ResourceLineageLink name must not be empty.")
        if not isinstance(self.dataset, DatasetReference):
            raise TypeError("ResourceLineageLink dataset must be a DatasetReference.")
        if not isinstance(self.resource, ResourceReference):
            raise TypeError("ResourceLineageLink resource must be a ResourceReference.")
        if not isinstance(self.role, ResourceLineageRole):
            raise TypeError("ResourceLineageLink role must be a ResourceLineageRole.")


@dataclass(frozen=True, slots=True)
class TransformationLineage:
    """Immutable PyTransformKit-owned logical lineage projection."""

    plan_id: TransformationPlanId
    inputs: tuple[tuple[str, DatasetReference], ...]
    outputs: tuple[tuple[str, DatasetReference], ...]
    dataset_edges: tuple[DatasetLineageEdge, ...]
    field_edges: tuple[FieldLineageEdge, ...]
    dependencies: tuple[FieldDependency, ...]
    resources: tuple[ResourceLineageLink, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.plan_id, TransformationPlanId):
            raise TypeError(
                "TransformationLineage plan_id must be a TransformationPlanId."
            )
        _validate_named_datasets(self.inputs, "inputs")
        _validate_named_datasets(self.outputs, "outputs")
        _validate_tuple_type(
            self.dataset_edges,
            DatasetLineageEdge,
            "dataset_edges",
        )
        _validate_tuple_type(
            self.field_edges,
            FieldLineageEdge,
            "field_edges",
        )
        _validate_tuple_type(
            self.dependencies,
            FieldDependency,
            "dependencies",
        )
        _validate_tuple_type(
            self.resources,
            ResourceLineageLink,
            "resources",
        )

    def input(self, name: str) -> DatasetReference:
        return _named_dataset(self.inputs, name)

    def output(self, name: str) -> DatasetReference:
        return _named_dataset(self.outputs, name)

    def field_sources(self, target: FieldReference) -> tuple[FieldReference, ...]:
        return tuple(
            edge.source
            for edge in self.field_edges
            if edge.target == target
        )

    def field_targets(self, source: FieldReference) -> tuple[FieldReference, ...]:
        return tuple(
            edge.target
            for edge in self.field_edges
            if edge.source == source
        )


def _validate_named_datasets(
    values: tuple[tuple[str, DatasetReference], ...],
    label: str,
) -> None:
    if not isinstance(values, tuple):
        raise TypeError(f"TransformationLineage {label} must be a tuple.")
    names: list[str] = []
    for item in values:
        if not isinstance(item, tuple) or len(item) != 2:
            raise TypeError(
                f"TransformationLineage {label} must contain name/reference pairs."
            )
        name, reference = item
        if not isinstance(name, str) or not name.strip():
            raise ValueError(
                f"TransformationLineage {label} names must not be empty."
            )
        if not isinstance(reference, DatasetReference):
            raise TypeError(
                f"TransformationLineage {label} values must be DatasetReference."
            )
        names.append(name)
    if len(names) != len(set(names)):
        raise ValueError(f"TransformationLineage {label} names must be unique.")


def _validate_tuple_type(
    values: tuple[object, ...],
    expected: type,
    label: str,
) -> None:
    if not isinstance(values, tuple):
        raise TypeError(f"TransformationLineage {label} must be a tuple.")
    if any(not isinstance(value, expected) for value in values):
        raise TypeError(
            f"TransformationLineage {label} contains an invalid value."
        )


def _named_dataset(
    values: tuple[tuple[str, DatasetReference], ...],
    name: str,
) -> DatasetReference:
    for item_name, reference in values:
        if item_name == name:
            return reference
    raise KeyError(name)
