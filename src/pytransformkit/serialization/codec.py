"""Safe versioned codec for closed PyTransformKit semantic graphs."""

from __future__ import annotations

import base64
import hashlib
import math
from collections.abc import Mapping
from dataclasses import MISSING, fields, is_dataclass
from datetime import UTC, date, datetime, time
from decimal import Decimal, InvalidOperation
from enum import Enum
from typing import Generic, TypeVar, cast
from uuid import UUID

from pytransformkit.domain.shared.fingerprint import Fingerprint
from pytransformkit.errors.serialization import (
    InvalidWirePayloadError,
    NonPortableValueError,
    UnknownContractError,
    UnsupportedContractVersionError,
)
from pytransformkit.serialization.canonical import (
    DEFAULT_MAX_NESTING_DEPTH,
    DEFAULT_MAX_PAYLOAD_BYTES,
    canonical_json,
    canonical_json_bytes,
    parse_json_strict,
)
from pytransformkit.serialization.migrations import MigrationRegistry
from pytransformkit.serialization.registry import SemanticTypeRegistry

T = TypeVar("T")

_ENVELOPE_FIELDS = frozenset({"contract", "contract_version", "payload"})


class ContractCodec(Generic[T]):
    """Encode/decode one explicit semantic contract through canonical JSON."""

    contract: str
    contract_version: int = 1
    python_type: type[object]

    def __init__(
        self,
        *,
        registry: SemanticTypeRegistry | None = None,
        migrations: MigrationRegistry | None = None,
        max_payload_bytes: int = DEFAULT_MAX_PAYLOAD_BYTES,
        max_nesting_depth: int = DEFAULT_MAX_NESTING_DEPTH,
    ) -> None:
        if not self.contract or not self.contract.strip():
            raise ValueError("Codec contract must not be empty.")
        if self.contract_version < 1:
            raise ValueError("Codec contract_version must be >= 1.")
        if max_payload_bytes <= 0:
            raise ValueError("max_payload_bytes must be positive.")
        if max_nesting_depth <= 0:
            raise ValueError("max_nesting_depth must be positive.")
        self._registry = registry or SemanticTypeRegistry.default()
        self._migrations = migrations or MigrationRegistry()
        self._max_payload_bytes = max_payload_bytes
        self._max_nesting_depth = max_nesting_depth

    def to_dict(self, value: T) -> dict[str, object]:
        """Return the versioned envelope as a JSON-compatible mapping."""
        self._validate_python_type(value)
        return {
            "contract": self.contract,
            "contract_version": self.contract_version,
            "payload": _encode_value(value, self._registry),
        }

    def to_json(self, value: T) -> str:
        """Return deterministic canonical JSON."""
        return canonical_json(self.to_dict(value))

    def to_bytes(self, value: T) -> bytes:
        """Return deterministic canonical UTF-8 bytes."""
        return canonical_json_bytes(self.to_dict(value))

    def from_dict(self, envelope: Mapping[str, object]) -> T:
        """Decode an already parsed envelope with strict field validation."""
        if not isinstance(envelope, Mapping):
            raise InvalidWirePayloadError("Wire envelope must be a JSON object.")
        fields_present = frozenset(envelope)
        if fields_present != _ENVELOPE_FIELDS:
            missing = sorted(_ENVELOPE_FIELDS - fields_present)
            unknown = sorted(fields_present - _ENVELOPE_FIELDS)
            raise InvalidWirePayloadError(
                "Wire envelope fields are invalid. "
                f"missing={missing!r}, unknown={unknown!r}."
            )

        contract = envelope["contract"]
        version = envelope["contract_version"]
        if not isinstance(contract, str):
            raise InvalidWirePayloadError("contract must be a string.")
        if contract != self.contract:
            raise UnknownContractError(
                f"Expected contract {self.contract!r}, received {contract!r}."
            )
        if isinstance(version, bool) or not isinstance(version, int):
            raise InvalidWirePayloadError("contract_version must be an integer.")
        if version < 1:
            raise InvalidWirePayloadError("contract_version must be >= 1.")

        payload = envelope["payload"]
        if version > self.contract_version:
            raise UnsupportedContractVersionError(
                f"{self.contract!r} v{version} is newer than supported "
                f"v{self.contract_version}."
            )
        if version < self.contract_version:
            payload = self._migrations.migrate(
                self.contract,
                version,
                self.contract_version,
                payload,
            )

        decoded = _decode_value(payload, self._registry)
        self._validate_python_type(decoded)
        return cast(T, decoded)

    def from_json(self, value: str | bytes) -> T:
        """Parse and decode strict JSON without code execution or implicit I/O."""
        parsed = parse_json_strict(
            value,
            max_payload_bytes=self._max_payload_bytes,
            max_nesting_depth=self._max_nesting_depth,
        )
        if not isinstance(parsed, dict):
            raise InvalidWirePayloadError("Wire envelope must be a JSON object.")
        return self.from_dict(parsed)

    def fingerprint(self, value: T) -> Fingerprint:
        """Fingerprint this contract's canonical semantic bytes."""
        digest = hashlib.sha256(self.to_bytes(value)).hexdigest()
        return Fingerprint("sha256", digest)

    def _validate_python_type(self, value: object) -> None:
        if not isinstance(value, self.python_type):
            raise TypeError(
                f"{type(self).__name__} requires {self.python_type.__name__}, "
                f"received {type(value).__name__}."
            )


def _encode_value(
    value: object,
    registry: SemanticTypeRegistry,
) -> object:
    if isinstance(value, Enum):
        return {
            "$enum": registry.type_id_for(value),
            "value": _encode_value(value.value, registry),
        }

    if value is None or isinstance(value, (bool, int, str)):
        return value

    if isinstance(value, float):
        if not math.isfinite(value):
            raise NonPortableValueError(
                "NaN and Infinity are not portable literal values."
            )
        return value

    if isinstance(value, Decimal):
        if not value.is_finite():
            raise NonPortableValueError(
                "Non-finite Decimal values are not portable."
            )
        return {"$decimal": str(value)}

    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise NonPortableValueError(
                "Naive datetimes are forbidden in durable wire contracts."
            )
        normalized = value.astimezone(UTC).isoformat(timespec="microseconds")
        return {"$datetime": normalized.replace("+00:00", "Z")}

    if isinstance(value, date):
        return {"$date": value.isoformat()}

    if isinstance(value, time):
        if value.tzinfo is not None and value.utcoffset() is None:
            raise NonPortableValueError("Invalid time timezone information.")
        return {"$time": value.isoformat(timespec="microseconds")}

    if isinstance(value, UUID):
        return {"$uuid": str(value)}

    if isinstance(value, bytes):
        return {
            "$bytes": base64.b64encode(value).decode("ascii"),
            "encoding": "base64",
        }

    if is_dataclass(value) and not isinstance(value, type):
        type_id = registry.type_id_for(value)
        encoded_fields = {
            field.name: _encode_value(getattr(value, field.name), registry)
            for field in fields(value)
            if field.init
        }
        return {
            "$type": type_id,
            "fields": encoded_fields,
        }

    if isinstance(value, tuple):
        return {"$tuple": [_encode_value(item, registry) for item in value]}

    if isinstance(value, list):
        return {"$list": [_encode_value(item, registry) for item in value]}

    if isinstance(value, frozenset):
        items = [_encode_value(item, registry) for item in value]
        return {"$frozenset": _sorted_encoded(items)}

    if isinstance(value, set):
        items = [_encode_value(item, registry) for item in value]
        return {"$set": _sorted_encoded(items)}

    if isinstance(value, Mapping):
        pairs = [
            [_encode_value(key, registry), _encode_value(item, registry)]
            for key, item in value.items()
        ]
        pairs.sort(key=lambda pair: canonical_json(pair[0]))
        return {"$map": pairs}

    if callable(value):
        raise NonPortableValueError(
            "Callbacks, closures and arbitrary callables are not portable."
        )

    raise NonPortableValueError(
        f"Value of type {type(value).__name__!r} is not portable."
    )


def _decode_value(
    value: object,
    registry: SemanticTypeRegistry,
) -> object:
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise InvalidWirePayloadError("Non-finite JSON numbers are forbidden.")
        return value
    if isinstance(value, list):
        raise InvalidWirePayloadError(
            "Raw arrays are not valid typed values; "
            "an explicit collection tag is required."
        )
    if not isinstance(value, dict):
        raise InvalidWirePayloadError(
            f"Unsupported wire value type {type(value).__name__!r}."
        )

    if "$decimal" in value:
        _require_exact_keys(value, {"$decimal"})
        raw = value["$decimal"]
        if not isinstance(raw, str):
            raise InvalidWirePayloadError("$decimal must be a string.")
        try:
            decimal = Decimal(raw)
        except InvalidOperation as error:
            raise InvalidWirePayloadError("Invalid Decimal wire value.") from error
        if not decimal.is_finite():
            raise InvalidWirePayloadError("Non-finite Decimal values are forbidden.")
        return decimal

    if "$datetime" in value:
        _require_exact_keys(value, {"$datetime"})
        raw = value["$datetime"]
        if not isinstance(raw, str):
            raise InvalidWirePayloadError("$datetime must be a string.")
        try:
            parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError as error:
            raise InvalidWirePayloadError("Invalid RFC 3339 datetime.") from error
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise InvalidWirePayloadError("Durable datetime must be timezone-aware.")
        return parsed

    if "$date" in value:
        _require_exact_keys(value, {"$date"})
        raw = value["$date"]
        if not isinstance(raw, str):
            raise InvalidWirePayloadError("$date must be a string.")
        try:
            return date.fromisoformat(raw)
        except ValueError as error:
            raise InvalidWirePayloadError("Invalid ISO 8601 date.") from error

    if "$time" in value:
        _require_exact_keys(value, {"$time"})
        raw = value["$time"]
        if not isinstance(raw, str):
            raise InvalidWirePayloadError("$time must be a string.")
        try:
            return time.fromisoformat(raw)
        except ValueError as error:
            raise InvalidWirePayloadError("Invalid ISO 8601 time.") from error

    if "$uuid" in value:
        _require_exact_keys(value, {"$uuid"})
        raw = value["$uuid"]
        if not isinstance(raw, str):
            raise InvalidWirePayloadError("$uuid must be a string.")
        try:
            return UUID(raw)
        except ValueError as error:
            raise InvalidWirePayloadError("Invalid UUID wire value.") from error

    if "$bytes" in value:
        _require_exact_keys(value, {"$bytes", "encoding"})
        raw = value["$bytes"]
        encoding = value["encoding"]
        if encoding != "base64" or not isinstance(raw, str):
            raise InvalidWirePayloadError("Binary wire values require base64 encoding.")
        try:
            return base64.b64decode(raw.encode("ascii"), validate=True)
        except (ValueError, UnicodeEncodeError) as error:
            raise InvalidWirePayloadError("Invalid base64 wire value.") from error

    if "$enum" in value:
        _require_exact_keys(value, {"$enum", "value"})
        type_id = value["$enum"]
        if not isinstance(type_id, str):
            raise InvalidWirePayloadError("$enum must be a semantic type ID string.")
        cls = registry.type_for(type_id)
        if not issubclass(cls, Enum):
            raise InvalidWirePayloadError(
                f"Semantic type {type_id!r} is not an enum."
            )
        enum_value = _decode_value(value["value"], registry)
        try:
            return cls(enum_value)
        except (TypeError, ValueError) as error:
            raise InvalidWirePayloadError(
                f"Invalid value for enum {type_id!r}."
            ) from error

    if "$type" in value:
        _require_exact_keys(value, {"$type", "fields"})
        type_id = value["$type"]
        raw_fields = value["fields"]
        if not isinstance(type_id, str):
            raise InvalidWirePayloadError("$type must be a semantic type ID string.")
        if not isinstance(raw_fields, dict):
            raise InvalidWirePayloadError("Typed value fields must be an object.")

        cls = registry.type_for(type_id)
        if not is_dataclass(cls):
            raise InvalidWirePayloadError(
                f"Semantic type {type_id!r} is not a dataclass."
            )
        dataclass_fields = {field.name: field for field in fields(cls) if field.init}
        supplied = set(raw_fields)
        known = set(dataclass_fields)
        unknown = sorted(supplied - known)
        missing = sorted(
            name
            for name, field in dataclass_fields.items()
            if name not in supplied
            and field.default is MISSING
            and field.default_factory is MISSING
        )
        if unknown or missing:
            raise InvalidWirePayloadError(
                f"Fields for {type_id!r} are invalid. "
                f"missing={missing!r}, unknown={unknown!r}."
            )

        kwargs = {
            name: _decode_value(raw_fields[name], registry)
            for name in supplied
        }
        try:
            return cls(**kwargs)
        except Exception as error:
            raise InvalidWirePayloadError(
                f"Semantic validation failed for {type_id!r}."
            ) from error

    for marker, factory in (
        ("$tuple", tuple),
        ("$list", list),
        ("$frozenset", frozenset),
        ("$set", set),
    ):
        if marker in value:
            _require_exact_keys(value, {marker})
            raw_items = value[marker]
            if not isinstance(raw_items, list):
                raise InvalidWirePayloadError(f"{marker} must contain a JSON array.")
            decoded = [_decode_value(item, registry) for item in raw_items]
            return factory(decoded)

    if "$map" in value:
        _require_exact_keys(value, {"$map"})
        raw_pairs = value["$map"]
        if not isinstance(raw_pairs, list):
            raise InvalidWirePayloadError("$map must contain a JSON array.")
        result: dict[object, object] = {}
        for raw_pair in raw_pairs:
            if not isinstance(raw_pair, list) or len(raw_pair) != 2:
                raise InvalidWirePayloadError(
                    "$map entries must be two-element arrays."
                )
            key = _decode_value(raw_pair[0], registry)
            item = _decode_value(raw_pair[1], registry)
            try:
                if key in result:
                    raise InvalidWirePayloadError(
                        "Decoded map contains a duplicate key."
                    )
                result[key] = item
            except TypeError as error:
                raise InvalidWirePayloadError(
                    "Decoded map key is not hashable."
                ) from error
        return result

    raise InvalidWirePayloadError(
        "Untyped JSON objects are forbidden inside semantic payloads."
    )


def _require_exact_keys(
    value: Mapping[str, object],
    expected: set[str],
) -> None:
    supplied = set(value)
    if supplied != expected:
        raise InvalidWirePayloadError(
            "Tagged wire value contains invalid fields. "
            f"expected={sorted(expected)!r}, supplied={sorted(supplied)!r}."
        )


def _sorted_encoded(items: list[object]) -> list[object]:
    return sorted(items, key=canonical_json)
