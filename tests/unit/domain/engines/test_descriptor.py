from __future__ import annotations

import pytest

from pytransformkit.domain.engines import EngineCapability, EngineDescriptor


def test_engine_descriptor_preserves_capabilities() -> None:
    descriptor = EngineDescriptor(
        id="pandas",
        name="Pandas",
        adapter_version="0.1.0a1",
        capabilities=frozenset(
            {
                EngineCapability.SELECT,
                EngineCapability.FILTER,
            }
        ),
    )

    assert descriptor.supports(EngineCapability.SELECT)
    assert descriptor.supports(EngineCapability.DERIVE) is False


@pytest.mark.parametrize(
    ("engine_id", "name", "version"),
    [
        ("", "Pandas", "1"),
        ("pandas", "", "1"),
        ("pandas", "Pandas", ""),
    ],
)
def test_engine_descriptor_rejects_blank_identity_fields(
    engine_id: str,
    name: str,
    version: str,
) -> None:
    with pytest.raises(ValueError):
        EngineDescriptor(
            id=engine_id,
            name=name,
            adapter_version=version,
            capabilities=frozenset(),
        )


def test_engine_descriptor_requires_immutable_capabilities() -> None:
    with pytest.raises(TypeError, match="frozenset"):
        EngineDescriptor(
            id="pandas",
            name="Pandas",
            adapter_version="1",
            capabilities={EngineCapability.SELECT},  # type: ignore[arg-type]
        )
