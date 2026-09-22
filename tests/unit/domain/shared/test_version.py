import pytest

from pytransformkit.domain.shared.version import Version


def test_version_string_representation() -> None:
    assert str(Version(1, 2, 3)) == "1.2.3"


def test_version_is_orderable() -> None:
    assert Version(1, 2, 3) < Version(1, 3, 0)


@pytest.mark.parametrize(
    ("major", "minor", "patch"),
    [
        (-1, 0, 0),
        (0, -1, 0),
        (0, 0, -1),
    ],
)
def test_version_rejects_negative_components(
    major: int,
    minor: int,
    patch: int,
) -> None:
    with pytest.raises(ValueError, match="non-negative"):
        Version(major, minor, patch)
