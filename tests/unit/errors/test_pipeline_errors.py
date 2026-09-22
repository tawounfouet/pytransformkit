from pytransformkit.errors import (
    InvalidPipelineError,
    PipelineCycleError,
    PipelineError,
    PipelineNodeNotFoundError,
    PyTransformKitError,
)


def test_pipeline_errors_share_framework_root() -> None:
    assert isinstance(PipelineError(), PyTransformKitError)
    assert isinstance(InvalidPipelineError(), PyTransformKitError)
    assert isinstance(PipelineCycleError(), PyTransformKitError)
    assert isinstance(
        PipelineNodeNotFoundError("node"),
        PyTransformKitError,
    )


def test_pipeline_error_codes_are_stable() -> None:
    assert str(PipelineError().code) == "PTK-PIPE-000"
    assert str(InvalidPipelineError().code) == "PTK-PIPE-001"
    assert str(PipelineCycleError().code) == "PTK-PIPE-002"
    assert str(PipelineNodeNotFoundError("node").code) == "PTK-PIPE-003"
