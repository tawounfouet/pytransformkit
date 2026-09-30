"""Deterministic semantic fingerprints for compiled LogicalPlan values."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID

from pytransformkit.domain.expressions.base import Expression
from pytransformkit.domain.expressions.fingerprint import canonical_expression
from pytransformkit.domain.pipelines.plan import LogicalPlan
from pytransformkit.domain.shared.fingerprint import Fingerprint
from pytransformkit.domain.shared.identifiers import Identifier


def logical_plan_fingerprint(plan: LogicalPlan) -> Fingerprint:
    """Return a deterministic fingerprint excluding runtime/random identities."""
    if not isinstance(plan, LogicalPlan):
        raise TypeError("logical_plan_fingerprint requires a LogicalPlan.")
    canonical = canonical_logical_plan(plan)
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return Fingerprint("sha256", digest)


def canonical_logical_plan(plan: LogicalPlan) -> str:
    """Return canonical JSON for semantic LogicalPlan content."""
    if not isinstance(plan, LogicalPlan):
        raise TypeError("canonical_logical_plan requires a LogicalPlan.")

    node_index = {node.node_id: index for index, node in enumerate(plan.nodes)}
    nodes = []
    for node in plan.nodes:
        nodes.append(
            {
                "kind": node.kind.value,
                "name": node.name,
                "inputs": [node_index[item] for item in node.input_node_ids],
                "input_schemas": [
                    _canonical_value(schema) for schema in node.input_schemas
                ],
                "output_schema": _canonical_value(node.output_schema),
                "transformation": _canonical_value(node.transformation),
            }
        )

    payload = {
        "plan_name": plan.plan_name,
        "nodes": nodes,
        "outputs": [
            {
                "name": name,
                "schema": _canonical_value(schema),
            }
            for name, schema in plan.output_schemas
        ],
    }
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _canonical_value(value: object) -> object:
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        return {"__float__": value.hex()}
    if isinstance(value, Decimal):
        return {"__decimal__": str(value)}
    if isinstance(value, datetime):
        return {"__datetime__": value.isoformat()}
    if isinstance(value, date):
        return {"__date__": value.isoformat()}
    if isinstance(value, UUID):
        return {"__uuid__": str(value)}
    if isinstance(value, Enum):
        return {
            "__enum__": f"{type(value).__module__}.{type(value).__qualname__}",
            "value": value.value,
        }
    if isinstance(value, Expression):
        return {"__expression__": canonical_expression(value)}
    if isinstance(value, Identifier):
        return {
            "__identifier_type__": type(value).__qualname__,
            "value": str(value),
        }
    if is_dataclass(value):
        return {
            "__type__": f"{type(value).__module__}.{type(value).__qualname__}",
            "fields": {
                field.name: _canonical_value(getattr(value, field.name))
                for field in fields(value)
            },
        }
    if isinstance(value, Mapping):
        return {
            str(key): _canonical_value(item)
            for key, item in sorted(
                value.items(),
                key=lambda pair: str(pair[0]),
            )
        }
    if isinstance(value, (tuple, list)):
        return [_canonical_value(item) for item in value]
    if isinstance(value, (set, frozenset)):
        canonical_items = [_canonical_value(item) for item in value]
        return sorted(
            canonical_items,
            key=lambda item: json.dumps(
                item,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ),
        )

    raise TypeError(
        "LogicalPlan contains a value without canonical fingerprint semantics: "
        f"{type(value).__name__!r}."
    )
