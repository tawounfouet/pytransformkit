from __future__ import annotations

import importlib
from dataclasses import dataclass

import pytest

from pytransformkit.application.extensions import (
    PLUGIN_ENTRY_POINT_GROUP,
    FunctionDefinition,
    PluginCompatibility,
    PluginDescriptor,
    PluginKind,
    PluginRegistry,
)
from pytransformkit.domain.expressions.functions import (
    FunctionCall,
    FunctionIdentifier,
)
from pytransformkit.domain.runtime import NullTelemetrySink
from pytransformkit.domain.shared.version import Version
from pytransformkit.errors import (
    PluginCompatibilityError,
    PluginConflictError,
    PluginNotFoundError,
    RegistryFrozenError,
)
from pytransformkit.errors.serialization import NonPortableValueError
from pytransformkit.functions import col
from pytransformkit.serialization.registry import SemanticTypeRegistry


class FakeEntryPoint:
    def __init__(self, name: str, provider: object) -> None:
        self.name = name
        self.group = PLUGIN_ENTRY_POINT_GROUP
        self.value = "tests.fake:provider"
        self.provider = provider
        self.load_count = 0

    def load(self) -> object:
        self.load_count += 1
        return self.provider


@dataclass
class DemoPlugin:
    descriptor: PluginDescriptor

    def activate(self, context) -> None:  # type: ignore[no-untyped-def]
        context.functions.register(
            FunctionDefinition(
                identifier=FunctionIdentifier("demo.identity"),
                builder=lambda arguments: FunctionCall(
                    FunctionIdentifier("demo.identity"),
                    arguments,
                ),
            )
        )
        context.telemetry_sinks.register("demo", NullTelemetrySink())


def _descriptor(
    plugin_id: str = "demo-plugin",
    *,
    compatibility: PluginCompatibility | None = None,
) -> PluginDescriptor:
    return PluginDescriptor(
        plugin_id=plugin_id,
        version="1.0.0",
        compatibility=compatibility or PluginCompatibility(),
        kinds=(PluginKind.FUNCTION, PluginKind.TELEMETRY_SINK),
    )


def test_discovery_does_not_load_or_activate_plugin_code() -> None:
    entry_point = FakeEntryPoint("demo-plugin", DemoPlugin(_descriptor()))

    plugins = PluginRegistry.discover(
        framework_version=Version(0, 5, 0),
        candidates=(entry_point,),
    )

    assert entry_point.load_count == 0
    assert plugins.list() == ("demo-plugin",)
    assert plugins.active() == ()
    assert plugins.context.functions.list() == ()
    assert plugins.context.telemetry_sinks.list() == ()


def test_explicit_activation_loads_once_and_registers_extensions() -> None:
    entry_point = FakeEntryPoint("demo-plugin", DemoPlugin(_descriptor()))
    plugins = PluginRegistry.discover(
        framework_version=Version(0, 5, 0),
        candidates=(entry_point,),
    )

    descriptor = plugins.activate("demo-plugin")

    assert descriptor == _descriptor()
    assert entry_point.load_count == 1
    assert plugins.context.functions.list() == ("demo.identity",)
    assert plugins.context.telemetry_sinks.list() == ("demo",)
    expression = plugins.context.functions.call("demo.identity", col("amount"))
    assert isinstance(expression, FunctionCall)


def test_unknown_plugin_requires_explicit_discovery() -> None:
    plugins = PluginRegistry.discover(
        framework_version=Version(0, 5, 0),
        candidates=(),
    )

    with pytest.raises(PluginNotFoundError):
        plugins.activate("not-discovered")


def test_incompatible_plugin_fails_before_provider_activation() -> None:
    compatibility = PluginCompatibility(
        framework_min=Version(0, 6, 0),
        framework_max_exclusive=Version(1, 0, 0),
    )
    plugin = DemoPlugin(_descriptor(compatibility=compatibility))
    entry_point = FakeEntryPoint("demo-plugin", plugin)
    plugins = PluginRegistry.discover(
        framework_version=Version(0, 5, 0),
        candidates=(entry_point,),
    )

    with pytest.raises(PluginCompatibilityError):
        plugins.activate("demo-plugin")

    assert entry_point.load_count == 1
    assert plugins.context.functions.list() == ()


def test_duplicate_discovery_and_double_activation_fail_explicitly() -> None:
    first = FakeEntryPoint("demo-plugin", DemoPlugin(_descriptor()))
    second = FakeEntryPoint("demo-plugin", DemoPlugin(_descriptor()))

    with pytest.raises(PluginConflictError):
        PluginRegistry.discover(
            framework_version=Version(0, 5, 0),
            candidates=(first, second),
        )

    plugins = PluginRegistry.discover(
        framework_version=Version(0, 5, 0),
        candidates=(first,),
    )
    plugins.activate("demo-plugin")
    with pytest.raises(PluginConflictError):
        plugins.activate("demo-plugin")


def test_freeze_prevents_activation_and_registry_mutation() -> None:
    entry_point = FakeEntryPoint("demo-plugin", DemoPlugin(_descriptor()))
    plugins = PluginRegistry.discover(
        framework_version=Version(0, 5, 0),
        candidates=(entry_point,),
    )

    plugins.freeze()

    with pytest.raises(RegistryFrozenError):
        plugins.activate("demo-plugin")
    with pytest.raises(RegistryFrozenError):
        plugins.context.telemetry_sinks.register("late", NullTelemetrySink())


def test_plugin_metadata_is_not_part_of_safe_wire_type_registry() -> None:
    registry = SemanticTypeRegistry.default()

    with pytest.raises(NonPortableValueError):
        registry.type_id_for(PluginDescriptor)


def test_importing_public_plugin_namespace_does_not_trigger_discovery(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    registry_module = importlib.import_module(
        "pytransformkit.application.extensions.registry"
    )

    def fail_discovery() -> object:
        raise AssertionError("entry_points() must not run during module import")

    monkeypatch.setattr(registry_module, "entry_points", fail_discovery)

    public_plugins = importlib.import_module("pytransformkit.plugins")
    importlib.reload(public_plugins)
