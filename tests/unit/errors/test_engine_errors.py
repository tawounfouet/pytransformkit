from pytransformkit.errors import (
    AdapterError,
    EngineError,
    EngineNotFoundError,
    ExecutionError,
    PyTransformKitError,
    UnsupportedEngineCapabilityError,
)


def test_engine_errors_share_framework_root() -> None:
    assert isinstance(EngineError(), PyTransformKitError)
    assert isinstance(AdapterError(), PyTransformKitError)
    assert isinstance(ExecutionError(), PyTransformKitError)
    assert isinstance(EngineNotFoundError("x"), PyTransformKitError)
    assert isinstance(
        UnsupportedEngineCapabilityError("x", ("filter",)),
        PyTransformKitError,
    )


def test_engine_error_codes_are_stable() -> None:
    assert str(EngineError().code) == "PTK-ENGINE-000"
    assert str(EngineNotFoundError("x").code) == "PTK-ENGINE-001"
    assert (
        str(
            UnsupportedEngineCapabilityError(
                "x",
                ("filter",),
            ).code
        )
        == "PTK-ENGINE-002"
    )
    assert str(AdapterError().code) == "PTK-ENGINE-100"
    assert str(ExecutionError().code) == "PTK-EXEC-000"
