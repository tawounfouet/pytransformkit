import pytest

from pytransformkit.domain.shared.fingerprint import Fingerprint


def test_fingerprint_is_structurally_equal() -> None:
    assert Fingerprint("sha256", "abc") == Fingerprint("sha256", "abc")


@pytest.mark.parametrize(
    ("algorithm", "value"),
    [
        ("", "abc"),
        ("   ", "abc"),
        ("sha256", ""),
        ("sha256", "   "),
    ],
)
def test_fingerprint_rejects_empty_values(
    algorithm: str,
    value: str,
) -> None:
    with pytest.raises(ValueError):
        Fingerprint(algorithm, value)
