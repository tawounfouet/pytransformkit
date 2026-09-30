from __future__ import annotations

from datetime import UTC, datetime

from pytransformkit import ResourceReference
from pytransformkit.domain.runtime import (
    CorrelationContext,
    Diagnostic,
    DiagnosticSeverity,
    ExecutionManifest,
    ExecutionStatus,
)
from pytransformkit.domain.runtime.references import (
    TransformationExecutionReference,
)
from pytransformkit.domain.shared.fingerprint import Fingerprint
from pytransformkit.domain.shared.identifiers import (
    CorrelationId,
    TransformationExecutionId,
    TransformationPlanId,
)
from pytransformkit.serialization import (
    DiagnosticCodec,
    ExecutionManifestCodec,
    TransformationExecutionReferenceCodec,
)


def _execution_id() -> TransformationExecutionId:
    return TransformationExecutionId.parse("11111111-1111-1111-1111-111111111111")


def _plan_id() -> TransformationPlanId:
    return TransformationPlanId.parse("22222222-2222-2222-2222-222222222222")


def _correlation() -> CorrelationContext:
    return CorrelationContext(
        correlation_id=CorrelationId.parse("33333333-3333-3333-3333-333333333333"),
        workflow_run_id="workflow-42",
        task_attempt_id="attempt-3",
    )


def test_transformation_execution_reference_round_trips_portably() -> None:
    reference = TransformationExecutionReference(
        transformation_execution_id=_execution_id(),
        transformation_plan_fingerprint=Fingerprint("sha256", "a" * 64),
        engine_id="duckdb",
        output_reference=ResourceReference(
            scheme="file",
            locator="outputs/customer_mart.parquet",
        ),
    )
    codec = TransformationExecutionReferenceCodec()

    encoded = codec.to_json(reference)
    decoded = codec.from_json(encoded)

    assert decoded == reference
    assert "credential" not in encoded.lower()
    assert "duckdb" in encoded


def test_diagnostic_round_trip_preserves_structured_evidence() -> None:
    diagnostic = Diagnostic(
        code="PTK-TEST-001",
        severity=DiagnosticSeverity.WARNING,
        summary="Contract evidence.",
        source_component="serialization.test",
        details=(("scope", "contract"),),
        execution_id=_execution_id(),
        correlation_id=_correlation().correlation_id,
    )
    codec = DiagnosticCodec()

    encoded = codec.to_json(diagnostic)

    assert codec.from_json(encoded) == diagnostic
    assert codec.to_json(codec.from_json(encoded)) == encoded


def test_execution_manifest_round_trip_preserves_wire_version_independently() -> None:
    started = datetime(2026, 9, 30, 16, 0, tzinfo=UTC)
    ended = datetime(2026, 9, 30, 16, 0, 1, tzinfo=UTC)
    manifest = ExecutionManifest(
        framework_version="0.5.0a1",
        execution_id=_execution_id(),
        correlation=_correlation(),
        status=ExecutionStatus.SUCCEEDED,
        started_at=started,
        ended_at=ended,
        input_names=("customers",),
        output_names=("result",),
        diagnostic_codes=("PTK-RUNTIME-001",),
        plan_id=_plan_id(),
        plan_fingerprint=Fingerprint("sha256", "b" * 64),
        engine_id="pandas",
        adapter_version="0.5.0a1",
        contract_version="1",
    )
    codec = ExecutionManifestCodec()

    encoded = codec.to_json(manifest)
    decoded = codec.from_json(encoded)

    assert decoded == manifest
    assert '"contract_version":1' in encoded
    assert '"framework_version":"0.5.0a1"' in encoded
    assert '"contract_version":"1"' in encoded
