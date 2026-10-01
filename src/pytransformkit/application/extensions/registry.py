"""Explicit extension registries and entry-point plugin activation."""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from importlib.metadata import PackageNotFoundError, entry_points, version
from typing import Protocol, runtime_checkable

from pytransformkit.application.execution.registry import EngineRegistry
from pytransformkit.application.extensions.contracts import (
    PLUGIN_API_VERSION,
    FunctionExtension,
    OptimizerRule,
    Plugin,
    PluginDescriptor,
    ResourceResolver,
)
from pytransformkit.application.io import ResourceIORegistry
from pytransformkit.domain.expressions.base import Expression
from pytransformkit.domain.resources import ResourceReference
from pytransformkit.domain.runtime import TelemetrySink
from pytransformkit.domain.shared.version import Version
from pytransformkit.errors.plugin import (
    PluginActivationError,
    PluginCompatibilityError,
    PluginConflictError,
    PluginError,
    PluginNotFoundError,
    RegistryFrozenError,
)

PLUGIN_ENTRY_POINT_GROUP = "pytransformkit.plugins"


@runtime_checkable
class PluginEntryPoint(Protocol):
    """Minimal importlib.metadata.EntryPoint surface used by discovery."""

    name: str
    group: str
    value: str

    def load(self) -> object:
        """Import and return the configured provider target."""
        ...


class FunctionRegistry:
    """Explicit registry for named engine-neutral Expression factories."""

    def __init__(self) -> None:
        self._values: dict[str, FunctionExtension] = {}
        self._frozen = False

    @property
    def frozen(self) -> bool:
        return self._frozen

    def register(
        self,
        extension: FunctionExtension,
        *,
        replace: bool = False,
    ) -> None:
        self._ensure_mutable()
        if not isinstance(extension, FunctionExtension):
            raise TypeError("extension must satisfy the FunctionExtension protocol.")
        key = str(extension.identifier)
        _validate_key(key, "function identifier")
        if key in self._values and not replace:
            raise PluginConflictError(f"Function {key!r} is already registered.")
        self._values[key] = extension

    def get(self, identifier: str) -> FunctionExtension:
        try:
            return self._values[identifier]
        except KeyError as error:
            raise KeyError(f"Function {identifier!r} is not registered.") from error

    def call(self, identifier: str, *arguments: Expression) -> Expression:
        if any(not isinstance(argument, Expression) for argument in arguments):
            raise TypeError("function arguments must be Expressions.")
        result = self.get(identifier).build(tuple(arguments))
        if not isinstance(result, Expression):
            raise TypeError("FunctionExtension.build() must return an Expression.")
        return result

    def list(self) -> tuple[str, ...]:
        return tuple(self._values)

    def freeze(self) -> None:
        self._frozen = True

    def _ensure_mutable(self) -> None:
        if self._frozen:
            raise RegistryFrozenError("FunctionRegistry is frozen.")


class OptimizerRuleRegistry:
    """Explicit registry for engine-neutral optimizer rules."""

    def __init__(self) -> None:
        self._values: dict[str, OptimizerRule] = {}
        self._frozen = False

    @property
    def frozen(self) -> bool:
        return self._frozen

    def register(self, rule: OptimizerRule, *, replace: bool = False) -> None:
        self._ensure_mutable()
        if not isinstance(rule, OptimizerRule):
            raise TypeError("rule must satisfy the OptimizerRule protocol.")
        key = rule.rule_id
        _validate_key(key, "optimizer rule id")
        if key in self._values and not replace:
            raise PluginConflictError(f"Optimizer rule {key!r} is already registered.")
        self._values[key] = rule

    def get(self, rule_id: str) -> OptimizerRule:
        try:
            return self._values[rule_id]
        except KeyError as error:
            raise KeyError(f"Optimizer rule {rule_id!r} is not registered.") from error

    def rules(self) -> tuple[OptimizerRule, ...]:
        return tuple(self._values.values())

    def list(self) -> tuple[str, ...]:
        return tuple(self._values)

    def freeze(self) -> None:
        self._frozen = True

    def _ensure_mutable(self) -> None:
        if self._frozen:
            raise RegistryFrozenError("OptimizerRuleRegistry is frozen.")


class ResourceResolverRegistry:
    """Resolve ResourceReference values only through explicitly registered resolvers."""

    def __init__(self) -> None:
        self._resolvers: dict[str, ResourceResolver] = {}
        self._frozen = False

    @property
    def frozen(self) -> bool:
        return self._frozen

    def register(
        self,
        resolver: ResourceResolver,
        *,
        replace: bool = False,
    ) -> None:
        self._ensure_mutable()
        if not isinstance(resolver, ResourceResolver):
            raise TypeError("resolver must satisfy the ResourceResolver protocol.")
        if not resolver.schemes:
            raise ValueError("ResourceResolver must advertise at least one scheme.")
        for scheme in resolver.schemes:
            normalized = _scheme(scheme)
            if normalized in self._resolvers and not replace:
                raise PluginConflictError(
                    f"ResourceResolver already registered for scheme {normalized!r}."
                )
        for scheme in resolver.schemes:
            self._resolvers[_scheme(scheme)] = resolver

    def resolver_for(self, scheme: str) -> ResourceResolver:
        normalized = _scheme(scheme)
        try:
            return self._resolvers[normalized]
        except KeyError as error:
            raise KeyError(
                f"No ResourceResolver is registered for scheme {normalized!r}."
            ) from error

    def resolve(self, reference: ResourceReference) -> object:
        if not isinstance(reference, ResourceReference):
            raise TypeError("reference must be a ResourceReference.")
        return self.resolver_for(reference.scheme).resolve(reference)

    def list(self) -> tuple[str, ...]:
        return tuple(self._resolvers)

    def freeze(self) -> None:
        self._frozen = True

    def _ensure_mutable(self) -> None:
        if self._frozen:
            raise RegistryFrozenError("ResourceResolverRegistry is frozen.")


class TelemetrySinkRegistry:
    """Explicit named registry for vendor-neutral telemetry sinks."""

    def __init__(self) -> None:
        self._sinks: dict[str, TelemetrySink] = {}
        self._frozen = False

    @property
    def frozen(self) -> bool:
        return self._frozen

    def register(
        self,
        name: str,
        sink: TelemetrySink,
        *,
        replace: bool = False,
    ) -> None:
        self._ensure_mutable()
        key = _normalized_name(name, "telemetry sink name")
        if not isinstance(sink, TelemetrySink):
            raise TypeError("sink must satisfy the TelemetrySink protocol.")
        if key in self._sinks and not replace:
            raise PluginConflictError(f"Telemetry sink {key!r} is already registered.")
        self._sinks[key] = sink

    def get(self, name: str) -> TelemetrySink:
        key = _normalized_name(name, "telemetry sink name")
        try:
            return self._sinks[key]
        except KeyError as error:
            raise KeyError(f"Telemetry sink {key!r} is not registered.") from error

    def list(self) -> tuple[str, ...]:
        return tuple(self._sinks)

    def freeze(self) -> None:
        self._frozen = True

    def _ensure_mutable(self) -> None:
        if self._frozen:
            raise RegistryFrozenError("TelemetrySinkRegistry is frozen.")


@dataclass(slots=True)
class PluginActivationContext:
    """Registries a trusted plugin may mutate only during explicit activation."""

    engines: EngineRegistry = field(default_factory=EngineRegistry)
    resources: ResourceIORegistry = field(default_factory=ResourceIORegistry)
    resource_resolvers: ResourceResolverRegistry = field(
        default_factory=ResourceResolverRegistry
    )
    functions: FunctionRegistry = field(default_factory=FunctionRegistry)
    optimizer_rules: OptimizerRuleRegistry = field(
        default_factory=OptimizerRuleRegistry
    )
    telemetry_sinks: TelemetrySinkRegistry = field(
        default_factory=TelemetrySinkRegistry
    )

    def freeze(self) -> None:
        """Freeze every registry after activation configuration is complete."""
        self.engines.freeze()
        self.resources.freeze()
        self.resource_resolvers.freeze()
        self.functions.freeze()
        self.optimizer_rules.freeze()
        self.telemetry_sinks.freeze()


@dataclass(frozen=True, slots=True)
class DiscoveredPlugin:
    """Non-executable entry-point metadata captured during discovery."""

    plugin_id: str
    group: str
    value: str


class PluginRegistry:
    """Separate non-executing discovery from explicit plugin activation."""

    def __init__(
        self,
        *,
        context: PluginActivationContext | None = None,
        framework_version: Version | None = None,
        protocol_version: int = PLUGIN_API_VERSION,
    ) -> None:
        self._context = context or PluginActivationContext()
        self._framework_version = framework_version or _current_framework_version()
        self._protocol_version = protocol_version
        self._entry_points: dict[str, PluginEntryPoint] = {}
        self._active: dict[str, PluginDescriptor] = {}
        self._frozen = False

    @classmethod
    def discover(
        cls,
        *,
        context: PluginActivationContext | None = None,
        framework_version: Version | None = None,
        protocol_version: int = PLUGIN_API_VERSION,
        group: str = PLUGIN_ENTRY_POINT_GROUP,
        candidates: Iterable[PluginEntryPoint] | None = None,
    ) -> PluginRegistry:
        """Discover entry-point metadata without importing plugin code."""
        registry = cls(
            context=context,
            framework_version=framework_version,
            protocol_version=protocol_version,
        )
        discovered = candidates
        if discovered is None:
            available = entry_points()
            discovered = available.select(group=group)

        for candidate in discovered:
            if candidate.group != group:
                continue
            registry._add_discovered(candidate)
        return registry

    @property
    def context(self) -> PluginActivationContext:
        return self._context

    @property
    def frozen(self) -> bool:
        return self._frozen

    def discovered(self) -> tuple[DiscoveredPlugin, ...]:
        return tuple(
            DiscoveredPlugin(
                plugin_id=plugin_id,
                group=entry_point.group,
                value=entry_point.value,
            )
            for plugin_id, entry_point in self._entry_points.items()
        )

    def list(self) -> tuple[str, ...]:
        return tuple(self._entry_points)

    def active(self) -> tuple[PluginDescriptor, ...]:
        return tuple(self._active.values())

    def activate(self, plugin_id: str) -> PluginDescriptor:
        """Load and activate exactly one previously discovered plugin."""
        self._ensure_mutable()
        key = _normalized_name(plugin_id, "plugin id")
        if key in self._active:
            raise PluginConflictError(f"Plugin {key!r} is already active.")
        try:
            candidate = self._entry_points[key]
        except KeyError as error:
            raise PluginNotFoundError(key) from error

        try:
            loaded = candidate.load()
            plugin = _plugin_instance(loaded)
        except PluginError:
            raise
        except Exception as error:
            raise PluginActivationError(
                f"Plugin {key!r} failed while loading its entry point."
            ) from error

        descriptor = plugin.descriptor
        if descriptor.plugin_id != key:
            raise PluginConflictError(
                f"Discovered plugin id {key!r} does not match provider descriptor "
                f"{descriptor.plugin_id!r}."
            )
        if not descriptor.compatibility.supports(
            self._framework_version,
            self._protocol_version,
        ):
            raise PluginCompatibilityError(
                f"Plugin {key!r} {descriptor.version!r} is incompatible with "
                f"PyTransformKit {self._framework_version} and plugin protocol "
                f"{self._protocol_version}."
            )

        try:
            plugin.activate(self._context)
        except PluginError:
            raise
        except Exception as error:
            raise PluginActivationError(
                f"Plugin {key!r} failed during explicit activation."
            ) from error

        self._active[key] = descriptor
        return descriptor

    def freeze(self) -> None:
        """Freeze plugin activation and every owned extension registry."""
        self._context.freeze()
        self._frozen = True

    def _add_discovered(self, candidate: PluginEntryPoint) -> None:
        self._ensure_mutable()
        if not isinstance(candidate, PluginEntryPoint):
            raise TypeError("candidate must satisfy the PluginEntryPoint protocol.")
        key = _normalized_name(candidate.name, "plugin id")
        if key in self._entry_points:
            raise PluginConflictError(
                f"Duplicate discovered plugin entry point {key!r}."
            )
        self._entry_points[key] = candidate

    def _ensure_mutable(self) -> None:
        if self._frozen:
            raise RegistryFrozenError("PluginRegistry is frozen.")


def _plugin_instance(value: object) -> Plugin:
    candidate = value
    if isinstance(candidate, type) or (
        not isinstance(candidate, Plugin) and callable(candidate)
    ):
        candidate = candidate()

    if not isinstance(candidate, Plugin):
        raise PluginActivationError(
            "Plugin entry point must resolve to a Plugin "
            "or zero-argument Plugin factory."
        )
    return candidate


def _current_framework_version() -> Version:
    try:
        raw = version("pytransformkit")
    except PackageNotFoundError:
        raw = "1.0.0"
    match = re.match(r"^(\d+)\.(\d+)\.(\d+)", raw)
    if match is None:
        raise PluginCompatibilityError(
            f"Cannot derive semantic framework version from {raw!r}."
        )
    return Version(*(int(item) for item in match.groups()))


def _normalized_name(value: str, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must not be empty.")
    return value.strip()


def _validate_key(value: str, label: str) -> None:
    _normalized_name(value, label)


def _scheme(value: str) -> str:
    return _normalized_name(value, "resource scheme").lower()
