"""Portable physical write semantics."""

from enum import StrEnum


class WriteMode(StrEnum):
    """Physical storage behavior for one explicit target resource."""

    CREATE_NEW = "create_new"
    FAIL_IF_EXISTS = "fail_if_exists"
    REPLACE = "replace"
    APPEND = "append"


class WriteStatus(StrEnum):
    """Observed outcome of one bounded physical write attempt."""

    SUCCEEDED = "succeeded"
    FAILED = "failed"
    UNKNOWN_OUTCOME = "unknown_outcome"
