from __future__ import annotations

import subprocess
import sys

import pytest

from pytransformkit import CredentialReference, InputBinding, ResourceReference


pytestmark = pytest.mark.contract


@pytest.mark.parametrize(
    "locator",
    [
        "https://user:password@example.com/data.parquet",
        "https://example.com/data.parquet?token=secret",
        "https://example.com/data.parquet?sig=secret",
        "https://example.com/data.parquet?x-amz-signature=secret",
    ],
)
def test_resource_reference_rejects_inline_credentials(locator: str) -> None:
    with pytest.raises(ValueError, match="CredentialReference"):
        ResourceReference(
            scheme="https",
            locator=locator,
        )


@pytest.mark.parametrize(
    "metadata",
    [
        (("password", "secret"),),
        (("api_key", "secret"),),
        (("authorization", "Bearer secret"),),
    ],
)
def test_resource_reference_rejects_credential_bearing_metadata(
    metadata: tuple[tuple[str, str], ...],
) -> None:
    with pytest.raises(ValueError, match="CredentialReference"):
        ResourceReference(
            scheme="s3",
            locator="bucket/path/data.parquet",
            metadata=metadata,
        )


def test_credential_reference_is_the_explicit_resource_binding_path() -> None:
    resource = ResourceReference(
        scheme="s3",
        locator="bucket/path/data.parquet",
    )
    credential = CredentialReference(
        credential_id="warehouse-read",
        provider="vault",
    )

    binding = InputBinding.from_resource(
        "orders",
        resource,
        credential=credential,
    )

    assert binding.resource == resource
    assert binding.credential == credential
    assert binding.portable is True


def test_core_import_does_not_eagerly_load_optional_engines() -> None:
    code = """
import sys
import pytransformkit

forbidden = {"pandas", "polars", "pyarrow", "duckdb"}
loaded = forbidden.intersection(sys.modules)
if loaded:
    raise SystemExit(
        "optional engines loaded by core import: " + ",".join(sorted(loaded))
    )
"""
    completed = subprocess.run(
        [sys.executable, "-c", code],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout


def test_core_import_does_not_make_legacy_or_forbidden_architecture_canonical() -> None:
    import pytransformkit

    forbidden = {
        "Pipeline",
        "RunPipelineService",
        "TransformationGraph",
        "OptimizedLogicalPlan",
        "PhysicalPlan",
    }

    assert forbidden.isdisjoint(pytransformkit.__all__)
