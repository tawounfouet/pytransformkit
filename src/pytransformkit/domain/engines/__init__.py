"""Engine-independent engine descriptors and capabilities."""

from pytransformkit.domain.engines.capabilities import (
    CancellationSupport,
    EngineCapability,
)
from pytransformkit.domain.engines.descriptor import EngineDescriptor

__all__ = ["CancellationSupport", "EngineCapability", "EngineDescriptor"]
