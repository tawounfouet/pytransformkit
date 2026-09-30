"""Application contracts for bounded physical resource I/O."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from pytransformkit.application.ports.engines import PhysicalHandle
from pytransformkit.domain.data.schema import Schema
from pytransformkit.domain.expressions.base import Expression
from pytransformkit.domain.resources import (
    CredentialReference,
    ResourceFormat,
    ResourceReference,
    RetrySafety,
    WriteMode,
    WriteStatus,
)
from pytransformkit.domain.runtime import Diagnostic


class ReadRepresentation(StrEnum):
    """Physical interchange representation returned by a Reader."""

    ARROW = "arrow"


class PushdownStatus(StrEnum):
    """Where a requested scan optimization was actually applied."""

    NOT_REQUESTED = "not_requested"
    SOURCE = "source"
    POST_SCAN = "post_scan"


@dataclass(frozen=True, slots=True)
class ReadPushdownEvidence:
    """Structured evidence for scan pushdown behavior."""

    projection: PushdownStatus = PushdownStatus.NOT_REQUESTED
    predicate: PushdownStatus = PushdownStatus.NOT_REQUESTED
    partition_pruning: PushdownStatus = PushdownStatus.NOT_REQUESTED


@dataclass(frozen=True, slots=True)
class ReadRequest:
    """Explicit request to resolve one portable resource into tabular data."""

    resource: ResourceReference
    expected_schema: Schema | None = None
    projection: tuple[str, ...] = ()
    predicate: Expression | None = None
    partition_filters: tuple[tuple[str, str], ...] = ()
    credential: CredentialReference | None = None
    retry_safety: RetrySafety = RetrySafety.SAFE

    def __post_init__(self) -> None:
        if not isinstance(self.resource, ResourceReference):
            raise TypeError("ReadRequest resource must be a ResourceReference.")
        if self.expected_schema is not None and not isinstance(
            self.expected_schema,
            Schema,
        ):
            raise TypeError("ReadRequest expected_schema must be a Schema.")
        if not isinstance(self.projection, tuple):
            raise TypeError("ReadRequest projection must be a tuple.")
        if any(
            not isinstance(name, str) or not name.strip() for name in self.projection
        ):
            raise ValueError("ReadRequest projection must contain non-empty names.")
        if len(set(self.projection)) != len(self.projection):
            raise ValueError("ReadRequest projection must not contain duplicates.")
        if self.predicate is not None and not isinstance(self.predicate, Expression):
            raise TypeError("ReadRequest predicate must be an Expression.")
        _validate_string_pairs(self.partition_filters, "partition_filters")
        if self.credential is not None and not isinstance(
            self.credential,
            CredentialReference,
        ):
            raise TypeError("ReadRequest credential must be a CredentialReference.")
        if not isinstance(self.retry_safety, RetrySafety):
            raise TypeError("ReadRequest retry_safety must be RetrySafety.")


@dataclass(frozen=True, slots=True)
class ReadResult:
    """Runtime-only data returned by a Reader."""

    resource: ResourceReference
    resource_format: ResourceFormat
    representation: ReadRepresentation
    value: object
    schema: Schema
    pushdown: ReadPushdownEvidence = ReadPushdownEvidence()
    diagnostics: tuple[Diagnostic, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.resource, ResourceReference):
            raise TypeError("ReadResult resource must be a ResourceReference.")
        if not isinstance(self.resource_format, ResourceFormat):
            raise TypeError("ReadResult resource_format must be ResourceFormat.")
        if not isinstance(self.representation, ReadRepresentation):
            raise TypeError("ReadResult representation must be ReadRepresentation.")
        if not isinstance(self.schema, Schema):
            raise TypeError("ReadResult schema must be a Schema.")
        if not isinstance(self.pushdown, ReadPushdownEvidence):
            raise TypeError("ReadResult pushdown must be ReadPushdownEvidence.")
        if not isinstance(self.diagnostics, tuple):
            raise TypeError("ReadResult diagnostics must be a tuple.")


@dataclass(frozen=True, slots=True)
class WriteRequest:
    """Explicit physical materialization request for one runtime handle."""

    resource: ResourceReference
    handle: PhysicalHandle
    schema: Schema
    mode: WriteMode = WriteMode.CREATE_NEW
    credential: CredentialReference | None = None
    retry_safety: RetrySafety = RetrySafety.UNKNOWN

    def __post_init__(self) -> None:
        if not isinstance(self.resource, ResourceReference):
            raise TypeError("WriteRequest resource must be a ResourceReference.")
        if not isinstance(self.handle, PhysicalHandle):
            raise TypeError("WriteRequest handle must satisfy PhysicalHandle.")
        if not isinstance(self.schema, Schema):
            raise TypeError("WriteRequest schema must be a Schema.")
        if not isinstance(self.mode, WriteMode):
            raise TypeError("WriteRequest mode must be WriteMode.")
        if self.credential is not None and not isinstance(
            self.credential,
            CredentialReference,
        ):
            raise TypeError("WriteRequest credential must be a CredentialReference.")
        if not isinstance(self.retry_safety, RetrySafety):
            raise TypeError("WriteRequest retry_safety must be RetrySafety.")


@dataclass(frozen=True, slots=True)
class WriteResult:
    """Observed result of one bounded physical write attempt."""

    resource: ResourceReference
    resource_format: ResourceFormat
    status: WriteStatus
    retry_safety: RetrySafety
    rows_written: int | None = None
    bytes_written: int | None = None
    diagnostics: tuple[Diagnostic, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.resource, ResourceReference):
            raise TypeError("WriteResult resource must be a ResourceReference.")
        if not isinstance(self.resource_format, ResourceFormat):
            raise TypeError("WriteResult resource_format must be ResourceFormat.")
        if not isinstance(self.status, WriteStatus):
            raise TypeError("WriteResult status must be WriteStatus.")
        if not isinstance(self.retry_safety, RetrySafety):
            raise TypeError("WriteResult retry_safety must be RetrySafety.")
        if self.rows_written is not None and self.rows_written < 0:
            raise ValueError("WriteResult rows_written must be non-negative.")
        if self.bytes_written is not None and self.bytes_written < 0:
            raise ValueError("WriteResult bytes_written must be non-negative.")
        if not isinstance(self.diagnostics, tuple):
            raise TypeError("WriteResult diagnostics must be a tuple.")


def _validate_string_pairs(
    values: tuple[tuple[str, str], ...],
    name: str,
) -> None:
    if not isinstance(values, tuple):
        raise TypeError(f"{name} must be a tuple.")
    for item in values:
        if (
            not isinstance(item, tuple)
            or len(item) != 2
            or not all(isinstance(value, str) and value.strip() for value in item)
        ):
            raise ValueError(f"{name} must contain non-empty string pairs.")
