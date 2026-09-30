"""Reader and Writer extension ports."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from pytransformkit.application.io.models import (
    ReadRequest,
    ReadResult,
    WriteRequest,
    WriteResult,
)


@runtime_checkable
class Reader(Protocol):
    """Resolve one physical resource into a runtime tabular representation."""

    @property
    def schemes(self) -> frozenset[str]:
        """Resource schemes supported by this Reader."""
        ...

    def read(self, request: ReadRequest) -> ReadResult:
        """Execute one bounded read request."""
        ...


@runtime_checkable
class Writer(Protocol):
    """Materialize one physical handle to an explicit target resource."""

    @property
    def schemes(self) -> frozenset[str]:
        """Resource schemes supported by this Writer."""
        ...

    def write(self, request: WriteRequest) -> WriteResult:
        """Execute one bounded write request."""
        ...
