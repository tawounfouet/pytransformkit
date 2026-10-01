"""Public engine registry and extension contracts."""

from pytransformkit.application.execution.registry import EngineRegistry
from pytransformkit.application.ports.engines import (
    EngineAdapter,
    MultiInputEngineAdapter,
    PhysicalHandle,
)
from pytransformkit.domain.engines import EngineCapability, EngineDescriptor

Capability = EngineCapability

__all__ = [
    "Capability",
    "EngineAdapter",
    "EngineCapability",
    "EngineDescriptor",
    "EngineRegistry",
    "PhysicalHandle",
]
