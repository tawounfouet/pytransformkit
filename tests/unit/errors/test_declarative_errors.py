from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

import pytransformkit
import pytransformkit.errors as errors
from pytransformkit.errors import (
    DeclarativeErrorContext,
    DeclarativeSchemaCardinalityError,
    DeclarativeSchemaDependencyError,
    DeclarativeSchemaDuplicateFieldError,
    DeclarativeSchemaDuplicateKeyError,
    DeclarativeSchemaDuplicateSchemaError,
    DeclarativeSchemaError,
    DeclarativeSchemaExportError,
    DeclarativeSchemaIOError,
    DeclarativeSchemaLimitError,
    DeclarativeSchemaParseError,
    DeclarativeSchemaTypeError,
    DeclarativeSchemaUnknownPropertyError,
    DeclarativeSchemaValidationError,
    DeclarativeSchemaVersionError,
    PyTransformKitError,
)

DECLARATIVE_ERROR_TYPES = (
    DeclarativeSchemaError,
    DeclarativeSchemaParseError,
    DeclarativeSchemaVersionError,
    DeclarativeSchemaValidationError,
    DeclarativeSchemaUnknownPropertyError,
    DeclarativeSchemaTypeError,
    DeclarativeSchemaDuplicateKeyError,
    DeclarativeSchemaDuplicateFieldError,
    DeclarativeSchemaDuplicateSchemaError,
    DeclarativeSchemaCardinalityError,
    DeclarativeSchemaDependencyError,
    DeclarativeSchemaIOError,
    DeclarativeSchemaExportError,
    DeclarativeSchemaLimitError,
)


def test_declarative_error_hierarchy_matches_contract() -> None:
    assert DeclarativeSchemaError.__bases__ == (PyTransformKitError,)
    assert DeclarativeSchemaParseError.__bases__ == (DeclarativeSchemaError,)
    assert DeclarativeSchemaVersionError.__bases__ == (DeclarativeSchemaError,)
    assert DeclarativeSchemaValidationError.__bases__ == (DeclarativeSchemaError,)
    assert DeclarativeSchemaUnknownPropertyError.__bases__ == (
        DeclarativeSchemaValidationError,
    )
    assert DeclarativeSchemaTypeError.__bases__ == (
        DeclarativeSchemaValidationError,
    )
    assert DeclarativeSchemaDuplicateKeyError.__bases__ == (
        DeclarativeSchemaParseError,
    )
    assert DeclarativeSchemaDuplicateFieldError.__bases__ == (
        DeclarativeSchemaValidationError,
    )
    assert DeclarativeSchemaDuplicateSchemaError.__bases__ == (
        DeclarativeSchemaValidationError,
    )
    assert DeclarativeSchemaCardinalityError.__bases__ == (DeclarativeSchemaError,)
    assert DeclarativeSchemaDependencyError.__bases__ == (DeclarativeSchemaError,)
    assert DeclarativeSchemaIOError.__bases__ == (DeclarativeSchemaError,)
    assert DeclarativeSchemaExportError.__bases__ == (DeclarativeSchemaError,)
    assert DeclarativeSchemaLimitError.__bases__ == (DeclarativeSchemaError,)


def test_declarative_error_codes_are_complete_unique_and_ordered() -> None:
    codes = [str(error_type.error_code) for error_type in DECLARATIVE_ERROR_TYPES]

    assert codes == [f"PTK-DECL-{index:03d}" for index in range(14)]
    assert len(codes) == len(set(codes))


def test_declarative_error_context_is_frozen_and_one_based() -> None:
    context = DeclarativeErrorContext(
        source="schemas/customers.yml",
        line=14,
        column=11,
        object_path="schema.fields[2].type",
    )

    assert context.source == "schemas/customers.yml"
    assert context.line == 14
    assert context.column == 11
    assert context.object_path == "schema.fields[2].type"

    with pytest.raises(FrozenInstanceError):
        context.line = 15


@pytest.mark.parametrize("name", ["source", "object_path"])
def test_declarative_error_context_rejects_blank_text(name: str) -> None:
    with pytest.raises(ValueError, match=name):
        DeclarativeErrorContext(**{name: " "})


@pytest.mark.parametrize("name", ["line", "column"])
@pytest.mark.parametrize("value", [0, -1])
def test_declarative_error_context_rejects_non_positive_positions(
    name: str,
    value: int,
) -> None:
    with pytest.raises(ValueError, match=name):
        DeclarativeErrorContext(**{name: value})


@pytest.mark.parametrize("name", ["line", "column"])
def test_declarative_error_context_rejects_boolean_positions(name: str) -> None:
    with pytest.raises(TypeError, match=name):
        DeclarativeErrorContext(**{name: True})


def test_base_error_exposes_context_aliases() -> None:
    context = DeclarativeErrorContext(
        source="<memory>",
        line=3,
        column=5,
        object_path="schema.fields[0]",
    )
    error = DeclarativeSchemaValidationError(
        "Invalid field.",
        context=context,
    )

    assert error.context == context
    assert error.source == "<memory>"
    assert error.line == 3
    assert error.column == 5
    assert error.object_path == "schema.fields[0]"
    assert str(error.code) == "PTK-DECL-003"


def test_specific_errors_expose_structured_attributes() -> None:
    context = DeclarativeErrorContext(object_path="schema.fields[0]")
    first_context = DeclarativeErrorContext(object_path="schema.fields[1]")

    version = DeclarativeSchemaVersionError(
        2,
        supported_versions=(1,),
        context=context,
    )
    unknown_property = DeclarativeSchemaUnknownPropertyError(
        "nulable",
        allowed_properties=("name", "type", "nullable"),
        context=context,
    )
    type_error = DeclarativeSchemaTypeError(
        "intger",
        expected_type_names=("string", "int64"),
        context=context,
    )
    duplicate_key = DeclarativeSchemaDuplicateKeyError(
        "nullable",
        context=context,
        first_context=first_context,
    )
    duplicate_field = DeclarativeSchemaDuplicateFieldError(
        "customer_id",
        context=context,
        first_context=first_context,
    )
    duplicate_schema = DeclarativeSchemaDuplicateSchemaError(
        "customers",
        context=context,
        first_context=first_context,
    )
    cardinality = DeclarativeSchemaCardinalityError(
        required_count=1,
        actual_count=2,
        context=context,
    )
    dependency = DeclarativeSchemaDependencyError(
        "PyYAML",
        extra_name="yaml",
        context=context,
    )
    io_error = DeclarativeSchemaIOError(
        "schemas/customers.yml",
        "read",
        context=context,
    )
    limit = DeclarativeSchemaLimitError(
        "document_bytes",
        1_048_576,
        1_048_577,
        context=context,
    )

    assert version.actual_version == 2
    assert version.supported_versions == (1,)
    assert unknown_property.property_name == "nulable"
    assert unknown_property.allowed_properties == ("name", "type", "nullable")
    assert type_error.type_name == "intger"
    assert type_error.expected_type_names == ("string", "int64")
    assert duplicate_key.key == "nullable"
    assert duplicate_key.first_context == first_context
    assert duplicate_field.field_name == "customer_id"
    assert duplicate_field.first_context == first_context
    assert duplicate_schema.schema_name == "customers"
    assert duplicate_schema.first_context == first_context
    assert cardinality.required_count == 1
    assert cardinality.actual_count == 2
    assert dependency.dependency_name == "PyYAML"
    assert dependency.extra_name == "yaml"
    assert io_error.path == "schemas/customers.yml"
    assert io_error.operation == "read"
    assert limit.limit_name == "document_bytes"
    assert limit.limit == 1_048_576
    assert limit.actual == 1_048_577


def test_declarative_errors_are_exported_from_errors_namespace_only() -> None:
    expected = {
        "DeclarativeErrorContext",
        *(error_type.__name__ for error_type in DECLARATIVE_ERROR_TYPES),
    }

    assert expected <= set(errors.__all__)
    assert expected.isdisjoint(pytransformkit.__all__)


def test_error_messages_are_actionable_without_being_machine_contracts() -> None:
    dependency = DeclarativeSchemaDependencyError("PyYAML")
    cardinality = DeclarativeSchemaCardinalityError(1, 2)
    export = DeclarativeSchemaExportError("Unsupported custom DataType.")

    assert "pytransformkit[yaml]" in str(dependency)
    assert "expected 1, got 2" in str(cardinality)
    assert "Unsupported custom DataType" in str(export)
