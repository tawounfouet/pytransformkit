"""Explicit engine adapter registry."""

from pytransformkit.application.ports.engines import EngineAdapter
from pytransformkit.errors.engine import EngineNotFoundError


class EngineRegistry:
    """Mutable application registry with no implicit fallback behavior."""

    def __init__(self) -> None:
        self._adapters: dict[str, EngineAdapter] = {}

    def register(self, adapter: EngineAdapter) -> None:
        """Register or replace an adapter by explicit engine id."""
        engine_id = adapter.descriptor.id
        self._adapters[engine_id] = adapter

    def get(self, engine_id: str) -> EngineAdapter:
        """Return one explicitly named adapter."""
        try:
            return self._adapters[engine_id]
        except KeyError as error:
            raise EngineNotFoundError(engine_id) from error

    def contains(self, engine_id: str) -> bool:
        return engine_id in self._adapters

    def engine_ids(self) -> tuple[str, ...]:
        """Return registered engine ids in deterministic insertion order."""
        return tuple(self._adapters)
