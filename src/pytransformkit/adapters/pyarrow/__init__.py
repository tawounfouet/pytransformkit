"""Public PyArrow adapter surface."""

from pytransformkit.infrastructure.engines.pyarrow import (
    ArrowConversionResult,
    ConversionLossiness,
    ConversionPolicy,
    PyArrowAdapter,
    PyArrowDatasetHandle,
    PyArrowExpressionCompiler,
    PyArrowInterchange,
    PyArrowSchemaInspector,
    PyArrowTypeMapper,
)

PyArrowEngineAdapter = PyArrowAdapter

__all__ = [
    "ArrowConversionResult",
    "ConversionLossiness",
    "ConversionPolicy",
    "PyArrowAdapter",
    "PyArrowDatasetHandle",
    "PyArrowEngineAdapter",
    "PyArrowExpressionCompiler",
    "PyArrowInterchange",
    "PyArrowSchemaInspector",
    "PyArrowTypeMapper",
]
