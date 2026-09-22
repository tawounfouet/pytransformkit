"""Logical engine descriptor."""

from dataclasses import dataclass

from pytransformkit.domain.engines.capabilities import EngineCapability


@dataclass(frozen=True, slots=True)
class EngineDescriptor:
    """Portable description of an execution engine adapter."""

    id: str
    name: str
    adapter_version: str
    capabilities: frozenset[EngineCapability]

    def __post_init__(self) -> None:
        if not self.id or not self.id.strip():
            raise ValueError("Engine id must not be empty.")
        if not self.name or not self.name.strip():
            raise ValueError("Engine name must not be empty.")
        if not self.adapter_version or not self.adapter_version.strip():
            raise ValueError("Engine adapter_version must not be empty.")
        if not isinstance(self.capabilities, frozenset):
            raise TypeError("Engine capabilities must be provided as a frozenset.")
        if any(
            not isinstance(capability, EngineCapability)
            for capability in self.capabilities
        ):
            raise TypeError(
                "Engine capabilities must contain only EngineCapability values."
            )

    def supports(self, capability: EngineCapability) -> bool:
        """Return whether this engine advertises one capability."""
        return capability in self.capabilities
