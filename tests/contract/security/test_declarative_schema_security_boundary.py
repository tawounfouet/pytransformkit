from __future__ import annotations

import builtins
import importlib
import os
import socket
import urllib.request

import pytest

from pytransformkit.errors import (
    DeclarativeSchemaParseError,
    DeclarativeSchemaTypeError,
    DeclarativeSchemaUnknownPropertyError,
)
from pytransformkit.schema_io import loads_schema

yaml = pytest.importorskip("yaml")


def _safe_loader_snapshot() -> tuple[
    dict[object, object],
    dict[object, object],
    dict[object, tuple[tuple[str, str, int | None], ...]],
]:
    resolvers = {
        initial: tuple(
            (
                tag,
                getattr(pattern, "pattern", repr(pattern)),
                getattr(pattern, "flags", None),
            )
            for tag, pattern in entries
        )
        for initial, entries in yaml.SafeLoader.yaml_implicit_resolvers.items()
    }
    return (
        dict(yaml.SafeLoader.yaml_constructors),
        dict(yaml.SafeLoader.yaml_multi_constructors),
        resolvers,
    )


def test_alias_amplification_is_rejected_before_construction() -> None:
    payload = """
version: 1
bomb: &level0 ["x", "x", "x", "x", "x", "x", "x", "x"]
level1: &level1 [*level0, *level0, *level0, *level0]
level2: &level2 [*level1, *level1, *level1, *level1]
schema:
  name: sample
  fields: []
"""

    with pytest.raises(DeclarativeSchemaParseError, match="anchors are forbidden"):
        loads_schema(payload)


def test_include_looking_property_never_triggers_secondary_file_read(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[object, ...]] = []

    def forbidden_open(*args: object, **kwargs: object) -> object:
        calls.append(args)
        raise AssertionError("declarative parsing must not open secondary files")

    monkeypatch.setattr(builtins, "open", forbidden_open)

    with pytest.raises(DeclarativeSchemaUnknownPropertyError):
        loads_schema(
            """
version: 1
include: /etc/passwd
schema:
  name: sample
  fields: []
"""
        )

    assert calls == []


def test_url_looking_scalar_never_triggers_network_access(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden_network(*args: object, **kwargs: object) -> object:
        raise AssertionError("declarative parsing must not access the network")

    monkeypatch.setattr(urllib.request, "urlopen", forbidden_network)
    monkeypatch.setattr(socket, "create_connection", forbidden_network)

    schema = loads_schema(
        """
version: 1
schema:
  name: sample
  fields:
    - name: endpoint
      type: string
      description: "https://example.invalid/schema.yml"
"""
    )

    assert schema.fields[0].description == "https://example.invalid/schema.yml"


def test_environment_looking_scalar_is_literal_and_never_resolved(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PTK_DECL_SECRET", "must-not-be-read")

    def forbidden_getenv(*args: object, **kwargs: object) -> object:
        raise AssertionError(
            "declarative parsing must not resolve environment variables"
        )

    monkeypatch.setattr(os, "getenv", forbidden_getenv)

    schema = loads_schema(
        """
version: 1
schema:
  name: sample
  fields:
    - name: value
      type: string
      description: "${PTK_DECL_SECRET}"
"""
    )

    assert schema.fields[0].description == "${PTK_DECL_SECRET}"


def test_plugin_like_type_fails_closed_without_dynamic_plugin_or_engine_import(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    real_import_module = importlib.import_module
    attempted_runtime_imports: list[str] = []

    def guarded_import(name: str, package: str | None = None) -> object:
        if name.startswith(("pytransformkit.plugins", "pytransformkit.engines")):
            attempted_runtime_imports.append(name)
            raise AssertionError("schema loading must not activate plugins or engines")
        return real_import_module(name, package)

    monkeypatch.setattr(importlib, "import_module", guarded_import)

    with pytest.raises(DeclarativeSchemaTypeError) as error:
        loads_schema(
            """
version: 1
schema:
  name: sample
  fields:
    - name: value
      type: "plugin://example/custom"
"""
        )

    assert error.value.type_name == "plugin://example/custom"
    assert attempted_runtime_imports == []


def test_pyyaml_global_loader_tables_are_byte_for_byte_logically_unchanged() -> None:
    before = _safe_loader_snapshot()

    schema = loads_schema(
        """
version: 1
schema:
  name: sample
  fields:
    - name: value
      type: string
      nullable: false
"""
    )
    assert schema.fields[0].nullable is False

    with pytest.raises(DeclarativeSchemaParseError):
        loads_schema(
            """
version: 1
schema:
  name: sample
  fields:
    - name: value
      type: !Forbidden {}
"""
        )

    after = _safe_loader_snapshot()
    assert after == before
