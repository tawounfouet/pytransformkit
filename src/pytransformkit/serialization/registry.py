"""Closed semantic type registry used by safe wire decoding."""

from __future__ import annotations

import inspect
import re
from dataclasses import is_dataclass
from enum import Enum
from importlib import import_module
from types import ModuleType

from pytransformkit.errors.serialization import (
    InvalidWirePayloadError,
    NonPortableValueError,
)

_SAFE_MODULES = (
    "pytransformkit.domain.data.data_types",
    "pytransformkit.domain.data.dataset",
    "pytransformkit.domain.data.field",
    "pytransformkit.domain.data.field_path",
    "pytransformkit.domain.data.metadata",
    "pytransformkit.domain.data.references",
    "pytransformkit.domain.data.schema",
    "pytransformkit.domain.data.statistics",
    "pytransformkit.domain.engines.capabilities",
    "pytransformkit.domain.engines.descriptor",
    "pytransformkit.domain.expressions.aggregate",
    "pytransformkit.domain.expressions.binary",
    "pytransformkit.domain.expressions.functions",
    "pytransformkit.domain.expressions.literals",
    "pytransformkit.domain.expressions.operators",
    "pytransformkit.domain.expressions.predicates",
    "pytransformkit.domain.expressions.references",
    "pytransformkit.domain.expressions.unary",
    "pytransformkit.domain.expressions.window",
    "pytransformkit.domain.lineage.model",
    "pytransformkit.domain.pipelines.dependencies",
    "pytransformkit.domain.pipelines.nodes",
    "pytransformkit.domain.pipelines.plan",
    "pytransformkit.domain.plans.transformation_plan",
    "pytransformkit.domain.quality.results",
    "pytransformkit.domain.quality.rules",
    "pytransformkit.domain.resources.credentials",
    "pytransformkit.domain.resources.formats",
    "pytransformkit.domain.resources.reference",
    "pytransformkit.domain.resources.retry",
    "pytransformkit.domain.resources.write",
    "pytransformkit.domain.runtime.context",
    "pytransformkit.domain.runtime.diagnostics",
    "pytransformkit.domain.runtime.execution",
    "pytransformkit.domain.runtime.failure",
    "pytransformkit.domain.runtime.references",
    "pytransformkit.domain.shared.fingerprint",
    "pytransformkit.domain.shared.identifiers",
    "pytransformkit.domain.shared.version",
    "pytransformkit.domain.transformations.aggregation",
    "pytransformkit.domain.transformations.casting",
    "pytransformkit.domain.transformations.deduplication",
    "pytransformkit.domain.transformations.derivation",
    "pytransformkit.domain.transformations.filtering",
    "pytransformkit.domain.transformations.projection",
    "pytransformkit.domain.transformations.properties",
    "pytransformkit.domain.transformations.quality",
    "pytransformkit.domain.transformations.relational",
    "pytransformkit.domain.transformations.reshaping",
    "pytransformkit.domain.transformations.sorting",
)

_NAMESPACE_BY_FRAGMENT = (
    (".domain.data.", "data"),
    (".domain.engines.", "engine"),
    (".domain.expressions.", "expression"),
    (".domain.lineage.", "lineage"),
    (".domain.pipelines.", "plan"),
    (".domain.plans.", "plan"),
    (".domain.quality.", "quality"),
    (".domain.resources.", "resource"),
    (".domain.runtime.", "runtime"),
    (".domain.shared.", "shared"),
    (".domain.transformations.", "transformation"),
)


class SemanticTypeRegistry:
    """Whitelist mapping stable semantic type IDs to local Python classes."""

    def __init__(self) -> None:
        self._by_id: dict[str, type[object]] = {}
        self._by_type: dict[type[object], str] = {}

    def register(self, type_id: str, cls: type[object]) -> None:
        if not type_id or not type_id.strip():
            raise ValueError("type_id must not be empty.")
        existing = self._by_id.get(type_id)
        if existing is not None and existing is not cls:
            raise ValueError(f"Semantic type ID collision for {type_id!r}.")
        existing_id = self._by_type.get(cls)
        if existing_id is not None and existing_id != type_id:
            raise ValueError(
                f"Python type {cls.__name__!r} already registered as {existing_id!r}."
            )
        self._by_id[type_id] = cls
        self._by_type[cls] = type_id

    def type_id_for(self, value: object | type[object]) -> str:
        cls = value if isinstance(value, type) else type(value)
        try:
            return self._by_type[cls]
        except KeyError as error:
            raise NonPortableValueError(
                f"Type {cls.__name__!r} is not in the portable semantic registry."
            ) from error

    def type_for(self, type_id: str) -> type[object]:
        try:
            return self._by_id[type_id]
        except KeyError as error:
            raise InvalidWirePayloadError(
                f"Unknown semantic wire type {type_id!r}."
            ) from error

    @classmethod
    def default(cls) -> SemanticTypeRegistry:
        registry = cls()
        for module_name in _SAFE_MODULES:
            module = import_module(module_name)
            _register_module_types(registry, module)
        return registry


def _register_module_types(
    registry: SemanticTypeRegistry,
    module: ModuleType,
) -> None:
    for _, member in inspect.getmembers(module, inspect.isclass):
        if member.__module__ != module.__name__:
            continue
        if member.__name__.startswith("_"):
            continue
        if not (is_dataclass(member) or issubclass(member, Enum)):
            continue
        registry.register(_semantic_type_id(member), member)


def _semantic_type_id(cls: type[object]) -> str:
    namespace = None
    for fragment, candidate in _NAMESPACE_BY_FRAGMENT:
        if fragment in cls.__module__:
            namespace = candidate
            break
    if namespace is None:
        raise ValueError(
            f"No semantic namespace configured for {cls.__module__}.{cls.__name__}."
        )
    return f"pytransformkit.{namespace}.{_snake_case(cls.__name__)}"


def _snake_case(value: str) -> str:
    first = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", value)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", first).lower()
