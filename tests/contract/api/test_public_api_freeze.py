from __future__ import annotations

import importlib
import inspect
import json
import tomllib
from enum import Enum
from pathlib import Path
from typing import Any

import pytransformkit
from pytransformkit.conformance import PUBLISHED_ENGINE_PROFILES
from pytransformkit.domain.shared.version import Version
from pytransformkit.plugins import (
    PLUGIN_API_VERSION,
    PLUGIN_ENTRY_POINT_GROUP,
    PluginCompatibility,
)
from pytransformkit.serialization import (
    DataTypeCodec,
    DiagnosticCodec,
    ExecutionManifestCodec,
    ExpressionCodec,
    FieldCodec,
    LineageCodec,
    LogicalPlanCodec,
    ResourceReferenceCodec,
    SchemaCodec,
    TransformationExecutionReferenceCodec,
    TransformationPlanCodec,
)

BASELINE_PATH = (
    Path(__file__).parents[2] / "fixtures" / "public_api" / "v1.json"
)
PROJECT_ROOT = Path(__file__).parents[3]


def _baseline() -> dict[str, Any]:
    return json.loads(BASELINE_PATH.read_text(encoding="utf-8"))


def _resolve(dotted: str) -> object:
    parts = dotted.split(".")
    module = None
    index = len(parts)
    while index:
        try:
            module = importlib.import_module(".".join(parts[:index]))
            break
        except ModuleNotFoundError:
            index -= 1
    if module is None:
        raise AssertionError(f"Cannot import public symbol path {dotted!r}.")
    value: object = module
    for part in parts[index:]:
        value = getattr(value, part)
    return value


def _default(value: object) -> object:
    if value is inspect.Signature.empty:
        return "<required>"
    if isinstance(value, Enum):
        return f"{type(value).__name__}.{value.name}"
    if isinstance(value, Version):
        return str(value)
    if isinstance(value, tuple):
        return list(value)
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    return repr(value)


def _signature_shape(value: object) -> list[list[object]]:
    signature = inspect.signature(value)
    return [
        [
            parameter.name,
            parameter.kind.name,
            _default(parameter.default),
        ]
        for parameter in signature.parameters.values()
    ]


def _protocol_members(value: object) -> list[str]:
    return sorted(
        name
        for name, member in vars(value).items()
        if not name.startswith("_")
        and (
            isinstance(member, property)
            or inspect.isfunction(member)
        )
    )


def test_root_exports_match_v1_freeze() -> None:
    assert pytransformkit.__all__ == _baseline()["root_exports"]


def test_stable_namespace_exports_match_v1_freeze() -> None:
    baseline = _baseline()
    for module_name, expected in baseline["stable_namespaces"].items():
        module = importlib.import_module(module_name)
        assert module.__all__ == expected, module_name


def test_public_signature_shapes_match_v1_freeze() -> None:
    baseline = _baseline()
    for dotted, expected in baseline["signatures"].items():
        assert _signature_shape(_resolve(dotted)) == expected, dotted


def test_protocol_members_match_v1_freeze() -> None:
    baseline = _baseline()
    for dotted, expected in baseline["protocol_members"].items():
        assert _protocol_members(_resolve(dotted)) == expected, dotted


def test_exception_hierarchy_and_error_codes_match_v1_freeze() -> None:
    errors = importlib.import_module("pytransformkit.errors")
    for name, (expected_parent, expected_code) in _baseline()[
        "exception_hierarchy"
    ].items():
        exception_type = getattr(errors, name)
        assert exception_type.__bases__[0].__name__ == expected_parent
        assert str(exception_type.error_code) == expected_code


def test_enum_members_match_v1_freeze() -> None:
    for dotted, expected in _baseline()["enum_members"].items():
        enum_type = _resolve(dotted)
        observed = {member.name: member.value for member in enum_type}
        assert observed == expected, dotted


def test_optional_extra_names_match_v1_freeze() -> None:
    project = tomllib.loads(
        (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    )
    observed = sorted(project["project"]["optional-dependencies"])
    assert observed == _baseline()["extras"]["all_names"]


def test_published_engine_ids_and_stability_match_v1_freeze() -> None:
    observed = {
        profile.engine_id: profile.stability.value
        for profile in PUBLISHED_ENGINE_PROFILES
    }
    assert observed == _baseline()["engine_profiles"]


def test_plugin_protocol_constants_and_default_range_match_v1_freeze() -> None:
    expected = _baseline()["plugin"]
    compatibility = PluginCompatibility()

    assert PLUGIN_API_VERSION == expected["api_version"]
    assert PLUGIN_ENTRY_POINT_GROUP == expected["entry_point_group"]
    assert str(compatibility.framework_min) == expected["default_framework_min"]
    assert (
        str(compatibility.framework_max_exclusive)
        == expected["default_framework_max_exclusive"]
    )


def test_wire_contract_ids_and_versions_match_v1_freeze() -> None:
    codecs = {
        codec_type.__name__: codec_type()
        for codec_type in (
            DataTypeCodec,
            FieldCodec,
            SchemaCodec,
            ExpressionCodec,
            TransformationPlanCodec,
            LogicalPlanCodec,
            ResourceReferenceCodec,
            TransformationExecutionReferenceCodec,
            LineageCodec,
            DiagnosticCodec,
            ExecutionManifestCodec,
        )
    }
    observed = {
        name: [codec.contract, codec.contract_version]
        for name, codec in codecs.items()
    }
    assert observed == _baseline()["wire_contracts"]


def test_forbidden_architecture_types_are_not_public() -> None:
    forbidden = {
        "TransformationGraph",
        "OptimizedLogicalPlan",
        "PhysicalPlan",
    }

    assert forbidden.isdisjoint(pytransformkit.__all__)

    for module_name in (
        "pytransformkit.authoring",
        "pytransformkit.planning",
        "pytransformkit.runtime",
    ):
        module = importlib.import_module(module_name)
        assert forbidden.isdisjoint(module.__all__)


def test_legacy_pipeline_names_remain_noncanonical() -> None:
    assert "Pipeline" not in pytransformkit.__all__
    assert "RunPipelineService" not in pytransformkit.__all__
    assert "PipelineExecutionResult" not in pytransformkit.__all__
