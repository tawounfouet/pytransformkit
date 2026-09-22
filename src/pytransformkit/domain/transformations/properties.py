"""Semantic properties of logical Transformations."""

from dataclasses import dataclass
from enum import StrEnum


class Determinism(StrEnum):
    DETERMINISTIC = "deterministic"
    CONTEXT_DEPENDENT = "context_dependent"
    NON_DETERMINISTIC = "non_deterministic"


class Portability(StrEnum):
    PORTABLE = "portable"
    ENGINE_BOUND = "engine_bound"
    OPAQUE = "opaque"


class Purity(StrEnum):
    PURE = "pure"
    IMPURE = "impure"


class CardinalityEffect(StrEnum):
    PRESERVE = "preserve"
    REDUCE = "reduce"
    EXPAND = "expand"
    UNKNOWN = "unknown"


class SchemaEffect(StrEnum):
    PRESERVE = "preserve"
    PROJECT = "project"
    EXTEND = "extend"
    MODIFY = "modify"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class TransformationProperties:
    """Static semantic properties used by planning and optimization."""

    determinism: Determinism
    portability: Portability
    purity: Purity
    cardinality: CardinalityEffect
    schema: SchemaEffect
