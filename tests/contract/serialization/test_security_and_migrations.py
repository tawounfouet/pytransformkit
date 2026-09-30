from __future__ import annotations

from pathlib import Path

import pytest

from pytransformkit import ResourceReference
from pytransformkit.domain.expressions.literals import Literal
from pytransformkit.errors import (
    InvalidWirePayloadError,
    NonPortableValueError,
    PayloadTooLargeError,
    UnsupportedContractVersionError,
    WireParseError,
)
from pytransformkit.serialization import (
    ExpressionCodec,
    MigrationRegistry,
    ResourceReferenceCodec,
    canonical_json,
)


class _ResourceReferenceV2Codec(ResourceReferenceCodec):
    contract_version = 2


def _resource() -> ResourceReference:
    return ResourceReference(
        scheme="file",
        locator="data/orders.parquet",
        media_type="application/vnd.apache.parquet",
    )


def test_duplicate_json_keys_are_rejected_before_domain_construction() -> None:
    payload = (
        '{"contract":"pykit.resource_reference",'
        '"contract":"pykit.resource_reference",'
        '"contract_version":1,"payload":null}'
    )

    with pytest.raises(WireParseError, match="Duplicate JSON object key"):
        ResourceReferenceCodec().from_json(payload)


def test_payload_limit_is_enforced_before_json_parsing() -> None:
    encoded = ResourceReferenceCodec().to_json(_resource())

    with pytest.raises(PayloadTooLargeError):
        ResourceReferenceCodec(max_payload_bytes=32).from_json(encoded)


def test_unknown_semantic_type_cannot_trigger_arbitrary_import_or_construction() -> None:
    envelope = {
        "contract": "pykit.resource_reference",
        "contract_version": 1,
        "payload": {
            "$type": "python.os.system",
            "fields": {},
        },
    }

    with pytest.raises(InvalidWirePayloadError, match="Unknown semantic wire type"):
        ResourceReferenceCodec().from_json(canonical_json(envelope))


def test_unknown_typed_fields_are_rejected_strictly() -> None:
    codec = ResourceReferenceCodec()
    envelope = codec.to_dict(_resource())
    payload = envelope["payload"]
    assert isinstance(payload, dict)
    raw_fields = payload["fields"]
    assert isinstance(raw_fields, dict)
    raw_fields["credential"] = "secret"

    with pytest.raises(InvalidWirePayloadError, match="unknown"):
        codec.from_dict(envelope)


def test_non_portable_callback_literal_fails_explicitly() -> None:
    expression = Literal(lambda value: value)

    with pytest.raises(NonPortableValueError, match="callable"):
        ExpressionCodec().to_json(expression)


def test_future_contract_versions_never_fall_back_to_current_semantics() -> None:
    envelope = ResourceReferenceCodec().to_dict(_resource())
    envelope["contract_version"] = 99

    with pytest.raises(UnsupportedContractVersionError):
        ResourceReferenceCodec().from_dict(envelope)


def test_explicit_migration_hook_can_upgrade_known_older_contract() -> None:
    migrations = MigrationRegistry()
    migrations.register(
        "pykit.resource_reference",
        1,
        lambda payload: payload,
    )
    old_payload = ResourceReferenceCodec().to_json(_resource())

    decoded = _ResourceReferenceV2Codec(migrations=migrations).from_json(old_payload)

    assert decoded == _resource()


def test_pickle_payload_is_not_treated_as_a_python_object_graph() -> None:
    pickle_header = b"\x80\x04}q\x00."

    with pytest.raises(WireParseError):
        ResourceReferenceCodec().from_json(pickle_header)


def test_serialization_package_has_no_pickle_eval_or_exec_decoder_fallback() -> None:
    root = Path(__file__).parents[3] / "src" / "pytransformkit" / "serialization"
    source = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted(root.glob("*.py"))
    )

    assert "import pickle" not in source
    assert "cloudpickle" not in source
    assert "dill" not in source
    assert "eval(" not in source
    assert "exec(" not in source
