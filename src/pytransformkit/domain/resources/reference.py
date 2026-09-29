"""Portable physical-resource references.

ResourceReference identifies a resource without carrying an active provider
handle or raw credential material.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ResourceReference:
    """Portable identity/location contract for one physical resource."""

    scheme: str
    locator: str
    media_type: str | None = None
    metadata: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        if not self.scheme or not self.scheme.strip():
            raise ValueError("ResourceReference scheme must not be empty.")
        if not self.locator or not self.locator.strip():
            raise ValueError("ResourceReference locator must not be empty.")
        if self.media_type is not None and not self.media_type.strip():
            raise ValueError("ResourceReference media_type must not be blank.")
        if not isinstance(self.metadata, tuple):
            raise TypeError("ResourceReference metadata must be a tuple.")
        for item in self.metadata:
            if (
                not isinstance(item, tuple)
                or len(item) != 2
                or not all(isinstance(value, str) for value in item)
            ):
                raise TypeError(
                    "ResourceReference metadata must contain string key/value pairs."
                )

    @property
    def portable(self) -> bool:
        return True
