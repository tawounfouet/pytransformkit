"""Local-filesystem Reader/Writer reference profile for LOT-20."""

from __future__ import annotations

import csv
import json
import os
import tempfile
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.csv as pa_csv
import pyarrow.dataset as ds
import pyarrow.ipc as pa_ipc
import pyarrow.json as pa_json
import pyarrow.parquet as pq

from pytransformkit.application.io import (
    PushdownStatus,
    ReadPushdownEvidence,
    ReadRepresentation,
    ReadRequest,
    ReadResult,
    WriteRequest,
    WriteResult,
)
from pytransformkit.application.ports import ArrowExportablePhysicalHandle
from pytransformkit.domain.expressions.binary import BinaryExpression
from pytransformkit.domain.expressions.literals import Literal
from pytransformkit.domain.expressions.operators import BinaryOperator, UnaryOperator
from pytransformkit.domain.expressions.predicates import (
    IsNotNullExpression,
    IsNullExpression,
)
from pytransformkit.domain.expressions.references import ColumnReference
from pytransformkit.domain.expressions.unary import UnaryExpression
from pytransformkit.domain.resources import (
    ResourceFormat,
    RetrySafety,
    WriteMode,
    WriteStatus,
    infer_resource_format,
)
from pytransformkit.errors.io import (
    ResourcePathViolationError,
    ResourceReadError,
    ResourceWriteError,
    UnsupportedResourceFormatError,
)
from pytransformkit.infrastructure.engines.pyarrow.expressions import (
    PyArrowExpressionCompiler,
)
from pytransformkit.infrastructure.engines.pyarrow.types import PyArrowSchemaInspector


class LocalFilePathResolver:
    """Resolve file ResourceReference locators under one configured root."""

    def __init__(self, root: str | Path) -> None:
        root_path = Path(root).expanduser()
        self._root = root_path.resolve()

    @property
    def root(self) -> Path:
        return self._root

    def resolve(self, locator: str) -> Path:
        if not locator or not locator.strip():
            raise ResourcePathViolationError("Local resource locator must not be empty.")

        raw = Path(locator).expanduser()
        candidate = raw if raw.is_absolute() else self._root / raw
        resolved = candidate.resolve(strict=False)

        try:
            resolved.relative_to(self._root)
        except ValueError as error:
            raise ResourcePathViolationError(
                f"Local resource {locator!r} escapes configured root "
                f"{str(self._root)!r}."
            ) from error

        return resolved


class LocalFileReader:
    """Read CSV, JSONL, Parquet and Arrow IPC through Arrow interchange."""

    def __init__(self, root: str | Path) -> None:
        self._paths = LocalFilePathResolver(root)
        self._schema_inspector = PyArrowSchemaInspector()
        self._expressions = PyArrowExpressionCompiler()

    @property
    def schemes(self) -> frozenset[str]:
        return frozenset({"file"})

    def read(self, request: ReadRequest) -> ReadResult:
        if request.resource.scheme.lower() != "file":
            raise ResourceReadError("LocalFileReader only supports file resources.")
        if request.credential is not None:
            raise ResourceReadError(
                "LocalFileReader does not resolve CredentialReference values."
            )

        path = self._paths.resolve(request.resource.locator)
        if not path.exists():
            raise ResourceReadError(f"Local resource does not exist: {path}.")

        try:
            resource_format = infer_resource_format(request.resource)
        except ValueError as error:
            raise UnsupportedResourceFormatError(str(error)) from error

        try:
            table, pushdown = self._read_table(
                path,
                resource_format,
                request,
            )
        except (ResourceReadError, UnsupportedResourceFormatError):
            raise
        except Exception as error:
            raise ResourceReadError(
                f"Failed to read local resource {request.resource.locator!r}."
            ) from error

        return ReadResult(
            resource=request.resource,
            resource_format=resource_format,
            representation=ReadRepresentation.ARROW,
            value=table,
            schema=self._schema_inspector.inspect(table.schema),
            pushdown=pushdown,
        )

    def _read_table(
        self,
        path: Path,
        resource_format: ResourceFormat,
        request: ReadRequest,
    ) -> tuple[pa.Table, ReadPushdownEvidence]:
        if resource_format is ResourceFormat.PARQUET:
            return self._read_parquet(path, request)

        if request.partition_filters:
            raise ResourceReadError(
                "Partition pruning is only qualified for Parquet in LOT-20."
            )

        if resource_format is ResourceFormat.CSV:
            table = pa_csv.read_csv(path)
        elif resource_format is ResourceFormat.JSONL:
            table = pa_json.read_json(path)
        elif resource_format is ResourceFormat.ARROW_IPC:
            with pa.memory_map(str(path), "r") as source:
                table = pa_ipc.open_file(source).read_all()
        else:
            raise UnsupportedResourceFormatError(
                f"Unsupported local read format {resource_format.value!r}."
            )

        predicate_status = PushdownStatus.NOT_REQUESTED
        if request.predicate is not None:
            mask = self._expressions.compile(request.predicate, table)
            table = table.filter(mask, null_selection_behavior="drop")
            predicate_status = PushdownStatus.POST_SCAN

        projection_status = PushdownStatus.NOT_REQUESTED
        if request.projection:
            table = table.select(list(request.projection))
            projection_status = PushdownStatus.POST_SCAN

        return (
            table,
            ReadPushdownEvidence(
                projection=projection_status,
                predicate=predicate_status,
            ),
        )

    def _read_parquet(
        self,
        path: Path,
        request: ReadRequest,
    ) -> tuple[pa.Table, ReadPushdownEvidence]:
        dataset = ds.dataset(
            str(path),
            format="parquet",
            partitioning="hive",
        )

        predicate = (
            _compile_dataset_expression(request.predicate)
            if request.predicate is not None
            else None
        )
        partition_predicate = _partition_expression(request.partition_filters)
        filter_expression = _and_expressions(predicate, partition_predicate)

        scanner = dataset.scanner(
            columns=list(request.projection) if request.projection else None,
            filter=filter_expression,
        )
        table = scanner.to_table()

        return (
            table,
            ReadPushdownEvidence(
                projection=(
                    PushdownStatus.SOURCE
                    if request.projection
                    else PushdownStatus.NOT_REQUESTED
                ),
                predicate=(
                    PushdownStatus.SOURCE
                    if request.predicate is not None
                    else PushdownStatus.NOT_REQUESTED
                ),
                partition_pruning=(
                    PushdownStatus.SOURCE
                    if request.partition_filters
                    else PushdownStatus.NOT_REQUESTED
                ),
            ),
        )


class LocalFileWriter:
    """Write Arrow-exportable handles to local tabular files."""

    def __init__(self, root: str | Path) -> None:
        self._paths = LocalFilePathResolver(root)

    @property
    def schemes(self) -> frozenset[str]:
        return frozenset({"file"})

    def write(self, request: WriteRequest) -> WriteResult:
        if request.resource.scheme.lower() != "file":
            raise ResourceWriteError("LocalFileWriter only supports file resources.")
        if request.credential is not None:
            raise ResourceWriteError(
                "LocalFileWriter does not resolve CredentialReference values."
            )
        if not isinstance(request.handle, ArrowExportablePhysicalHandle):
            raise ResourceWriteError(
                "LocalFileWriter requires an Arrow-exportable PhysicalHandle."
            )
        if request.mode is WriteMode.APPEND and request.retry_safety is RetrySafety.SAFE:
            raise ResourceWriteError(
                "APPEND cannot be declared retry-safe without stronger idempotency."
            )

        path = self._paths.resolve(request.resource.locator)
        path.parent.mkdir(parents=True, exist_ok=True)

        try:
            resource_format = infer_resource_format(request.resource)
        except ValueError as error:
            raise UnsupportedResourceFormatError(str(error)) from error

        table = request.handle.to_arrow_table()
        if not isinstance(table, pa.Table):
            raise ResourceWriteError(
                "Arrow-exportable handle did not return a pyarrow.Table."
            )

        if request.mode is WriteMode.APPEND:
            return self._append(path, table, resource_format, request)

        return self._atomic_write(path, table, resource_format, request)

    def _atomic_write(
        self,
        path: Path,
        table: pa.Table,
        resource_format: ResourceFormat,
        request: WriteRequest,
    ) -> WriteResult:
        if request.mode in {WriteMode.CREATE_NEW, WriteMode.FAIL_IF_EXISTS}:
            if path.exists():
                raise ResourceWriteError(
                    f"Target resource already exists: {request.resource.locator!r}."
                )

        fd, temp_name = tempfile.mkstemp(
            prefix=f".{path.name}.",
            suffix=".ptk-tmp",
            dir=str(path.parent),
        )
        os.close(fd)
        temp_path = Path(temp_name)

        try:
            self._write_table(temp_path, table, resource_format)
        except Exception as error:
            temp_path.unlink(missing_ok=True)
            raise ResourceWriteError(
                f"Failed before committing {request.resource.locator!r}."
            ) from error

        try:
            if request.mode in {WriteMode.CREATE_NEW, WriteMode.FAIL_IF_EXISTS}:
                os.link(temp_path, path)
                temp_path.unlink(missing_ok=True)
            elif request.mode is WriteMode.REPLACE:
                os.replace(temp_path, path)
            else:
                temp_path.unlink(missing_ok=True)
                raise ResourceWriteError(
                    f"Unsupported write mode {request.mode.value!r}."
                )
        except FileExistsError as error:
            temp_path.unlink(missing_ok=True)
            raise ResourceWriteError(
                f"Target resource already exists: {request.resource.locator!r}."
            ) from error
        except OSError:
            temp_path.unlink(missing_ok=True)
            return WriteResult(
                resource=request.resource,
                resource_format=resource_format,
                status=WriteStatus.UNKNOWN_OUTCOME,
                retry_safety=RetrySafety.REQUIRES_RECONCILIATION,
                rows_written=table.num_rows,
            )

        return WriteResult(
            resource=request.resource,
            resource_format=resource_format,
            status=WriteStatus.SUCCEEDED,
            retry_safety=request.retry_safety,
            rows_written=table.num_rows,
            bytes_written=path.stat().st_size,
        )

    def _append(
        self,
        path: Path,
        table: pa.Table,
        resource_format: ResourceFormat,
        request: WriteRequest,
    ) -> WriteResult:
        if resource_format not in {ResourceFormat.CSV, ResourceFormat.JSONL}:
            raise ResourceWriteError(
                "LOT-20 local APPEND is only qualified for CSV and JSONL."
            )

        before = path.stat().st_size if path.exists() else 0
        try:
            if resource_format is ResourceFormat.CSV:
                _append_csv(path, table)
            else:
                _append_jsonl(path, table)
        except Exception:
            return WriteResult(
                resource=request.resource,
                resource_format=resource_format,
                status=WriteStatus.UNKNOWN_OUTCOME,
                retry_safety=RetrySafety.REQUIRES_RECONCILIATION,
                rows_written=None,
                bytes_written=None,
            )

        after = path.stat().st_size
        return WriteResult(
            resource=request.resource,
            resource_format=resource_format,
            status=WriteStatus.SUCCEEDED,
            retry_safety=request.retry_safety,
            rows_written=table.num_rows,
            bytes_written=max(0, after - before),
        )

    @staticmethod
    def _write_table(
        path: Path,
        table: pa.Table,
        resource_format: ResourceFormat,
    ) -> None:
        if resource_format is ResourceFormat.CSV:
            pa_csv.write_csv(table, path)
            return
        if resource_format is ResourceFormat.JSONL:
            _write_jsonl(path, table)
            return
        if resource_format is ResourceFormat.PARQUET:
            pq.write_table(table, path)
            return
        if resource_format is ResourceFormat.ARROW_IPC:
            with pa.OSFile(str(path), "wb") as sink:
                with pa_ipc.new_file(sink, table.schema) as writer:
                    writer.write_table(table)
            return
        raise UnsupportedResourceFormatError(
            f"Unsupported local write format {resource_format.value!r}."
        )


def _compile_dataset_expression(expression: Any) -> ds.Expression:
    if isinstance(expression, ColumnReference):
        if len(expression.path.parts) != 1:
            raise ResourceReadError(
                "Parquet predicate pushdown currently supports root fields only."
            )
        return ds.field(expression.path.parts[0])

    if isinstance(expression, Literal):
        return ds.scalar(expression.value)

    if isinstance(expression, BinaryExpression):
        left = _compile_dataset_expression(expression.left)
        right = _compile_dataset_expression(expression.right)
        operator = expression.operator
        if operator is BinaryOperator.EQ:
            return left == right
        if operator is BinaryOperator.NE:
            return left != right
        if operator is BinaryOperator.LT:
            return left < right
        if operator is BinaryOperator.LE:
            return left <= right
        if operator is BinaryOperator.GT:
            return left > right
        if operator is BinaryOperator.GE:
            return left >= right
        if operator is BinaryOperator.AND:
            return left & right
        if operator is BinaryOperator.OR:
            return left | right
        raise ResourceReadError(
            f"Unsupported Parquet pushdown operator {operator.value!r}."
        )

    if isinstance(expression, UnaryExpression):
        if expression.operator is not UnaryOperator.NOT:
            raise ResourceReadError(
                f"Unsupported Parquet unary pushdown {expression.operator.value!r}."
            )
        return ~_compile_dataset_expression(expression.operand)

    if isinstance(expression, IsNullExpression):
        return _compile_dataset_expression(expression.operand).is_null()

    if isinstance(expression, IsNotNullExpression):
        return _compile_dataset_expression(expression.operand).is_valid()

    raise ResourceReadError(
        "Expression cannot be lowered to a Parquet dataset predicate in LOT-20."
    )


def _partition_expression(
    filters: tuple[tuple[str, str], ...],
) -> ds.Expression | None:
    result: ds.Expression | None = None
    for field_name, value in filters:
        current = ds.field(field_name) == ds.scalar(value)
        result = current if result is None else result & current
    return result


def _and_expressions(
    left: ds.Expression | None,
    right: ds.Expression | None,
) -> ds.Expression | None:
    if left is None:
        return right
    if right is None:
        return left
    return left & right


def _write_jsonl(path: Path, table: pa.Table) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        for row in table.to_pylist():
            stream.write(json.dumps(row, default=str, ensure_ascii=False))
            stream.write("\n")


def _append_jsonl(path: Path, table: pa.Table) -> None:
    with path.open("a", encoding="utf-8", newline="") as stream:
        for row in table.to_pylist():
            stream.write(json.dumps(row, default=str, ensure_ascii=False))
            stream.write("\n")


def _append_csv(path: Path, table: pa.Table) -> None:
    exists = path.exists() and path.stat().st_size > 0
    with path.open("a", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=table.column_names)
        if not exists:
            writer.writeheader()
        writer.writerows(table.to_pylist())
