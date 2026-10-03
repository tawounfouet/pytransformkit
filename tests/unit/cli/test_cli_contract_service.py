from __future__ import annotations

import pytest

from pytransformkit.cli.exceptions import CLIUsageError
from pytransformkit.cli.services.contracts import ContractInspectionService


def test_contract_catalogue_has_deterministic_candidate_ids() -> None:
    report = ContractInspectionService().list()

    assert [contract.id for contract in report.contracts] == [
        "public-api",
        "errors",
        "schema-wire",
        "cli",
    ]
    assert [contract.status for contract in report.contracts] == [
        "stable",
        "stable",
        "stable",
        "candidate",
    ]


def test_public_api_contract_comes_from_packaged_v1_1_snapshot() -> None:
    report = ContractInspectionService().inspect("public-api")

    assert report.contract.id == "public-api"
    assert report.contract.status == "stable"
    assert report.contract.version == "2"
    assert report.document["snapshot_version"] == 2
    assert report.document["framework_line"] == "1.1.x"
    assert report.document["predecessor"] == "contracts/public_api_v1.json"


def test_error_contract_comes_from_packaged_v1_1_catalogue() -> None:
    report = ContractInspectionService().inspect("errors")

    assert report.contract.id == "errors"
    assert report.document["catalogue_version"] == 2
    assert report.document["contract"] == "pytransformkit.errors.v1"
    entries = report.document["entries"]
    assert isinstance(entries, dict)
    assert entries["DeclarativeSchemaDependencyError"]["code"] == "PTK-DECL-010"


def test_schema_wire_contract_uses_runtime_schema_codec_authority() -> None:
    report = ContractInspectionService().inspect("schema-wire")

    assert report.document == {
        "codec": "SchemaCodec",
        "contract": "pytransformkit.schema",
        "contract_version": 1,
    }


def test_cli_contract_is_explicitly_candidate_until_lot_55_freeze() -> None:
    report = ContractInspectionService().inspect("cli")

    assert report.contract.status == "candidate"
    assert report.document["cli_contract_version"] == 1
    assert report.document["report_contract_version"] == 1
    assert report.document["program"] == "ptk"
    assert report.document["commands"] == [
        "version",
        "doctor",
        "schema.validate",
        "schema.inspect",
        "schema.format",
        "schema.convert",
        "engines.list",
        "engines.inspect",
        "contract.inspect",
    ]
    assert report.document["exit_codes"]["invalid_usage"] == 2
    assert "filesystem_error" in report.document["error_categories"]


def test_contract_inspect_normalizes_case_and_whitespace() -> None:
    report = ContractInspectionService().inspect("  SCHEMA-WIRE  ")

    assert report.contract.id == "schema-wire"


def test_unknown_contract_is_usage_error() -> None:
    with pytest.raises(CLIUsageError, match="Unknown contract id"):
        ContractInspectionService().inspect("runtime")
