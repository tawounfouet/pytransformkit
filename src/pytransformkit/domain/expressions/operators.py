"""Logical Expression operators."""

from enum import StrEnum


class BinaryOperator(StrEnum):
    EQ = "eq"
    NE = "ne"
    LT = "lt"
    LE = "le"
    GT = "gt"
    GE = "ge"
    ADD = "add"
    SUB = "sub"
    MUL = "mul"
    DIV = "div"
    AND = "and"
    OR = "or"


class UnaryOperator(StrEnum):
    NOT = "not"
    NEGATE = "negate"
