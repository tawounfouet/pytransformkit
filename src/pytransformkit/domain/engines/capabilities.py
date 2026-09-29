"""Portable engine capabilities."""

from enum import StrEnum


class EngineCapability(StrEnum):
    """Logical capabilities an engine adapter can implement."""

    SELECT = "select"
    DROP = "drop"
    RENAME = "rename"
    FILTER = "filter"
    LIMIT = "limit"
    DISTINCT = "distinct"
    CAST = "cast"
    DERIVE = "derive"
    SORT = "sort"
    DEDUPLICATE = "deduplicate"

    JOIN = "join"
    JOIN_INNER = "join_inner"
    JOIN_LEFT = "join_left"
    JOIN_RIGHT = "join_right"
    JOIN_FULL = "join_full"
    JOIN_SEMI = "join_semi"
    JOIN_ANTI = "join_anti"
    JOIN_CROSS = "join_cross"
    UNION = "union"
    INTERSECT = "intersect"
    EXCEPT = "except"

    AGGREGATE = "aggregate"
    WINDOW = "window"
    PIVOT = "pivot"
    UNPIVOT = "unpivot"
    NESTED = "nested"

    LAZY = "lazy"
    STREAMING = "streaming"
    PYTHON_UDF = "python_udf"
