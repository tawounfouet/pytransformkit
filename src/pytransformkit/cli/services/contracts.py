"""Installed-artifact contract inspection for the PyTransformKit CLI."""

from __future__ import annotations

import json
from dataclasses import dataclass
from importlib import resources
from typing import cast

from pytransformkit.cli.exceptions import CLIUsageError
from pytransformkit.cli.models.reports import (
    ContractInspectionReport,
    ContractListReport,
    ContractSummaryReport,
)


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
        status="stable",
        version="1",
        description="Frozen PyTransformKit 1.2 CLI public contract.",
    ),
)


class ContractInspectionService:
    """Inspect stable contract metadata from the installed package."""

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
            document = self._load_packaged_json("cli_contract_v1.json")

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


__all__ = ["ContractInspectionService"]
