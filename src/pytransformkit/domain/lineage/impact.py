"""Impact-analysis primitives over PyTransformKit logical lineage."""

from __future__ import annotations

from collections import deque

from pytransformkit.domain.data.references import DatasetReference
from pytransformkit.domain.lineage.model import (
    FieldReference,
    TransformationLineage,
)


class LineageImpactAnalyzer:
    """Traverse exact logical dataset and field dependencies."""

    def upstream_fields(
        self,
        lineage: TransformationLineage,
        target: FieldReference,
    ) -> tuple[FieldReference, ...]:
        """Return transitive field ancestors in deterministic breadth-first order."""
        if not isinstance(lineage, TransformationLineage):
            raise TypeError("lineage must be a TransformationLineage.")
        if not isinstance(target, FieldReference):
            raise TypeError("target must be a FieldReference.")

        by_target: dict[FieldReference, tuple[FieldReference, ...]] = {}
        for edge in lineage.field_edges:
            by_target.setdefault(edge.target, ())
            by_target[edge.target] = by_target[edge.target] + (edge.source,)

        return _walk_fields(target, by_target)

    def downstream_fields(
        self,
        lineage: TransformationLineage,
        source: FieldReference,
    ) -> tuple[FieldReference, ...]:
        """Return transitive field descendants in deterministic breadth-first order."""
        if not isinstance(lineage, TransformationLineage):
            raise TypeError("lineage must be a TransformationLineage.")
        if not isinstance(source, FieldReference):
            raise TypeError("source must be a FieldReference.")

        by_source: dict[FieldReference, tuple[FieldReference, ...]] = {}
        for edge in lineage.field_edges:
            by_source.setdefault(edge.source, ())
            by_source[edge.source] = by_source[edge.source] + (edge.target,)

        return _walk_fields(source, by_source)

    def upstream_datasets(
        self,
        lineage: TransformationLineage,
        target: DatasetReference,
    ) -> tuple[DatasetReference, ...]:
        """Return transitive logical dataset ancestors."""
        if not isinstance(lineage, TransformationLineage):
            raise TypeError("lineage must be a TransformationLineage.")
        if not isinstance(target, DatasetReference):
            raise TypeError("target must be a DatasetReference.")

        by_target: dict[DatasetReference, tuple[DatasetReference, ...]] = {}
        for edge in lineage.dataset_edges:
            by_target.setdefault(edge.target, ())
            by_target[edge.target] = by_target[edge.target] + (edge.source,)

        return _walk_datasets(target, by_target)

    def downstream_datasets(
        self,
        lineage: TransformationLineage,
        source: DatasetReference,
    ) -> tuple[DatasetReference, ...]:
        """Return transitive logical dataset descendants."""
        if not isinstance(lineage, TransformationLineage):
            raise TypeError("lineage must be a TransformationLineage.")
        if not isinstance(source, DatasetReference):
            raise TypeError("source must be a DatasetReference.")

        by_source: dict[DatasetReference, tuple[DatasetReference, ...]] = {}
        for edge in lineage.dataset_edges:
            by_source.setdefault(edge.source, ())
            by_source[edge.source] = by_source[edge.source] + (edge.target,)

        return _walk_datasets(source, by_source)


def _walk_fields(
    start: FieldReference,
    adjacency: dict[FieldReference, tuple[FieldReference, ...]],
) -> tuple[FieldReference, ...]:
    queue: deque[FieldReference] = deque(adjacency.get(start, ()))
    seen: set[FieldReference] = set()
    result: list[FieldReference] = []

    while queue:
        current = queue.popleft()
        if current in seen:
            continue
        seen.add(current)
        result.append(current)
        queue.extend(adjacency.get(current, ()))

    return tuple(result)


def _walk_datasets(
    start: DatasetReference,
    adjacency: dict[DatasetReference, tuple[DatasetReference, ...]],
) -> tuple[DatasetReference, ...]:
    queue: deque[DatasetReference] = deque(adjacency.get(start, ()))
    seen: set[DatasetReference] = set()
    result: list[DatasetReference] = []

    while queue:
        current = queue.popleft()
        if current in seen:
            continue
        seen.add(current)
        result.append(current)
        queue.extend(adjacency.get(current, ()))

    return tuple(result)
