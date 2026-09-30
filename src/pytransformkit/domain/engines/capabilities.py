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
    WINDOW_ROWS_CUMULATIVE = "window_rows_cumulative"
    WINDOW_ROWS_MOVING = "window_rows_moving"
    WINDOW_ROWS_ARBITRARY = "window_rows_arbitrary"
    WINDOW_RANGE = "window_range"
    PIVOT = "pivot"
    UNPIVOT = "unpivot"
    EXPLODE = "explode"
    FLATTEN = "flatten"
    NESTED = "nested"
    TEMPORAL = "temporal"
    DURATION = "duration"
    QUALITY = "quality"

    LAZY = "lazy"
    STREAMING = "streaming"
    PYTHON_UDF = "python_udf"
