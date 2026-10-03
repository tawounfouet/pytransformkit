"""Installed-artifact contract inspection for the PyTransformKit CLI."""

from __future__ import annotations

import json
from dataclasses import dataclass
from importlib import resources
from typing import cast

from pytransformkit.cli.exceptions import CLIUsageError
from pytransformkit.cli.exit_codes import ExitCode
from pytransformkit.cli.models.errors import ErrorCategory
from pytransformkit.cli.models.reports import (
    ContractInspectionReport,
    ContractListReport,
    ContractSummaryReport,
)
from pytransformkit.cli.rendering.json import CLI_REPORT_CONTRACT_VERSION


@dataclass(frozen=True, slots=True)
class _ContractSpec:
    id: str
    status: str
    version: str
    description: str


_CONTRACT_SPECS: tuple[_ContractSpec, ...] = (
    _ContractSpec(
        id="public-api",
        status="stable",
        version="2",
        description="PyTransformKit 1.1 public API compatibility snapshot.",
    ),
    _ContractSpec(
        id="errors",
        status="stable",
        version="2",
        description="PyTransformKit 1.1 public error-code catalogue.",
    ),
    _ContractSpec(
        id="schema-wire",
        status="stable",
        version="1",
        description="Stable SchemaCodec wire contract.",
    ),
    _ContractSpec(
        id="cli",
        status="candidate",
        version="1",
        description="PyTransformKit 1.2 CLI candidate contract metadata.",
    ),
)

_REPORT_COMMANDS: tuple[str, ...] = (
    "version",
    "doctor",
    "schema.validate",
    "schema.inspect",
    "engines.list",
    "engines.inspect",
    "contract.inspect",
)
_PAYLOAD_COMMANDS: tuple[str, ...] = (
    "schema.format",
    "schema.convert",
)
_COMMANDS: tuple[str, ...] = (
    "version",
    "doctor",
    "schema.validate",
    "schema.inspect",
    "schema.format",
    "schema.convert",
    "engines.list",
    "engines.inspect",
    "contract.inspect",
)


class ContractInspectionService:
    """Inspect stable/candidate contract metadata from the installed package."""

    def list(self) -> ContractListReport:
        """Return inspectable contracts in deterministic public order."""
        return ContractListReport(
            contracts=tuple(self._summary(spec) for spec in _CONTRACT_SPECS)
        )

    def inspect(self, contract_id: str) -> ContractInspectionReport:
        """Return one contract document without relying on a Git checkout."""
        normalized = contract_id.strip().lower()
        spec = next(
            (candidate for candidate in _CONTRACT_SPECS if candidate.id == normalized),
            None,
        )
        if spec is None:
            known = ", ".join(candidate.id for candidate in _CONTRACT_SPECS)
            raise CLIUsageError(
                f"Unknown contract id {contract_id!r}. Known contracts: {known}."
            )

        if normalized == "public-api":
            document = self._load_packaged_json("public_api_v1_1.json")
        elif normalized == "errors":
            document = self._load_packaged_json("error_codes_v1_1.json")
        elif normalized == "schema-wire":
            document = self._schema_wire_document()
        else:
            document = self._cli_document()

        return ContractInspectionReport(
            contract=self._summary(spec),
            document=document,
        )

    @staticmethod
    def _summary(spec: _ContractSpec) -> ContractSummaryReport:
        return ContractSummaryReport(
            id=spec.id,
            status=spec.status,
            version=spec.version,
            description=spec.description,
        )

    @staticmethod
    def _load_packaged_json(filename: str) -> dict[str, object]:
        package = resources.files("pytransformkit._contract_data")
        text = package.joinpath(filename).read_text(encoding="utf-8")
        payload = json.loads(text)
        if not isinstance(payload, dict):
            raise RuntimeError(f"Packaged contract {filename!r} is not a JSON object.")
        return cast(dict[str, object], payload)

    @staticmethod
    def _schema_wire_document() -> dict[str, object]:
        from pytransformkit.serialization import SchemaCodec

        return {
            "codec": "SchemaCodec",
            "contract": SchemaCodec.contract,
            "contract_version": SchemaCodec.contract_version,
        }

    @staticmethod
    def _cli_document() -> dict[str, object]:
        return {
            "cli_contract_version": 1,
            "status": "candidate",
            "program": "ptk",
            "report_contract_version": CLI_REPORT_CONTRACT_VERSION,
            "commands": list(_COMMANDS),
            "report_commands": list(_REPORT_COMMANDS),
            "payload_commands": list(_PAYLOAD_COMMANDS),
            "exit_codes": {
                code.name.lower(): int(code)
                for code in ExitCode
            },
            "error_categories": [
                category.value
                for category in ErrorCategory
            ],
            "security": {
                "implicit_network": False,
                "plugin_command_injection": False,
                "project_discovery": False,
                "silent_overwrite": False,
            },
        }


__all__ = ["ContractInspectionService"]
