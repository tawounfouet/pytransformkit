"""Core public Expression constructors."""

from pytransformkit.domain.data.data_types import DataType
from pytransformkit.domain.data.field_path import FieldPath
from pytransformkit.domain.expressions.literals import Literal
from pytransformkit.domain.expressions.references import ColumnReference


def col(name: str) -> ColumnReference:
    return ColumnReference(path=FieldPath.of(name))


def lit(value: object, data_type: DataType | None = None) -> Literal:
    return Literal(value=value, data_type=data_type)
