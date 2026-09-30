"""Optional PyArrow execution and interchange adapter."""

from pytransformkit.infrastructure.engines.pyarrow.adapter import PyArrowAdapter
from pytransformkit.infrastructure.engines.pyarrow.conversion import (
    ArrowConversionResult,
    ConversionLossiness,
    ConversionPolicy,
    PyArrowInterchange,
)
from pytransformkit.infrastructure.engines.pyarrow.expressions import (
    PyArrowExpressionCompiler,
)
from pytransformkit.infrastructure.engines.pyarrow.handle import (
    PyArrowDatasetHandle,
)
from pytransformkit.infrastructure.engines.pyarrow.types import (
    PyArrowSchemaInspector,
    PyArrowTypeMapper,
)

__all__ = [
    "ArrowConversionResult",
    "ConversionLossiness",
    "ConversionPolicy",
    "PyArrowAdapter",
    "PyArrowDatasetHandle",
    "PyArrowExpressionCompiler",
    "PyArrowInterchange",
    "PyArrowSchemaInspector",
    "PyArrowTypeMapper",
]
