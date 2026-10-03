"""Published V1 cross-engine conformance profiles."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from pytransformkit.domain.engines import EngineCapability


class EngineStability(StrEnum):
    """Release stability of one official execution adapter."""

    STABLE = "stable"
    PROVISIONAL = "provisional"


class ConformanceDimension(StrEnum):
    """Semantic dimensions qualified by the LOT-24 conformance gate."""

    NULL_NAN = "null_nan"
    NUMERIC_PROMOTION = "numeric_promotion"
    DECIMAL = "decimal"
    TIMEZONE = "timezone"
    NESTED = "nested"
    UNICODE = "unicode"
    ORDERING = "ordering"
    DUPLICATES = "duplicates"
    EMPTY_DATA = "empty_data"
    JOINS = "joins"
    AGGREGATES = "aggregates"
    WINDOWS = "windows"
    QUALITY = "quality"
    LINEAGE = "lineage"
    SERIALIZATION = "serialization"
    CAPABILITY_FAILURE = "capability_failure"
    NO_HIDDEN_FALLBACK = "no_hidden_fallback"


class ConformanceStatus(StrEnum):
    """Qualification state for one semantic dimension on one engine."""

    QUALIFIED = "qualified"
    PROVISIONAL = "provisional"
    UNSUPPORTED = "unsupported"


@dataclass(frozen=True, slots=True)
class EngineConformanceProfile:
    """Published release-level conformance statement for one official engine."""

    engine_id: str
    stability: EngineStability
    mandatory_for_v1: bool
    dimensions: tuple[tuple[ConformanceDimension, ConformanceStatus], ...]

    def __post_init__(self) -> None:
        if not self.engine_id or not self.engine_id.strip():
            raise ValueError("engine_id must not be empty.")
        if not isinstance(self.stability, EngineStability):
            raise TypeError("stability must be EngineStability.")
        if not isinstance(self.mandatory_for_v1, bool):
            raise TypeError("mandatory_for_v1 must be a bool.")
        if not isinstance(self.dimensions, tuple):
            raise TypeError("dimensions must be a tuple.")
        names = tuple(dimension for dimension, _ in self.dimensions)
        if len(names) != len(set(names)):
            raise ValueError("conformance dimensions must be unique.")
        if set(names) != set(ConformanceDimension):
            raise ValueError(
                "conformance profile must classify every ConformanceDimension."
            )
        for dimension, status in self.dimensions:
            if not isinstance(dimension, ConformanceDimension):
                raise TypeError("dimensions must use ConformanceDimension keys.")
            if not isinstance(status, ConformanceStatus):
                raise TypeError("dimensions must use ConformanceStatus values.")

    def status_for(self, dimension: ConformanceDimension) -> ConformanceStatus:
        """Return the published status for one semantic dimension."""
        if not isinstance(dimension, ConformanceDimension):
            raise TypeError("dimension must be ConformanceDimension.")
        for current, status in self.dimensions:
            if current is dimension:
                return status
        raise KeyError(dimension)


MANDATORY_V1_CAPABILITIES = frozenset(
    {
        EngineCapability.SELECT,
        EngineCapability.DROP,
        EngineCapability.RENAME,
        EngineCapability.FILTER,
        EngineCapability.LIMIT,
        EngineCapability.DISTINCT,
        EngineCapability.CAST,
        EngineCapability.DERIVE,
        EngineCapability.SORT,
        EngineCapability.DEDUPLICATE,
        EngineCapability.JOIN_INNER,
        EngineCapability.JOIN_LEFT,
        EngineCapability.JOIN_RIGHT,
        EngineCapability.JOIN_FULL,
        EngineCapability.JOIN_SEMI,
        EngineCapability.JOIN_ANTI,
        EngineCapability.JOIN_CROSS,
        EngineCapability.UNION,
        EngineCapability.INTERSECT,
        EngineCapability.EXCEPT,
        EngineCapability.AGGREGATE,
        EngineCapability.WINDOW,
        EngineCapability.WINDOW_ROWS_CUMULATIVE,
        EngineCapability.WINDOW_ROWS_MOVING,
        EngineCapability.PIVOT,
        EngineCapability.UNPIVOT,
        EngineCapability.EXPLODE,
        EngineCapability.FLATTEN,
        EngineCapability.NESTED,
        EngineCapability.TEMPORAL,
        EngineCapability.DURATION,
        EngineCapability.QUALITY,
    }
)

PUBLISHED_ENGINE_CAPABILITIES: tuple[
    tuple[str, frozenset[EngineCapability]],
    ...,
] = (
    ("pandas", MANDATORY_V1_CAPABILITIES),
    (
        "polars",
        MANDATORY_V1_CAPABILITIES | frozenset({EngineCapability.LAZY}),
    ),
    (
        "pyarrow",
        frozenset(
            {
                EngineCapability.SELECT,
                EngineCapability.DROP,
                EngineCapability.RENAME,
                EngineCapability.FILTER,
                EngineCapability.LIMIT,
                EngineCapability.DERIVE,
                EngineCapability.SORT,
            }
        ),
    ),
    (
        "duckdb",
        frozenset(
            {
                EngineCapability.SELECT,
                EngineCapability.DROP,
                EngineCapability.RENAME,
                EngineCapability.FILTER,
                EngineCapability.LIMIT,
                EngineCapability.DISTINCT,
                EngineCapability.CAST,
                EngineCapability.DERIVE,
                EngineCapability.SORT,
                EngineCapability.JOIN_INNER,
                EngineCapability.JOIN_LEFT,
                EngineCapability.JOIN_RIGHT,
                EngineCapability.JOIN_FULL,
                EngineCapability.JOIN_SEMI,
                EngineCapability.JOIN_ANTI,
                EngineCapability.JOIN_CROSS,
                EngineCapability.UNION,
                EngineCapability.INTERSECT,
                EngineCapability.EXCEPT,
                EngineCapability.AGGREGATE,
                EngineCapability.WINDOW,
                EngineCapability.WINDOW_ROWS_CUMULATIVE,
                EngineCapability.WINDOW_ROWS_MOVING,
                EngineCapability.WINDOW_ROWS_ARBITRARY,
                EngineCapability.WINDOW_RANGE,
                EngineCapability.LAZY,
            }
        ),
    ),
)


def engine_capabilities(engine_id: str) -> frozenset[EngineCapability]:
    """Return the published capability set for one official engine."""
    if not isinstance(engine_id, str) or not engine_id.strip():
        raise ValueError("engine_id must not be empty.")
    for current_id, capabilities in PUBLISHED_ENGINE_CAPABILITIES:
        if current_id == engine_id:
            return capabilities
    raise KeyError(engine_id)


def _all(
    status: ConformanceStatus,
) -> tuple[
    tuple[ConformanceDimension, ConformanceStatus],
    ...,
]:
    return tuple((dimension, status) for dimension in ConformanceDimension)


def _profile(
    engine_id: str,
    stability: EngineStability,
    mandatory_for_v1: bool,
    overrides: dict[ConformanceDimension, ConformanceStatus] | None = None,
) -> EngineConformanceProfile:
    values = dict(_all(ConformanceStatus.QUALIFIED))
    if overrides is not None:
        values.update(overrides)
    return EngineConformanceProfile(
        engine_id=engine_id,
        stability=stability,
        mandatory_for_v1=mandatory_for_v1,
        dimensions=tuple(
            (dimension, values[dimension]) for dimension in ConformanceDimension
        ),
    )


PANDAS_CONFORMANCE = _profile(
    "pandas",
    EngineStability.STABLE,
    True,
)

POLARS_CONFORMANCE = _profile(
    "polars",
    EngineStability.STABLE,
    True,
)

PYARROW_CONFORMANCE = _profile(
    "pyarrow",
    EngineStability.PROVISIONAL,
    False,
    {
        ConformanceDimension.NULL_NAN: ConformanceStatus.PROVISIONAL,
        ConformanceDimension.NUMERIC_PROMOTION: ConformanceStatus.PROVISIONAL,
        ConformanceDimension.DECIMAL: ConformanceStatus.PROVISIONAL,
        ConformanceDimension.TIMEZONE: ConformanceStatus.PROVISIONAL,
        ConformanceDimension.NESTED: ConformanceStatus.PROVISIONAL,
        ConformanceDimension.UNICODE: ConformanceStatus.PROVISIONAL,
        ConformanceDimension.DUPLICATES: ConformanceStatus.UNSUPPORTED,
        ConformanceDimension.JOINS: ConformanceStatus.UNSUPPORTED,
        ConformanceDimension.AGGREGATES: ConformanceStatus.UNSUPPORTED,
        ConformanceDimension.WINDOWS: ConformanceStatus.UNSUPPORTED,
        ConformanceDimension.QUALITY: ConformanceStatus.UNSUPPORTED,
    },
)

DUCKDB_CONFORMANCE = _profile(
    "duckdb",
    EngineStability.PROVISIONAL,
    False,
    {
        ConformanceDimension.NULL_NAN: ConformanceStatus.PROVISIONAL,
        ConformanceDimension.NUMERIC_PROMOTION: ConformanceStatus.PROVISIONAL,
        ConformanceDimension.TIMEZONE: ConformanceStatus.PROVISIONAL,
        ConformanceDimension.NESTED: ConformanceStatus.UNSUPPORTED,
        ConformanceDimension.QUALITY: ConformanceStatus.UNSUPPORTED,
    },
)


PUBLISHED_ENGINE_PROFILES = (
    PANDAS_CONFORMANCE,
    POLARS_CONFORMANCE,
    PYARROW_CONFORMANCE,
    DUCKDB_CONFORMANCE,
)


def engine_profile(engine_id: str) -> EngineConformanceProfile:
    """Return one official published conformance profile."""
    if not isinstance(engine_id, str) or not engine_id.strip():
        raise ValueError("engine_id must not be empty.")
    for profile in PUBLISHED_ENGINE_PROFILES:
        if profile.engine_id == engine_id:
            return profile
    raise KeyError(engine_id)
