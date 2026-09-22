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
    AGGREGATE = "aggregate"
    WINDOW = "window"
    PIVOT = "pivot"
    UNPIVOT = "unpivot"
    NESTED = "nested"

    LAZY = "lazy"
    STREAMING = "streaming"
    PYTHON_UDF = "python_udf"
