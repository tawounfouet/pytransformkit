"""Stable public extension contracts for PyTransformKit plugins."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from pytransformkit.domain.expressions.base import Expression
from pytransformkit.domain.expressions.functions import FunctionIdentifier
from pytransformkit.domain.pipelines.plan import LogicalPlan
from pytransformkit.domain.resources import ResourceReference
from pytransformkit.domain.shared.version import Version

if TYPE_CHECKING:
    from pytransformkit.application.extensions.registry import PluginActivationContext

PLUGIN_API_VERSION = 1


class PluginKind(StrEnum):
    """Stable extension categories supported by the V1 plugin boundary."""

    ENGINE_ADAPTER = "engine_adapter"
    READER = "reader"
    WRITER = "writer"
    RESOURCE_RESOLVER = "resource_resolver"
    FUNCTION = "function"
    OPTIMIZER_RULE = "optimizer_rule"
    TELEMETRY_SINK = "telemetry_sink"


@dataclass(frozen=True, slots=True)
class PluginCompatibility:
    """Machine-checkable package and plugin-protocol compatibility range."""

    framework_min: Version = Version(0, 5, 0)
    framework_max_exclusive: Version = Version(1, 0, 0)
    protocol_min: int = PLUGIN_API_VERSION
    protocol_max: int = PLUGIN_API_VERSION

    def __post_init__(self) -> None:
        if self.framework_min >= self.framework_max_exclusive:
            raise ValueError(
                "framework_min must be lower than framework_max_exclusive."
            )
        if (
            not isinstance(self.protocol_min, int)
            or isinstance(self.protocol_min, bool)
            or self.protocol_min < 1
        ):
            raise ValueError("protocol_min must be a positive integer.")
        if (
            not isinstance(self.protocol_max, int)
            or isinstance(self.protocol_max, bool)
            or self.protocol_max < self.protocol_min
        ):
            raise ValueError("protocol_max must be >= protocol_min.")

    def supports(
        self,
        framework_version: Version,
        protocol_version: int = PLUGIN_API_VERSION,
    ) -> bool:
        """Return whether one framework/protocol pair is compatible."""
        if not isinstance(framework_version, Version):
            raise TypeError("framework_version must be a Version.")
        if not isinstance(protocol_version, int) or isinstance(protocol_version, bool):
            raise TypeError("protocol_version must be an integer.")
        return (
            self.framework_min <= framework_version < self.framework_max_exclusive
            and self.protocol_min <= protocol_version <= self.protocol_max
        )


@dataclass(frozen=True, slots=True)
class PluginDescriptor:
    """Pure metadata exposed by an explicitly loaded plugin."""

    plugin_id: str
    version: str
    compatibility: PluginCompatibility
    kinds: tuple[PluginKind, ...]

    def __post_init__(self) -> None:
        if not self.plugin_id or not self.plugin_id.strip():
            raise ValueError("plugin_id must not be empty.")
        if not self.version or not self.version.strip():
            raise ValueError("plugin version must not be empty.")
        if not isinstance(self.compatibility, PluginCompatibility):
            raise TypeError("compatibility must be a PluginCompatibility.")
        if not isinstance(self.kinds, tuple) or not self.kinds:
            raise ValueError("kinds must contain at least one PluginKind.")
        if any(not isinstance(kind, PluginKind) for kind in self.kinds):
            raise TypeError("kinds must contain only PluginKind values.")
        if len(set(self.kinds)) != len(self.kinds):
            raise ValueError("plugin kinds must be unique.")


@runtime_checkable
class ResourceResolver(Protocol):
    """Resolve a portable ResourceReference into one process-local value."""

    @property
    def schemes(self) -> frozenset[str]:
        """Resource schemes supported by this resolver."""
        ...

    def resolve(self, reference: ResourceReference) -> object:
        """Resolve one explicit portable reference."""
        ...


@runtime_checkable
class FunctionExtension(Protocol):
    """One named Expression factory registered explicitly at runtime."""

    @property
    def identifier(self) -> FunctionIdentifier:
        """Stable logical function identifier."""
        ...

    def build(self, arguments: tuple[Expression, ...]) -> Expression:
        """Build one engine-neutral Expression."""
        ...


@dataclass(frozen=True, slots=True)
class FunctionDefinition:
    """Convenience immutable implementation of FunctionExtension."""

    identifier: FunctionIdentifier
    builder: Callable[[tuple[Expression, ...]], Expression]

    def __post_init__(self) -> None:
        if not isinstance(self.identifier, FunctionIdentifier):
            raise TypeError("identifier must be a FunctionIdentifier.")
        if not callable(self.builder):
            raise TypeError("builder must be callable.")

    def build(self, arguments: tuple[Expression, ...]) -> Expression:
        return self.builder(arguments)


@runtime_checkable
class OptimizerRule(Protocol):
    """Extension rule preserving LogicalPlan semantics."""

    @property
    def rule_id(self) -> str:
        """Stable optimizer rule identifier."""
        ...

    def apply(self, plan: LogicalPlan) -> LogicalPlan:
        """Return a semantically equivalent LogicalPlan."""
        ...


@runtime_checkable
class Plugin(Protocol):
    """Explicitly activated provider loaded from an entry point."""

    @property
    def descriptor(self) -> PluginDescriptor:
        """Return immutable plugin compatibility metadata."""
        ...

    def activate(self, context: PluginActivationContext) -> None:
        """Register extensions in the explicit activation context."""
        ...
