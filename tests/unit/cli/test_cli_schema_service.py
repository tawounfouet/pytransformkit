from __future__ import annotations

from pathlib import Path

import pytest

from pytransformkit.cli.exceptions import CLIUnsupportedOperationError
from pytransformkit.cli.models.reports import SchemaValidationReport
from pytransformkit.cli.services import schema as schema_service


def test_schema_validate_delegates_to_public_load_schema(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: list[str] = []

    def fake_load_schema(path: str) -> object:
        seen.append(path)
        return object()

    monkeypatch.setattr(schema_service, "load_schema", fake_load_schema)

    report = schema_service.SchemaCLIService().validate("schemas/customers.yml")

    assert seen == ["schemas/customers.yml"]
    assert report == SchemaValidationReport(
        path="schemas/customers.yml",
        valid=True,
    )


@pytest.mark.parametrize(
    "uri",
    [
        "https://example.com/schema.yml",
        "HTTP://example.com/schema.yml",
        "s3://bucket/schema.yml",
        "gs://bucket/schema.yml",
        "azure://container/schema.yml",
        "ftp://example.com/schema.yml",
        "ssh://host/schema.yml",
    ],
)
def test_schema_validate_rejects_remote_sources_before_loading(
    monkeypatch: pytest.MonkeyPatch,
    uri: str,
) -> None:
    called = False

    def forbidden_load(path: str) -> object:
        nonlocal called
        called = True
        return object()

    monkeypatch.setattr(schema_service, "load_schema", forbidden_load)

    with pytest.raises(CLIUnsupportedOperationError):
        schema_service.SchemaCLIService().validate(uri)

    assert called is False


def test_windows_like_local_path_is_not_misclassified_as_remote(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: list[str] = []

    def fake_load_schema(path: str) -> object:
        seen.append(path)
        return object()

    monkeypatch.setattr(schema_service, "load_schema", fake_load_schema)

    report = schema_service.SchemaCLIService().validate(r"C:\schemas\customers.yml")

    assert seen == [r"C:\schemas\customers.yml"]
    assert report.valid is True


def test_pathlike_is_preserved_as_explicit_local_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: list[str] = []

    def fake_load_schema(path: str) -> object:
        seen.append(path)
        return object()

    monkeypatch.setattr(schema_service, "load_schema", fake_load_schema)

    report = schema_service.SchemaCLIService().validate(Path("schema.yml"))

    assert seen == ["schema.yml"]
    assert report.path == "schema.yml"
