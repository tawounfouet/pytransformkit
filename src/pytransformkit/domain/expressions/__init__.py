"""Engine-independent logical Expression model."""

from pytransformkit.domain.expressions.base import Expression, ensure_expression
from pytransformkit.domain.expressions.binary import BinaryExpression
from pytransformkit.domain.expressions.dependencies import (
    ExpressionDependencyExtractor,
)
from pytransformkit.domain.expressions.fingerprint import (
    canonical_expression,
    expression_fingerprint,
)
from pytransformkit.domain.expressions.functions import (
    FunctionCall,
    FunctionIdentifier,
)
from pytransformkit.domain.expressions.literals import Literal
from pytransformkit.domain.expressions.operators import (
    BinaryOperator,
    UnaryOperator,
)
from pytransformkit.domain.expressions.predicates import (
    IsNotNullExpression,
    IsNullExpression,
)
from pytransformkit.domain.expressions.references import ColumnReference
from pytransformkit.domain.expressions.typing import (
    ExpressionType,
    ExpressionTypeResolver,
)
from pytransformkit.domain.expressions.unary import UnaryExpression

__all__ = [
    "BinaryExpression",
    "BinaryOperator",
    "ColumnReference",
    "Expression",
    "ExpressionDependencyExtractor",
    "ExpressionType",
    "ExpressionTypeResolver",
    "FunctionCall",
    "FunctionIdentifier",
    "IsNotNullExpression",
    "IsNullExpression",
    "Literal",
    "UnaryExpression",
    "UnaryOperator",
    "canonical_expression",
    "ensure_expression",
    "expression_fingerprint",
]
