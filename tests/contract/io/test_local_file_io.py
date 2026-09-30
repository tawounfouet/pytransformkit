# ruff: noqa: E402

from __future__ import annotations

from pathlib import Path

import pytest

pa = pytest.importorskip("pyarrow")
pq = pytest.importorskip("pyarrow.parquet")

from pytransformkit import ResourceReference, RetrySafety, WriteMode
from pytransformkit.adapters.pyarrow import PyArrowDatasetHandle
from pytransformkit.functions import col
from pytransformkit.errors import ResourcePathViolationError, ResourceWriteError
from pytransformkit.infrastructure.engines.pyarrow.types import PyArrowSchemaInspector
from pytransformkit.readers import LocalFileReader, PushdownStatus, ReadRequest
from pytransformkit.writers import LocalFileWriter, WriteRequest, WriteStatus


@pytest.mark.parametrize(
    ("filename", "media_type"),
    [
        ("records.csv", "text/csv"),
        ("records.jsonl", "application/x-ndjson"),
        ("records.parquet", "application/vnd.apache.parquet"),
        ("records.arrow", "application/vnd.apache.arrow.file"),
    ],
)
def test_local_file_round_trip_supported_formats(
    tmp_path: Path,
    filename: str,
    media_type: str,
) -> None:
    table = pa.table(
        {
            "customer_id": [1, 2],
            "status": ["ACTIVE", "INACTIVE"],
        }
    )
    resource = ResourceReference(
        scheme="file",
        locator=filename,
        media_type=media_type,
    )
    writer = LocalFileWriter(tmp_path)

    written = writer.write(
        WriteRequest(
            resource=resource,
            handle=PyArrowDatasetHandle(table),
            schema=PyArrowSchemaInspector().inspect(table),
            mode=WriteMode.CREATE_NEW,
            retry_safety=RetrySafety.SAFE,
        )
    )

    assert written.status is WriteStatus.SUCCEEDED
    assert written.rows_written == 2

    read = LocalFileReader(tmp_path).read(ReadRequest(resource=resource))

    assert read.value.to_pylist() == table.to_pylist()


def test_parquet_pushdown_and_hive_partition_pruning_are_source_applied(
    tmp_path: Path,
) -> None:
    fr = tmp_path / "orders" / "country=FR"
    de = tmp_path / "orders" / "country=DE"
    fr.mkdir(parents=True)
    de.mkdir(parents=True)

    pq.write_table(
        pa.table({"order_id": [1, 2], "amount": [5, 20]}),
        fr / "part.parquet",
    )
    pq.write_table(
        pa.table({"order_id": [3], "amount": [50]}),
        de / "part.parquet",
    )

    result = LocalFileReader(tmp_path).read(
        ReadRequest(
            resource=ResourceReference(
                scheme="file",
                locator="orders",
                media_type="application/vnd.apache.parquet",
            ),
            projection=("order_id", "country"),
            predicate=col("amount") > 10,
            partition_filters=(("country", "FR"),),
        )
    )

    assert result.value.to_pylist() == [{"order_id": 2, "country": "FR"}]
    assert result.pushdown.projection is PushdownStatus.SOURCE
    assert result.pushdown.predicate is PushdownStatus.SOURCE
    assert result.pushdown.partition_pruning is PushdownStatus.SOURCE


def test_non_parquet_filter_and_projection_are_explicitly_post_scan(
    tmp_path: Path,
) -> None:
    path = tmp_path / "records.csv"
    path.write_text("id,status\n1,OPEN\n2,ACTIVE\n", encoding="utf-8")

    result = LocalFileReader(tmp_path).read(
        ReadRequest(
            resource=ResourceReference(scheme="file", locator="records.csv"),
            projection=("id",),
            predicate=col("status") == "ACTIVE",
        )
    )

    assert result.value.to_pylist() == [{"id": 2}]
    assert result.pushdown.projection is PushdownStatus.POST_SCAN
    assert result.pushdown.predicate is PushdownStatus.POST_SCAN


def test_local_root_blocks_path_traversal(tmp_path: Path) -> None:
    reader = LocalFileReader(tmp_path)

    with pytest.raises(ResourcePathViolationError):
        reader.read(
            ReadRequest(
                resource=ResourceReference(
                    scheme="file",
                    locator="../outside.csv",
                )
            )
        )


def test_create_new_refuses_existing_target(tmp_path: Path) -> None:
    table = pa.table({"id": [1]})
    handle = PyArrowDatasetHandle(table)
    resource = ResourceReference(scheme="file", locator="records.parquet")
    writer = LocalFileWriter(tmp_path)
    logical_schema = PyArrowSchemaInspector().inspect(table)
    request = WriteRequest(
        resource=resource,
        handle=handle,
        schema=logical_schema,
        retry_safety=RetrySafety.SAFE,
    )

    writer.write(request)

    with pytest.raises(ResourceWriteError):
        writer.write(request)


def test_csv_append_is_not_allowed_to_claim_safe_retry(tmp_path: Path) -> None:
    table = pa.table({"id": [1]})
    with pytest.raises(ResourceWriteError):
        LocalFileWriter(tmp_path).write(
            WriteRequest(
                resource=ResourceReference(scheme="file", locator="records.csv"),
                handle=PyArrowDatasetHandle(table),
                schema=PyArrowSchemaInspector().inspect(table),
                mode=WriteMode.APPEND,
                retry_safety=RetrySafety.SAFE,
            )
        )
