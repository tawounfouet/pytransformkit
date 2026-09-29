"""Explicit engine adapter registry."""

from pytransformkit.application.ports.engines import EngineAdapter
from pytransformkit.errors.engine import AdapterError, EngineNotFoundError


class EngineRegistry:
    """Mutable application registry with no implicit fallback behavior."""

    def __init__(self) -> None:
        self._adapters: dict[str, EngineAdapter] = {}

    def register(
        self,
        adapter: EngineAdapter,
        *,
        replace: bool = False,
    ) -> None:
        """Register one adapter by explicit engine id."""
        engine_id = adapter.descriptor.id
        if engine_id in self._adapters and not replace:
            raise AdapterError(
                f"Engine {engine_id!r} is already registered. "
                "Pass replace=True to replace it explicitly."
            )
        self._adapters[engine_id] = adapter

    def unregister(self, engine_id: str) -> None:
        """Remove one explicitly named adapter."""
        if engine_id not in self._adapters:
            raise EngineNotFoundError(engine_id)
        del self._adapters[engine_id]

    def get(self, engine_id: str) -> EngineAdapter:
        """Return one explicitly named adapter."""
        try:
            return self._adapters[engine_id]
        except KeyError as error:
            raise EngineNotFoundError(engine_id) from error

    def contains(self, engine_id: str) -> bool:
        return engine_id in self._adapters

    def has(self, engine_id: str) -> bool:
        """Canonical V1 spelling for contains()."""
        return self.contains(engine_id)

    def engine_ids(self) -> tuple[str, ...]:
        """Return registered engine ids in deterministic insertion order."""
        return tuple(self._adapters)

    def list(self) -> tuple[str, ...]:
        """Canonical V1 registry inspection method."""
        return self.engine_ids()

    def capabilities(self, engine_id: str):
        """Return the immutable capability set for one engine."""
        return self.get(engine_id).descriptor.capabilities
