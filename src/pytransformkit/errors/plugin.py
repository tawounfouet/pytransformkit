"""Plugin and extension-registry related errors."""

from typing import ClassVar

from pytransformkit.errors.base import PyTransformKitError
from pytransformkit.errors.codes import ErrorCode


class PluginError(PyTransformKitError):
    """Base class for plugin architecture failures."""

    error_code: ClassVar[ErrorCode] = ErrorCode("PTK-PLUGIN-000")


class PluginNotFoundError(PluginError):
    """Raised when an explicitly requested discovered plugin does not exist."""

    error_code: ClassVar[ErrorCode] = ErrorCode("PTK-PLUGIN-001")

    def __init__(self, plugin_id: str) -> None:
        self.plugin_id = plugin_id
        super().__init__(f"Plugin {plugin_id!r} is not discovered.")


class PluginConflictError(PluginError):
    """Raised for duplicate plugin or extension registrations."""

    error_code: ClassVar[ErrorCode] = ErrorCode("PTK-PLUGIN-002")


class PluginCompatibilityError(PluginError):
    """Raised when a plugin compatibility declaration rejects this runtime."""

    error_code: ClassVar[ErrorCode] = ErrorCode("PTK-PLUGIN-003")


class PluginActivationError(PluginError):
    """Raised when explicit plugin activation fails."""

    error_code: ClassVar[ErrorCode] = ErrorCode("PTK-PLUGIN-004")


class RegistryFrozenError(PluginError):
    """Raised when a frozen extension registry is mutated."""

    error_code: ClassVar[ErrorCode] = ErrorCode("PTK-PLUGIN-005")
