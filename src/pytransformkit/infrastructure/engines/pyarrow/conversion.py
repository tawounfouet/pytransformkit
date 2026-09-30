"""Explicit Arrow interchange bridges and lossiness diagnostics."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

import pyarrow as pa

from pytransformkit.domain.runtime import Diagnostic, DiagnosticSeverity
from pytransformkit.errors.engine import AdapterError
from pytransformkit.infrastructure.engines.pyarrow.handle import (
    PyArrowDatasetHandle,
)


class ConversionPolicy(StrEnum):
    """How interchange handles conversions with known semantic risk."""

    STRICT = "strict"
    ALLOW_POTENTIALLY_LOSSY = "allow_potentially_lossy"


class ConversionLossiness(StrEnum):
    """Observed/known conversion fidelity."""

    LOSSLESS = "lossless"
    POTENTIALLY_LOSSY = "potentially_lossy"


@dataclass(frozen=True, slots=True)
class ArrowConversionResult:
    """Converted value plus explicit conversion evidence."""

    value: Any
    lossiness: ConversionLossiness
    diagnostics: tuple[Diagnostic, ...] = ()


class PyArrowInterchange:
    """Bridges Pandas/Polars through Arrow without making Arrow a Domain type."""

    @staticmethod
    def from_pandas(
        dataframe: Any,
        *,
        policy: ConversionPolicy = ConversionPolicy.STRICT,
    ) -> ArrowConversionResult:
        import pandas as pd

        if not isinstance(dataframe, pd.DataFrame):
            raise TypeError("from_pandas requires a pandas.DataFrame.")

        diagnostics = tuple(
            _potentially_lossy(
                "PTK-ARROW-CONV-001",
                f"Pandas object dtype on column {name!r} requires Arrow inference.",
                related_field=str(name),
            )
            for name, dtype in dataframe.dtypes.items()
            if str(dtype) == "object"
        )
        _enforce(policy, diagnostics)
        table = pa.Table.from_pandas(dataframe, preserve_index=False)
        return ArrowConversionResult(
            value=PyArrowDatasetHandle(table),
            lossiness=_lossiness(diagnostics),
            diagnostics=diagnostics,
        )

    @staticmethod
    def to_pandas(
        value: PyArrowDatasetHandle | pa.Table | pa.RecordBatch,
        *,
        policy: ConversionPolicy = ConversionPolicy.STRICT,
    ) -> ArrowConversionResult:
        table = _table(value)
        diagnostics = tuple(
            _potentially_lossy(
                "PTK-ARROW-CONV-002",
                (
                    f"Arrow field {field.name!r} uses {field.type}; "
                    "Pandas may preserve values while changing dtype representation."
                ),
                related_field=field.name,
            )
            for field in table.schema
            if _pandas_risky(field.type)
        )
        _enforce(policy, diagnostics)
        return ArrowConversionResult(
            value=table.to_pandas(),
            lossiness=_lossiness(diagnostics),
            diagnostics=diagnostics,
        )

    @staticmethod
    def from_polars(
        frame: Any,
        *,
        policy: ConversionPolicy = ConversionPolicy.STRICT,
    ) -> ArrowConversionResult:
        import polars as pl

        if not isinstance(frame, pl.DataFrame):
            raise TypeError(
                "from_polars requires a materialized polars.DataFrame; "
                "LazyFrame collection must be explicit at the caller boundary."
            )

        table = frame.to_arrow()
        diagnostics = tuple(
            _potentially_lossy(
                "PTK-ARROW-CONV-003",
                f"Arrow dictionary field {field.name!r} may encode Polars categoricals.",
                related_field=field.name,
            )
            for field in table.schema
            if pa.types.is_dictionary(field.type)
        )
        _enforce(policy, diagnostics)
        return ArrowConversionResult(
            value=PyArrowDatasetHandle(table),
            lossiness=_lossiness(diagnostics),
            diagnostics=diagnostics,
        )

    @staticmethod
    def to_polars(
        value: PyArrowDatasetHandle | pa.Table | pa.RecordBatch,
        *,
        policy: ConversionPolicy = ConversionPolicy.STRICT,
    ) -> ArrowConversionResult:
        import polars as pl

        table = _table(value)
        diagnostics = tuple(
            _potentially_lossy(
                "PTK-ARROW-CONV-004",
                (
                    f"Arrow field {field.name!r} uses {field.type}; "
                    "Polars representation may not preserve all Arrow metadata."
                ),
                related_field=field.name,
            )
            for field in table.schema
            if _polars_risky(field.type)
        )
        _enforce(policy, diagnostics)
        return ArrowConversionResult(
            value=pl.from_arrow(table),
            lossiness=_lossiness(diagnostics),
            diagnostics=diagnostics,
        )


def _table(value: PyArrowDatasetHandle | pa.Table | pa.RecordBatch) -> pa.Table:
    if isinstance(value, PyArrowDatasetHandle):
        return value.table
    if isinstance(value, pa.Table):
        return value
    if isinstance(value, pa.RecordBatch):
        return pa.Table.from_batches([value])
    raise TypeError("Arrow conversion requires an Arrow handle, Table, or RecordBatch.")


def _pandas_risky(dtype: pa.DataType) -> bool:
    return (
        pa.types.is_decimal(dtype)
        or pa.types.is_list(dtype)
        or pa.types.is_large_list(dtype)
        or pa.types.is_struct(dtype)
        or pa.types.is_map(dtype)
        or pa.types.is_dictionary(dtype)
    )


def _polars_risky(dtype: pa.DataType) -> bool:
    return (
        pa.types.is_map(dtype)
        or pa.types.is_union(dtype)
        or pa.types.is_dictionary(dtype)
    )


def _potentially_lossy(
    code: str,
    summary: str,
    *,
    related_field: str,
) -> Diagnostic:
    return Diagnostic(
        code=code,
        severity=DiagnosticSeverity.WARNING,
        summary=summary,
        source_component="pyarrow.interchange",
        related_field=related_field,
    )


def _lossiness(
    diagnostics: tuple[Diagnostic, ...],
) -> ConversionLossiness:
    if diagnostics:
        return ConversionLossiness.POTENTIALLY_LOSSY
    return ConversionLossiness.LOSSLESS


def _enforce(
    policy: ConversionPolicy,
    diagnostics: tuple[Diagnostic, ...],
) -> None:
    if not isinstance(policy, ConversionPolicy):
        raise TypeError("policy must be a ConversionPolicy.")
    if policy is ConversionPolicy.STRICT and diagnostics:
        fields = ", ".join(
            diagnostic.related_field or "<unknown>" for diagnostic in diagnostics
        )
        raise AdapterError(
            "Strict Arrow conversion rejected a potentially lossy conversion "
            f"for fields: {fields}."
        )
