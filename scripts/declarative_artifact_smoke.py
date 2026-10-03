"""Smoke-test declarative schema behavior from an installed distribution."""

from __future__ import annotations

import argparse
import importlib.util
from importlib.metadata import metadata, requires, version

import pytransformkit
import pytransformkit.schema_io as schema_io
from pytransformkit.domain.data import Field, IntegerType, Schema, StringType
from pytransformkit.errors import DeclarativeSchemaDependencyError

_EXPECTED_EXPORTS = [
    "dump_schema",
    "dump_schemas",
    "dumps_schema",
    "dumps_schemas",
    "load_schema",
    "load_schemas",
    "loads_schema",
    "loads_schemas",
]


def _assert_distribution_metadata() -> None:
    distribution = metadata("pytransformkit")
    extras = set(distribution.get_all("Provides-Extra") or ())
    requirement_lines = requires("pytransformkit") or []

    assert "yaml" in extras
    yaml_requirements = [
        line
        for line in requirement_lines
        if line.lower().startswith("pyyaml") and 'extra == "yaml"' in line
    ]
    assert len(yaml_requirements) == 1, requirement_lines

    unconditional = [line for line in requirement_lines if "extra ==" not in line]
    assert unconditional == [], unconditional


def _assert_common_surface() -> None:
    assert version("pytransformkit") == pytransformkit.__version__
    assert schema_io.__all__ == _EXPECTED_EXPORTS
    assert set(_EXPECTED_EXPORTS).isdisjoint(pytransformkit.__all__)
    _assert_distribution_metadata()


def _core_only_smoke() -> None:
    _assert_common_surface()
    assert importlib.util.find_spec("yaml") is None

    try:
        schema_io.loads_schema(
            "version: 1\nschema:\n  name: empty\n  fields: []\n"
        )
    except DeclarativeSchemaDependencyError as error:
        assert str(error.error_code) == "PTK-DECL-010"
        assert error.extra_name == "yaml"
    else:
        raise AssertionError("YAML operation must fail without the optional extra.")


def _yaml_smoke() -> None:
    _assert_common_surface()
    assert importlib.util.find_spec("yaml") is not None

    schema = Schema(
        fields=(
            Field("customer_id", IntegerType(), nullable=False),
            Field("email", StringType(), description="Customer email"),
        )
    )
    text = schema_io.dumps_schema(schema, name="customers")
    loaded = schema_io.loads_schema(text, source="<artifact-smoke>")

    assert loaded == schema
    assert text.startswith("version: 1\nschema:\n")
    assert text.endswith("\n")


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("core", "yaml"), required=True)
    return parser.parse_args()


def main() -> int:
    args = _arguments()
    if args.mode == "core":
        _core_only_smoke()
    else:
        _yaml_smoke()

    print(f"Declarative installed-artifact smoke ({args.mode}): PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
