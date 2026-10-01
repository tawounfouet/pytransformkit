"""Installed-artifact smoke for the canonical V1 authoring and planning API."""

from pytransformkit import DataType, Field, Schema, TransformationPlan, col
from pytransformkit.planning import TransformationCompiler


schema = Schema(
    fields=(
        Field("customer_id", DataType.int64(), nullable=False),
        Field("status", DataType.string(), nullable=False),
        Field("amount", DataType.float64(), nullable=False),
    )
)

builder = TransformationPlan.builder("paid_orders")
orders = builder.input("orders", schema=schema)
paid = builder.filter(
    "paid_only",
    source=orders,
    where=col("status") == "PAID",
)
plan = builder.output("paid_orders", paid).build()

logical = TransformationCompiler().compile(plan)

assert logical.output_names == ("paid_orders",)
assert logical.output_schema == schema
assert plan.fingerprint() == logical.fingerprint()
assert "LogicalPlan" in plan.explain()
assert '"format_version":1' in logical.explain(format="json")
assert schema.fingerprint().algorithm == "sha256"

print("core-getting-started: OK")
