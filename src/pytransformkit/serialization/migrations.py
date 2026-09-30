"""Explicit version-to-version wire migration hooks."""

from __future__ import annotations

from collections.abc import Callable

from pytransformkit.errors.serialization import (
    MigrationError,
    UnsupportedContractVersionError,
)

Migration = Callable[[object], object]


class MigrationRegistry:
    """Registry of explicit one-version-forward migration functions."""

    def __init__(self) -> None:
        self._migrations: dict[tuple[str, int], Migration] = {}

    def register(
        self,
        contract: str,
        from_version: int,
        migration: Migration,
    ) -> None:
        if not contract or not contract.strip():
            raise ValueError("contract must not be empty.")
        if from_version < 1:
            raise ValueError("from_version must be >= 1.")
        if not callable(migration):
            raise TypeError("migration must be callable.")
        key = (contract, from_version)
        if key in self._migrations:
            raise ValueError(
                f"Migration already registered for {contract!r} v{from_version}."
            )
        self._migrations[key] = migration

    def migrate(
        self,
        contract: str,
        from_version: int,
        to_version: int,
        payload: object,
    ) -> object:
        """Apply an explicit contiguous migration chain."""
        if from_version > to_version:
            raise UnsupportedContractVersionError(
                "Wire downgrade is not implicit; use an explicit older writer."
            )
        current = from_version
        value = payload
        while current < to_version:
            migration = self._migrations.get((contract, current))
            if migration is None:
                raise UnsupportedContractVersionError(
                    f"No migration path for {contract!r} v{current} → v{current + 1}."
                )
            try:
                value = migration(value)
            except Exception as error:
                raise MigrationError(
                    f"Migration failed for {contract!r} v{current} → v{current + 1}."
                ) from error
            current += 1
        return value
