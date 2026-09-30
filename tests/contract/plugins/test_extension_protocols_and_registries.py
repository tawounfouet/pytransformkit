from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

pd = pytest.importorskip("pandas")
pytest.importorskip("polars")
pytest.importorskip("pyarrow")
pytest.importorskip("duckdb")

from pytransformkit import TransformationPlan
from pytransformkit.adapters.duckdb import DuckDBEngineAdapter
from pytransformkit.adapters.pandas import PandasEngineAdapter
from pytransformkit.adapters.polars import PolarsEngineAdapter
from pytransformkit.adapters.pyarrow import PyArrowEngineAdapter
from pytransformkit.application.extensions import (
    FunctionDefinition,
    FunctionRegistry,
    OptimizerRuleRegistry,
    ResourceResolver,
    ResourceResolverRegistry,
    TelemetrySinkRegistry,
)
from pytransformkit.application.io import Reader, ResourceIORegistry, Writer
from pytransformkit.application.planning import LogicalOptimizer
from pytransformkit.application.ports.engines import EngineAdapter
from pytransformkit.domain.data.data_types import IntegerType
from pytransformkit.domain.data.field import Field
from pytransformkit.domain.data.schema import Schema
from pytransformkit.domain.expressions.functions import (
    FunctionCall,
    FunctionIdentifier,
)
from pytransformkit.domain.pipelines.plan import LogicalPlan
from pytransformkit.domain.resources import ResourceReference
from pytransformkit.domain.runtime import NullTelemetrySink, TelemetrySink
from pytransformkit.errors import PluginConflictError, RegistryFrozenError
from pytransformkit.functions import col
from pytransformkit.infrastructure.io.local import (
    LocalFilePathResolver,
    LocalFileReader,
    LocalFileWriter,
)
from pytransformkit.planning import TransformationCompiler


class RenamePlanRule:
    rule_id = "tests.rename-plan"

    def apply(self, plan: LogicalPlan) -> LogicalPlan:
        if plan.pipeline_name.endswith("-optimized"):
            return plan
        return replace(plan, pipeline_name=f"{plan.pipeline_name}-optimized")


def _logical_plan() -> LogicalPlan:
    schema = Schema((Field("amount", IntegerType(), nullable=False),))
    builder = TransformationPlan.builder("extension_rule")
    source = builder.input("input", schema=schema)
    selected = builder.select("selected", source=source, columns=("amount",))
    return TransformationCompiler().compile(
        builder.output("output", selected).build()
    )


def test_official_builtins_satisfy_public_extension_protocols(tmp_path: Path) -> None:
    assert isinstance(PandasEngineAdapter(), EngineAdapter)
    assert isinstance(PolarsEngineAdapter(), EngineAdapter)
    assert isinstance(PyArrowEngineAdapter(), EngineAdapter)
    assert isinstance(DuckDBEngineAdapter(), EngineAdapter)

    reader = LocalFileReader(tmp_path)
    writer = LocalFileWriter(tmp_path)
    resolver = LocalFilePathResolver(tmp_path)

    assert isinstance(reader, Reader)
    assert isinstance(writer, Writer)
    assert isinstance(resolver, ResourceResolver)
    assert isinstance(NullTelemetrySink(), TelemetrySink)


def test_resource_resolver_registry_is_explicit_and_freezable(tmp_path: Path) -> None:
    registry = ResourceResolverRegistry()
    resolver = LocalFilePathResolver(tmp_path)
    registry.register(resolver)

    resolved = registry.resolve(
        ResourceReference(scheme="file", locator="nested/data.parquet")
    )

    assert resolved == (tmp_path / "nested/data.parquet").resolve()

    with pytest.raises(PluginConflictError):
        registry.register(resolver)

    registry.freeze()
    with pytest.raises(RegistryFrozenError):
        registry.register(LocalFilePathResolver(tmp_path / "other"), replace=True)


def test_function_registry_builds_only_registered_expression_factories() -> None:
    registry = FunctionRegistry()
    definition = FunctionDefinition(
        identifier=FunctionIdentifier("demo.identity"),
        builder=lambda arguments: FunctionCall(
            FunctionIdentifier("demo.identity"),
            arguments,
        ),
    )
    registry.register(definition)

    expression = registry.call("demo.identity", col("amount"))

    assert isinstance(expression, FunctionCall)
    assert str(expression.function) == "demo.identity"

    with pytest.raises(PluginConflictError):
        registry.register(definition)


def test_optimizer_rule_registry_drives_explicit_logical_optimizer_extension() -> None:
    rules = OptimizerRuleRegistry()
    rules.register(RenamePlanRule())

    result = LogicalOptimizer(
        extension_rules=rules.rules(),
    ).optimize_with_report(_logical_plan())

    assert result.plan.pipeline_name == "extension_rule-optimized"
    assert "tests.rename-plan" in {
        application.rule_id for application in result.report.applications
    }


def test_telemetry_and_existing_io_registries_freeze_explicitly(
    tmp_path: Path,
) -> None:
    telemetry = TelemetrySinkRegistry()
    telemetry.register("null", NullTelemetrySink())
    telemetry.freeze()
    with pytest.raises(RegistryFrozenError):
        telemetry.register("other", NullTelemetrySink())

    resources = ResourceIORegistry()
    resources.register_reader(LocalFileReader(tmp_path))
    resources.register_writer(LocalFileWriter(tmp_path))
    resources.freeze()
    with pytest.raises(RegistryFrozenError):
        resources.register_reader(LocalFileReader(tmp_path),)
