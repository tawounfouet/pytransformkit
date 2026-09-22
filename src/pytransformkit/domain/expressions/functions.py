"""Logical function Expressions."""

from dataclasses import dataclass

from pytransformkit.domain.expressions.base import Expression


@dataclass(frozen=True, slots=True)
class FunctionIdentifier:
    value: str

    def __post_init__(self) -> None:
        if not self.value or not self.value.strip():
            raise ValueError("Function identifier must not be empty.")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True, eq=False)
class FunctionCall(Expression):
    function: FunctionIdentifier
    arguments: tuple[Expression, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.function, FunctionIdentifier):
            raise TypeError("FunctionCall function must be a FunctionIdentifier.")
        if not isinstance(self.arguments, tuple):
            raise TypeError("FunctionCall arguments must be provided as a tuple.")
        if any(not isinstance(argument, Expression) for argument in self.arguments):
            raise TypeError("FunctionCall arguments must contain only Expressions.")
