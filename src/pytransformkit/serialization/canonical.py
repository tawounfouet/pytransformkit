"""Canonical JSON primitives for PyTransformKit wire contracts."""

from __future__ import annotations

import json
import math
import unicodedata
from collections.abc import Mapping
from typing import Any

from pytransformkit.errors.serialization import (
    InvalidWirePayloadError,
    PayloadTooLargeError,
    WireParseError,
)

DEFAULT_MAX_PAYLOAD_BYTES = 1_048_576
DEFAULT_MAX_NESTING_DEPTH = 64


def canonical_json_bytes(value: object) -> bytes:
    """Encode JSON deterministically using UTF-8, NFC text and sorted keys."""
    normalized = _normalize_json(value)
    try:
        text = json.dumps(
            normalized,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as error:
        raise InvalidWirePayloadError(
            "Value cannot be represented as canonical JSON."
        ) from error
    return text.encode("utf-8")


def canonical_json(value: object) -> str:
    """Return canonical JSON text."""
    return canonical_json_bytes(value).decode("utf-8")


def parse_json_strict(
    value: str | bytes,
    *,
    max_payload_bytes: int = DEFAULT_MAX_PAYLOAD_BYTES,
    max_nesting_depth: int = DEFAULT_MAX_NESTING_DEPTH,
) -> object:
    """Parse JSON while rejecting duplicates, non-standard numbers and excess size."""
    if isinstance(value, str):
        encoded = value.encode("utf-8")
        text = value
    elif isinstance(value, bytes):
        encoded = value
        try:
            text = value.decode("utf-8")
        except UnicodeDecodeError as error:
            raise WireParseError("Wire JSON must be valid UTF-8.") from error
    else:
        raise TypeError("Wire JSON must be str or bytes.")

    if max_payload_bytes <= 0:
        raise ValueError("max_payload_bytes must be positive.")
    if len(encoded) > max_payload_bytes:
        raise PayloadTooLargeError(
            f"Wire payload exceeds {max_payload_bytes} bytes."
        )
    if max_nesting_depth <= 0:
        raise ValueError("max_nesting_depth must be positive.")

    try:
        parsed = json.loads(
            text,
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_json_constant,
        )
    except WireParseError:
        raise
    except (json.JSONDecodeError, UnicodeError, ValueError) as error:
        raise WireParseError("Wire payload is not valid strict JSON.") from error

    _validate_depth(parsed, max_nesting_depth)
    return parsed


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise WireParseError(f"Duplicate JSON object key {key!r}.")
        result[key] = value
    return result


def _reject_json_constant(value: str) -> object:
    raise WireParseError(f"Non-standard JSON numeric constant {value!r} is forbidden.")


def _normalize_json(value: object) -> object:
    if value is None or isinstance(value, (bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise InvalidWirePayloadError(
                "NaN and Infinity are forbidden in portable JSON."
            )
        return value
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value)
    if isinstance(value, Mapping):
        normalized: dict[str, object] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise InvalidWirePayloadError(
                    "Canonical JSON object keys must be strings."
                )
            normalized_key = unicodedata.normalize("NFC", key)
            if normalized_key in normalized:
                raise InvalidWirePayloadError(
                    "Unicode normalization creates duplicate object keys."
                )
            normalized[normalized_key] = _normalize_json(item)
        return normalized
    if isinstance(value, (list, tuple)):
        return [_normalize_json(item) for item in value]
    raise InvalidWirePayloadError(
        f"Unsupported canonical JSON value {type(value).__name__!r}."
    )


def _validate_depth(value: object, limit: int, depth: int = 0) -> None:
    if depth > limit:
        raise InvalidWirePayloadError(
            f"Wire payload exceeds maximum nesting depth {limit}."
        )
    if isinstance(value, dict):
        for item in value.values():
            _validate_depth(item, limit, depth + 1)
    elif isinstance(value, list):
        for item in value:
            _validate_depth(item, limit, depth + 1)
