"""Fingerprint value object."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Fingerprint:
    """Stable reference to a fingerprint computed elsewhere."""

    algorithm: str
    value: str

    def __post_init__(self) -> None:
        if not self.algorithm or not self.algorithm.strip():
            raise ValueError("Fingerprint algorithm must not be empty.")
        if not self.value or not self.value.strip():
            raise ValueError("Fingerprint value must not be empty.")
