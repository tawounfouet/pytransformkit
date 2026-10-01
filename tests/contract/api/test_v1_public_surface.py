from __future__ import annotations

import warnings

import pytransformkit
from pytransformkit import DataType, Field
from pytransformkit.domain.data.data_types import (
    BinaryType,
    BooleanType,
    DateType,
    DecimalType,
    FloatType,
    IntegerType,
    StringType,
    TimestampType,
    TimeType,
    UnknownType,
)

FORBIDDEN_ROOT_EXPORTS = {
    "CredentialReference",
    "EngineRegistry",
    "ExecutionContext",
    "ExecutionMode",
    "OptimizedLogicalPlan",
    "PhysicalPlan",
    "Pipeline",
    "PipelineExecutionResult",
    "RetrySafety",
    "RunPipelineService",
    "TransformationGraph",
    "WriteMode",
    "WriteStatus",
}


def test_root_exports_are_curated_for_v1() -> None:
    exports = set(pytransformkit.__all__)

    assert FORBIDDEN_ROOT_EXPORTS.isdisjoint(exports)
    assert {
        "DataType",
        "Dataset",
        "Expression",
        "Field",
        "InputBinding",
        "LogicalPlan",
        "OutputBinding",
        "ResourceReference",
        "Schema",
        "TransformationExecutionId",
        "TransformationPlan",
        "TransformationResult",
        "TransformationRuntime",
        "col",
        "lit",
    }.issubset(exports)


def test_legacy_root_names_warn_without_becoming_canonical() -> None:
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        pipeline = pytransformkit.Pipeline
        run_service = pytransformkit.RunPipelineService
        write_mode = pytransformkit.WriteMode

    assert pipeline.__name__ == "Pipeline"
    assert run_service.__name__ == "RunPipelineService"
    assert write_mode.__name__ == "WriteMode"
    assert len(captured) == 3
    assert all(item.category is DeprecationWarning for item in captured)


def test_datatype_v1_factories_are_stable_values() -> None:
    assert DataType.boolean() == BooleanType()
    assert DataType.int8() == IntegerType(bits=8, signed=True)
    assert DataType.int16() == IntegerType(bits=16, signed=True)
    assert DataType.int32() == IntegerType(bits=32, signed=True)
    assert DataType.int64() == IntegerType(bits=64, signed=True)
    assert DataType.uint8() == IntegerType(bits=8, signed=False)
    assert DataType.uint16() == IntegerType(bits=16, signed=False)
    assert DataType.uint32() == IntegerType(bits=32, signed=False)
    assert DataType.uint64() == IntegerType(bits=64, signed=False)
    assert DataType.float32() == FloatType(bits=32)
    assert DataType.float64() == FloatType(bits=64)
    assert DataType.decimal(18, 2) == DecimalType(18, 2)
    assert DataType.string() == StringType()
    assert DataType.binary() == BinaryType()
    assert DataType.date() == DateType()
    assert DataType.time("ms") == TimeType("ms")
    assert DataType.timestamp(timezone="UTC") == TimestampType(timezone="UTC")
    assert DataType.unknown() == UnknownType()


def test_field_dtype_is_a_non_breaking_v1_alias() -> None:
    field = Field("amount", DataType.decimal(18, 2), nullable=False)

    assert field.dtype is field.data_type


def test_stable_qualified_namespaces_import() -> None:
    import pytransformkit.authoring as authoring
    import pytransformkit.engines as engines
    import pytransformkit.expressions as expressions
    import pytransformkit.planning as planning
    import pytransformkit.runtime as runtime
    import pytransformkit.serialization as serialization
    import pytransformkit.transformations as transformations
    from pytransformkit.adapters import pandas as pandas_adapter
    from pytransformkit.adapters import polars as polars_adapter

    assert authoring.__all__ == ["TransformationPlanBuilder"]
    assert "Expression" in expressions.__all__
    assert "TransformationSpec" in transformations.__all__
    assert planning.__all__ == [
        "LogicalOptimizer",
        "LogicalPlan",
        "TransformationCompiler",
    ]
    assert engines.__all__ == [
        "Capability",
        "EngineAdapter",
        "EngineCapability",
        "EngineDescriptor",
        "EngineRegistry",
    ]
    assert "OutputMode" not in runtime.__all__
    assert "ContractCodec" not in serialization.__all__
    assert "SemanticTypeRegistry" not in serialization.__all__
    assert pandas_adapter.__all__ == ["PandasEngineAdapter"]
    assert polars_adapter.__all__ == ["PolarsEngineAdapter"]
