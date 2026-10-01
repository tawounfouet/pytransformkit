"""Portable physical-resource references.

ResourceReference identifies a resource without carrying an active provider
handle or raw credential material.
"""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import parse_qsl, urlsplit


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

        _reject_inline_credentials(self.locator, self.metadata)

    @property
    def portable(self) -> bool:
        return True


_SENSITIVE_LOCATOR_KEYS = frozenset(
    {
        "access_token",
        "api_key",
        "apikey",
        "authorization",
        "aws_access_key_id",
        "credential",
        "password",
        "private_key",
        "sas",
        "secret",
        "secret_key",
        "sig",
        "signature",
        "token",
        "x-amz-credential",
        "x-amz-signature",
        "x-goog-credential",
        "x-goog-signature",
    }
)


def _reject_inline_credentials(
    locator: str,
    metadata: tuple[tuple[str, str], ...],
) -> None:
    """Keep raw credential material out of portable ResourceReference values."""
    parsed = urlsplit(locator if "://" in locator else f"resource:///{locator}")

    if parsed.username is not None or parsed.password is not None:
        raise ValueError(
            "ResourceReference locator must not embed URI userinfo credentials; "
            "use CredentialReference instead."
        )

    query_keys = {
        key.lower()
        for key, _ in parse_qsl(parsed.query, keep_blank_values=True)
    }
    sensitive_query = sorted(query_keys & _SENSITIVE_LOCATOR_KEYS)
    if sensitive_query:
        raise ValueError(
            "ResourceReference locator contains credential-bearing query keys "
            f"{sensitive_query!r}; use CredentialReference instead."
        )

    metadata_keys = {key.lower() for key, _ in metadata}
    sensitive_metadata = sorted(metadata_keys & _SENSITIVE_LOCATOR_KEYS)
    if sensitive_metadata:
        raise ValueError(
            "ResourceReference metadata contains credential-bearing keys "
            f"{sensitive_metadata!r}; use CredentialReference instead."
        )
