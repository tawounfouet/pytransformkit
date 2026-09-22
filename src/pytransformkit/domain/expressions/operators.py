"""Logical Expression operators."""

from enum import Enum


class BinaryOperator(str, Enum):
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


class UnaryOperator(str, Enum):
    NOT = "not"
    NEGATE = "negate"
