"""Public plugin and extension architecture."""

from pytransformkit.application.extensions import (
    PLUGIN_API_VERSION,
    PLUGIN_ENTRY_POINT_GROUP,
    DiscoveredPlugin,
    FunctionDefinition,
    FunctionExtension,
    FunctionRegistry,
    OptimizerRule,
    OptimizerRuleRegistry,
    Plugin,
    PluginActivationContext,
    PluginCompatibility,
    PluginDescriptor,
    PluginEntryPoint,
    PluginKind,
    PluginRegistry,
    ResourceResolver,
    ResourceResolverRegistry,
    TelemetrySinkRegistry,
)
from pytransformkit.application.io import Reader, Writer
from pytransformkit.application.ports.engines import EngineAdapter
from pytransformkit.domain.runtime import TelemetrySink

__all__ = [
    "PLUGIN_API_VERSION",
    "PLUGIN_ENTRY_POINT_GROUP",
    "DiscoveredPlugin",
    "EngineAdapter",
    "FunctionDefinition",
    "FunctionExtension",
    "FunctionRegistry",
    "OptimizerRule",
    "OptimizerRuleRegistry",
    "Plugin",
    "PluginActivationContext",
    "PluginCompatibility",
    "PluginDescriptor",
    "PluginEntryPoint",
    "PluginKind",
    "PluginRegistry",
    "Reader",
    "ResourceResolver",
    "ResourceResolverRegistry",
    "TelemetrySink",
    "TelemetrySinkRegistry",
    "Writer",
]
