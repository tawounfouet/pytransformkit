"""Application-level plugin and extension contracts."""

from pytransformkit.application.extensions.contracts import (
    PLUGIN_API_VERSION,
    FunctionDefinition,
    FunctionExtension,
    OptimizerRule,
    Plugin,
    PluginCompatibility,
    PluginDescriptor,
    PluginKind,
    ResourceResolver,
)
from pytransformkit.application.extensions.registry import (
    PLUGIN_ENTRY_POINT_GROUP,
    DiscoveredPlugin,
    FunctionRegistry,
    OptimizerRuleRegistry,
    PluginActivationContext,
    PluginEntryPoint,
    PluginRegistry,
    ResourceResolverRegistry,
    TelemetrySinkRegistry,
)

__all__ = [
    "PLUGIN_API_VERSION",
    "PLUGIN_ENTRY_POINT_GROUP",
    "DiscoveredPlugin",
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
    "ResourceResolver",
    "ResourceResolverRegistry",
    "TelemetrySinkRegistry",
]
