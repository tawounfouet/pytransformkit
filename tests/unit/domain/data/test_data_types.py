from __future__ import annotations

import pytest

from pytransformkit.domain.data.data_types import (
    DecimalType,
    FloatType,
    IntegerType,
    StringType,
    TimestampType,
    TimeType,
)


def test_data_types_use_structural_equality() -> None:
    assert StringType() == StringType()
    assert IntegerType(bits=32) == IntegerType(bits=32)
    assert IntegerType(bits=32) != IntegerType(bits=64)


@pytest.mark.parametrize("bits", [8, 16, 32, 64])
def test_integer_type_accepts_supported_widths(bits: int) -> None:
    assert IntegerType(bits=bits).bits == bits


def test_integer_type_rejects_unsupported_width() -> None:
    with pytest.raises(ValueError, match="Integer bits"):
        IntegerType(bits=128)


@pytest.mark.parametrize("bits", [32, 64])
def test_float_type_accepts_supported_widths(bits: int) -> None:
    assert FloatType(bits=bits).bits == bits


def test_float_type_rejects_unsupported_width() -> None:
    with pytest.raises(ValueError, match="Float bits"):
        FloatType(bits=16)


def test_decimal_type_accepts_valid_precision_and_scale() -> None:
    assert DecimalType(precision=18, scale=2) == DecimalType(18, 2)


@pytest.mark.parametrize(
    ("precision", "scale"),
    [
        (0, 0),
        (10, -1),
        (4, 5),
    ],
)
def test_decimal_type_rejects_invalid_bounds(precision: int, scale: int) -> None:
    with pytest.raises(ValueError):
        DecimalType(precision=precision, scale=scale)


@pytest.mark.parametrize("unit", ["s", "ms", "us", "ns"])
def test_temporal_types_accept_supported_units(unit: str) -> None:
    assert TimeType(unit=unit).unit == unit
    assert TimestampType(unit=unit).unit == unit


def test_temporal_types_reject_unsupported_unit() -> None:
    with pytest.raises(ValueError, match="Time unit"):
        TimeType(unit="minutes")


def test_timestamp_preserves_timezone() -> None:
    timestamp = TimestampType(timezone="Europe/Paris")

    assert timestamp.timezone == "Europe/Paris"


def test_timestamp_rejects_blank_timezone() -> None:
    with pytest.raises(ValueError, match="timezone"):
        TimestampType(timezone="   ")
