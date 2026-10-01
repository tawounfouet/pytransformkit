from __future__ import annotations

import importlib.abc
import json
import socket
import subprocess
import sys
from pathlib import Path

import pytest

from pytransformkit import InputBinding, OutputBinding, ResourceReference
from pytransformkit.errors import InvalidWirePayloadError
from pytransformkit.serialization import ResourceReferenceCodec


class _BlockOptionalEngines(importlib.abc.MetaPathFinder):
    blocked = {"duckdb", "pandas", "polars", "pyarrow"}

    def find_spec(self, fullname: str, path=None, target=None):  # type: ignore[no-untyped-def]
        del path, target
        if fullname.split(".", 1)[0] in self.blocked:
            raise AssertionError(f"core import attempted optional dependency {fullname!r}")
        return None


def test_core_import_is_safe_without_optional_engines_or_network() -> None:
    code = r"""
import importlib.abc
import socket
import sys

class BlockOptionalEngines(importlib.abc.MetaPathFinder):
    blocked = {"duckdb", "pandas", "polars", "pyarrow"}

    def find_spec(self, fullname, path=None, target=None):
        if fullname.split(".", 1)[0] in self.blocked:
            raise RuntimeError(f"optional engine import: {fullname}")
        return None

def deny(*args, **kwargs):
    raise RuntimeError("network access during import")

sys.meta_path.insert(0, BlockOptionalEngines())
socket.create_connection = deny
socket.socket.connect = deny

import pytransformkit

for name in ("duckdb", "pandas", "polars", "pyarrow"):
    assert name not in sys.modules
assert "Pipeline" not in pytransformkit.__all__
assert "RunPipelineService" not in pytransformkit.__all__
"""
    subprocess.run(
        [sys.executable, "-I", "-c", code],
        check=True,
        text=True,
        capture_output=True,
    )


def test_binding_constructors_do_not_touch_filesystem(monkeypatch, tmp_path: Path) -> None:
    resource = ResourceReference(
        scheme="file",
        locator=str(tmp_path / "does-not-exist.parquet"),
    )

    def deny(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("constructor attempted physical filesystem access")

    monkeypatch.setattr(Path, "open", deny)
    monkeypatch.setattr(Path, "exists", deny)

    input_binding = InputBinding.from_resource("orders", resource)
    output_binding = OutputBinding.to_resource("orders_out", resource)

    assert input_binding.resource == resource
    assert output_binding.resource == resource


def test_resource_reference_wire_payload_cannot_embed_credentials() -> None:
    resource = ResourceReference(
        scheme="file",
        locator="orders.parquet",
        media_type="application/vnd.apache.parquet",
    )
    payload = ResourceReferenceCodec().to_json(resource)

    assert "credential" not in payload.lower()
    assert "secret" not in payload.lower()
    assert "token" not in payload.lower()


def test_wire_decoder_rejects_unknown_executable_type() -> None:
    envelope = {
        "contract": "pykit.resource_reference",
        "contract_version": 1,
        "payload": {
            "$type": "python.subprocess.popen",
            "fields": {},
        },
    }

    with pytest.raises(InvalidWirePayloadError):
        ResourceReferenceCodec().from_json(json.dumps(envelope))


def test_source_tree_has_no_executable_serialization_fallbacks() -> None:
    root = Path(__file__).parents[3] / "src" / "pytransformkit"
    forbidden = ("cloudpickle", "dill")
    pickle_import_markers = ("import pickle", "from pickle")

    for path in root.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert all(item not in text for item in forbidden), path
        assert all(item not in text for item in pickle_import_markers), path
