"""Portable credential references without secret material."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CredentialReference:
    """Reference to runtime-resolved credentials, never the credential value."""

    credential_id: str
    provider: str | None = None

    def __post_init__(self) -> None:
        if not self.credential_id or not self.credential_id.strip():
            raise ValueError("CredentialReference credential_id must not be empty.")
        if self.provider is not None and not self.provider.strip():
            raise ValueError("CredentialReference provider must not be blank.")

    @property
    def portable(self) -> bool:
        return True
