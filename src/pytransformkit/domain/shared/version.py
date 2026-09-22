"""Domain version value object."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True, order=True)
class Version:
    """Simple immutable semantic version used by domain entities."""

    major: int
    minor: int
    patch: int

    def __post_init__(self) -> None:
        values = (self.major, self.minor, self.patch)
        if any(not isinstance(value, int) for value in values):
            raise TypeError("Version components must be integers.")
        if any(value < 0 for value in values):
            raise ValueError("Version components must be non-negative.")

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"
