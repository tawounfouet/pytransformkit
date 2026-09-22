from pytransformkit.errors import (
    InvalidTransformationError,
    PyTransformKitError,
    TransformationError,
    UnsupportedTransformationError,
)


def test_transformation_errors_share_framework_root() -> None:
    assert isinstance(TransformationError(), PyTransformKitError)
    assert isinstance(InvalidTransformationError(), PyTransformKitError)
    assert isinstance(UnsupportedTransformationError(), PyTransformKitError)


def test_transformation_error_codes_are_stable() -> None:
    assert str(TransformationError().code) == "PTK-TRANSFORM-000"
    assert str(InvalidTransformationError().code) == "PTK-TRANSFORM-001"
    assert str(UnsupportedTransformationError().code) == "PTK-TRANSFORM-002"
