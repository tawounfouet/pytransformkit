from __future__ import annotations

import importlib
import os

import pytest

from pytransformkit.errors import (
    DeclarativeSchemaDependencyError,
    DeclarativeSchemaDuplicateKeyError,
    DeclarativeSchemaLimitError,
    DeclarativeSchemaParseError,
    DeclarativeSchemaTypeError,
    DeclarativeSchemaUnknownPropertyError,
    DeclarativeSchemaValidationError,
)
from pytransformkit.schema_io._model import (
    DecimalTypeDefinition,
    IntegerTypeDefinition,
    ListTypeDefinition,
    MapTypeDefinition,
    StringTypeDefinition,
    StructTypeDefinition,
    TimestampTypeDefinition,
)
from pytransformkit.schema_io._yaml import (
    DeclarativeParsingLimits,
    YamlSchemaParser,
)

yaml = pytest.importorskip("yaml")


def test_basic_single_schema_decodes_to_normalized_model() -> None:
    document = YamlSchemaParser().parse(
        """
version: 1
schema:
  name: customers
  fields:
    - name: customer_id
      type: int64
      nullable: false
      description: Stable identifier
    - name: balance
      type:
        decimal:
          precision: 18
          scale: 2
"""
    )

    assert document.version == 1
    assert len(document.schemas) == 1
    schema = document.schemas[0]
    assert schema.name == "customers"
    assert tuple(field.name for field in schema.fields) == (
        "customer_id",
        "balance",
    )
    assert schema.fields[0].data_type == IntegerTypeDefinition()
    assert schema.fields[0].nullable is False
    assert schema.fields[0].description == "Stable identifier"
    assert schema.fields[1].data_type == DecimalTypeDefinition(18, 2)


def test_multi_schema_order_and_names_are_preserved() -> None:
    document = YamlSchemaParser().parse(
        """
version: 1
schemas:
  customers:
    fields: []
  orders:
    fields: []
"""
    )

    assert tuple(schema.name for schema in document.schemas) == (
        "customers",
        "orders",
    )


def test_nested_list_struct_map_decodes_recursively() -> None:
    document = YamlSchemaParser().parse(
        """
version: 1
schema:
  name: customers
  fields:
    - name: payload
      type:
        map:
          key:
            type: string
          value:
            type:
              list:
                element:
                  type:
                    struct:
                      fields:
                        - name: created_at
                          type:
                            timestamp:
                              unit: ns
                              timezone: UTC
                          nullable: false
                element_nullable: false
          value_nullable: false
"""
    )

    data_type = document.schemas[0].fields[0].data_type
    assert isinstance(data_type, MapTypeDefinition)
    assert data_type.key_type == StringTypeDefinition()
    assert data_type.value_nullable is False
    assert isinstance(data_type.value_type, ListTypeDefinition)
    assert data_type.value_type.element_nullable is False
    assert isinstance(data_type.value_type.element_type, StructTypeDefinition)
    nested_field = data_type.value_type.element_type.fields[0]
    assert nested_field.name == "created_at"
    assert nested_field.nullable is False
    assert nested_field.data_type == TimestampTypeDefinition(
        unit="ns",
        timezone="UTC",
    )


@pytest.mark.parametrize(
    ("spelling", "expected"),
    [
        ("integer", IntegerTypeDefinition()),
        ("int8", IntegerTypeDefinition(bits=8, signed=True)),
        ("uint32", IntegerTypeDefinition(bits=32, signed=False)),
    ],
)
def test_integer_authoring_forms_are_normalized(
    spelling: str,
    expected: IntegerTypeDefinition,
) -> None:
    document = YamlSchemaParser().parse(
        f"""
version: 1
schema:
  name: sample
  fields:
    - name: value
      type: {spelling}
"""
    )

    assert document.schemas[0].fields[0].data_type == expected


def test_unknown_type_fails_closed_without_unknown_fallback() -> None:
    with pytest.raises(DeclarativeSchemaTypeError) as error:
        YamlSchemaParser().parse(
            """
version: 1
schema:
  name: sample
  fields:
    - name: value
      type: intger
"""
        )

    assert str(error.value.code) == "PTK-DECL-005"
    assert error.value.type_name == "intger"
    assert error.value.object_path == "schema.fields[0].type"


def test_unknown_properties_fail_recursively() -> None:
    with pytest.raises(DeclarativeSchemaUnknownPropertyError) as error:
        YamlSchemaParser().parse(
            """
version: 1
schema:
  name: sample
  fields:
    - name: value
      type:
        decimal:
          precision: 18
          scale: 2
          rounding: half_even
"""
        )

    assert str(error.value.code) == "PTK-DECL-004"
    assert error.value.property_name == "rounding"
    assert error.value.object_path == "schema.fields[0].type.decimal.rounding"


@pytest.mark.parametrize(
    "yaml_text",
    [
        """
version: 1
owner: data-team
schema:
  name: sample
  fields: []
""",
        """
version: 1
schema:
  name: sample
  description: unsupported
  fields: []
""",
        """
version: 1
schema:
  name: sample
  fields:
    - name: value
      type: string
      metadata: {}
""",
        """
version: 1
schema:
  name: sample
  fields:
    - name: nested
      type:
        struct:
          fields:
            - name: city
              type: string
              description: unsupported
""",
    ],
)
def test_unsupported_metadata_and_properties_are_never_silently_dropped(
    yaml_text: str,
) -> None:
    with pytest.raises(DeclarativeSchemaUnknownPropertyError):
        YamlSchemaParser().parse(yaml_text)


@pytest.mark.parametrize(
    "yaml_text",
    [
        """
version: 1
version: 1
schema:
  name: sample
  fields: []
""",
        """
version: 1
schema:
  name: sample
  fields:
    - name: value
      type: string
      nullable: true
      nullable: false
""",
        """
version: 1
schema:
  name: sample
  fields:
    - name: value
      type:
        decimal:
          precision: 18
          precision: 20
          scale: 2
""",
    ],
)
def test_duplicate_mapping_keys_are_rejected_before_normalization(
    yaml_text: str,
) -> None:
    with pytest.raises(DeclarativeSchemaDuplicateKeyError) as error:
        YamlSchemaParser().parse(yaml_text, source="schemas.yml")

    assert str(error.value.code) == "PTK-DECL-006"
    assert error.value.source == "schemas.yml"
    assert error.value.line is not None
    assert error.value.column is not None
    assert error.value.first_context is not None


@pytest.mark.parametrize(
    "yaml_text",
    [
        """
version: 1
base: &common
  type: string
schema:
  name: sample
  fields: []
""",
        """
version: 1
schema:
  name: sample
  fields:
    - name: value
      type: *common
""",
        """
version: 1
schema:
  name: sample
  fields:
    - &field
      name: value
      type: string
""",
    ],
)
def test_anchors_and_aliases_are_rejected_during_preflight(yaml_text: str) -> None:
    with pytest.raises(DeclarativeSchemaParseError) as error:
        YamlSchemaParser().parse(yaml_text)

    assert str(error.value.code) == "PTK-DECL-001"


def test_merge_keys_are_rejected_as_parse_policy_failure() -> None:
    with pytest.raises(DeclarativeSchemaParseError) as error:
        YamlSchemaParser().parse(
            """
version: 1
base: &base
  fields: []
schema:
  <<: *base
  name: sample
"""
        )

    assert str(error.value.code) == "PTK-DECL-001"


@pytest.mark.parametrize(
    "yaml_text",
    [
        """
version: 1
schema:
  name: sample
  fields:
    - name: value
      type: !CustomType {}
""",
        """
version: 1
schema:
  name: sample
  fields:
    - name: value
      type: !!python/name:builtins.str
""",
    ],
)
def test_explicit_and_python_specific_tags_are_rejected(yaml_text: str) -> None:
    with pytest.raises(DeclarativeSchemaParseError) as error:
        YamlSchemaParser().parse(yaml_text)

    assert str(error.value.code) == "PTK-DECL-001"


def test_python_object_tag_never_constructs_object(monkeypatch: pytest.MonkeyPatch) -> None:
    sentinel = {"called": False}

    def fail_if_called(*args: object, **kwargs: object) -> None:
        sentinel["called"] = True
        raise AssertionError("arbitrary construction must not run")

    monkeypatch.setattr(os, "system", fail_if_called)

    with pytest.raises(DeclarativeSchemaParseError):
        YamlSchemaParser().parse(
            """
version: 1
schema:
  name: sample
  fields:
    - name: value
      type: !!python/object/apply:os.system ["echo forbidden"]
"""
        )

    assert sentinel["called"] is False


def test_multiple_yaml_documents_are_rejected() -> None:
    with pytest.raises(DeclarativeSchemaParseError) as error:
        YamlSchemaParser().parse(
            """
version: 1
schema:
  name: first
  fields: []
---
version: 1
schema:
  name: second
  fields: []
"""
        )

    assert str(error.value.code) == "PTK-DECL-001"


def test_malformed_yaml_is_translated_and_chained() -> None:
    with pytest.raises(DeclarativeSchemaParseError) as error:
        YamlSchemaParser().parse(
            """
version: 1
schema: [
"""
        )

    assert str(error.value.code) == "PTK-DECL-001"
    assert error.value.__cause__ is not None


@pytest.mark.parametrize("spelling", ["yes", "no", "on", "off", "YES", "OFF"])
def test_yaml_11_boolean_ambiguities_do_not_become_booleans(spelling: str) -> None:
    with pytest.raises(DeclarativeSchemaValidationError):
        YamlSchemaParser().parse(
            f"""
version: 1
schema:
  name: sample
  fields:
    - name: value
      type: string
      nullable: {spelling}
"""
        )


def test_implicit_iso_date_remains_a_string() -> None:
    document = YamlSchemaParser().parse(
        """
version: 1
schema:
  name: 2026-10-01
  fields: []
"""
    )

    assert document.schemas[0].name == "2026-10-01"
    assert type(document.schemas[0].name) is str


def test_global_pyyaml_safe_loader_behavior_is_not_mutated() -> None:
    before = yaml.safe_load("flag: yes")
    assert before == {"flag": True}

    with pytest.raises(DeclarativeSchemaValidationError):
        YamlSchemaParser().parse(
            """
version: 1
schema:
  name: sample
  fields:
    - name: value
      type: string
      nullable: yes
"""
        )

    after = yaml.safe_load("flag: yes")
    assert after == {"flag": True}


@pytest.mark.parametrize(
    "spelling",
    [".nan", ".inf", "-.inf", "NaN", "Infinity"],
)
def test_non_finite_numeric_spellings_are_rejected(spelling: str) -> None:
    with pytest.raises(DeclarativeSchemaParseError):
        YamlSchemaParser().parse(
            f"""
version: 1
schema:
  name: sample
  fields:
    - name: value
      type: string
      description: {spelling}
"""
        )


def test_explicit_null_description_is_rejected() -> None:
    with pytest.raises(DeclarativeSchemaValidationError) as error:
        YamlSchemaParser().parse(
            """
version: 1
schema:
  name: sample
  fields:
    - name: value
      type: string
      description: null
"""
        )

    assert error.value.object_path == "schema.fields[0].description"


def test_quoted_false_is_not_coerced_to_boolean() -> None:
    with pytest.raises(DeclarativeSchemaValidationError) as error:
        YamlSchemaParser().parse(
            """
version: 1
schema:
  name: sample
  fields:
    - name: value
      type: string
      nullable: "false"
"""
        )

    assert error.value.object_path == "schema.fields[0].nullable"


def test_string_to_integer_coercion_is_forbidden_for_decimal_parameters() -> None:
    with pytest.raises(DeclarativeSchemaTypeError) as error:
        YamlSchemaParser().parse(
            """
version: 1
schema:
  name: sample
  fields:
    - name: value
      type:
        decimal:
          precision: "18"
          scale: 2
"""
        )

    assert error.value.object_path == "schema.fields[0].type.decimal.precision"


def test_payload_limit_is_enforced_on_utf8_bytes() -> None:
    parser = YamlSchemaParser(
        DeclarativeParsingLimits(
            max_payload_bytes=8,
            max_nesting_depth=64,
            max_schemas=256,
            max_fields_per_schema=10_000,
            max_total_field_nodes=50_000,
        )
    )

    with pytest.raises(DeclarativeSchemaLimitError) as error:
        parser.parse("version: 1")

    assert error.value.limit_name == "payload_bytes"
    assert error.value.limit == 8
    assert error.value.actual == len("version: 1".encode())


def test_minimal_valid_document_respects_exact_depth_boundary() -> None:
    text = """
version: 1
schema:
  name: sample
  fields: []
"""
    parser = YamlSchemaParser(
        DeclarativeParsingLimits(
            max_payload_bytes=1_048_576,
            max_nesting_depth=3,
            max_schemas=256,
            max_fields_per_schema=10_000,
            max_total_field_nodes=50_000,
        )
    )
    assert parser.parse(text).schemas[0].name == "sample"

    too_shallow = YamlSchemaParser(
        DeclarativeParsingLimits(
            max_payload_bytes=1_048_576,
            max_nesting_depth=2,
            max_schemas=256,
            max_fields_per_schema=10_000,
            max_total_field_nodes=50_000,
        )
    )
    with pytest.raises(DeclarativeSchemaLimitError) as error:
        too_shallow.parse(text)

    assert error.value.limit_name == "nesting_depth"
    assert error.value.actual == 3


def test_schema_count_limit_is_enforced_before_decoding_all_schemas() -> None:
    parser = YamlSchemaParser(
        DeclarativeParsingLimits(
            max_payload_bytes=1_048_576,
            max_nesting_depth=64,
            max_schemas=1,
            max_fields_per_schema=10_000,
            max_total_field_nodes=50_000,
        )
    )

    with pytest.raises(DeclarativeSchemaLimitError) as error:
        parser.parse(
            """
version: 1
schemas:
  first:
    fields: []
  second:
    fields: []
"""
        )

    assert error.value.limit_name == "schemas"
    assert error.value.actual == 2


def test_fields_per_schema_limit_is_enforced() -> None:
    parser = YamlSchemaParser(
        DeclarativeParsingLimits(
            max_payload_bytes=1_048_576,
            max_nesting_depth=64,
            max_schemas=256,
            max_fields_per_schema=1,
            max_total_field_nodes=50_000,
        )
    )

    with pytest.raises(DeclarativeSchemaLimitError) as error:
        parser.parse(
            """
version: 1
schema:
  name: sample
  fields:
    - name: first
      type: string
    - name: second
      type: string
"""
        )

    assert error.value.limit_name == "fields_per_schema"
    assert error.value.actual == 2


def test_total_field_node_limit_counts_nested_struct_fields() -> None:
    parser = YamlSchemaParser(
        DeclarativeParsingLimits(
            max_payload_bytes=1_048_576,
            max_nesting_depth=64,
            max_schemas=256,
            max_fields_per_schema=10_000,
            max_total_field_nodes=2,
        )
    )

    with pytest.raises(DeclarativeSchemaLimitError) as error:
        parser.parse(
            """
version: 1
schema:
  name: sample
  fields:
    - name: payload
      type:
        struct:
          fields:
            - name: first
              type: string
            - name: second
              type: string
"""
        )

    assert error.value.limit_name == "total_field_nodes"
    assert error.value.actual == 3


def test_source_line_column_and_object_path_are_retained_when_available() -> None:
    with pytest.raises(DeclarativeSchemaUnknownPropertyError) as error:
        YamlSchemaParser().parse(
            """
version: 1
schema:
  name: sample
  fields:
    - name: value
      type: string
      nulable: false
""",
            source="schemas/sample.yml",
        )

    assert error.value.source == "schemas/sample.yml"
    assert error.value.line is not None
    assert error.value.column is not None
    assert error.value.object_path == "schema.fields[0].nulable"


def test_invalid_utf8_bytes_are_translated() -> None:
    with pytest.raises(DeclarativeSchemaParseError) as error:
        YamlSchemaParser().parse(b"version: 1\xff")

    assert error.value.__cause__ is not None


def test_utf8_bom_is_accepted() -> None:
    document = YamlSchemaParser().parse(
        b"\xef\xbb\xbfversion: 1\nschema:\n  name: sample\n  fields: []\n"
    )

    assert document.schemas[0].name == "sample"


def test_environment_looking_strings_are_not_interpolated(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PTK_DECL_TEST_SECRET", "should-not-appear")

    document = YamlSchemaParser().parse(
        """
version: 1
schema:
  name: "${PTK_DECL_TEST_SECRET}"
  fields: []
"""
    )

    assert document.schemas[0].name == "${PTK_DECL_TEST_SECRET}"


def test_missing_yaml_dependency_is_translated(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    yaml_module = importlib.import_module("pytransformkit.schema_io._yaml")
    real_import_module = yaml_module.importlib.import_module

    def controlled_import(name: str, package: str | None = None) -> object:
        if name == "yaml":
            raise ModuleNotFoundError("No module named 'yaml'")
        return real_import_module(name, package)

    monkeypatch.setattr(yaml_module.importlib, "import_module", controlled_import)

    with pytest.raises(DeclarativeSchemaDependencyError) as error:
        yaml_module.YamlSchemaParser().parse(
            "version: 1\nschema:\n  name: sample\n  fields: []\n"
        )

    assert str(error.value.code) == "PTK-DECL-010"
    assert error.value.dependency_name == "PyYAML"


@pytest.mark.parametrize(
    ("kwargs", "exception_type"),
    [
        ({"max_payload_bytes": 0}, ValueError),
        ({"max_nesting_depth": -1}, ValueError),
        ({"max_schemas": True}, TypeError),
        ({"max_fields_per_schema": 0}, ValueError),
        ({"max_total_field_nodes": 0}, ValueError),
    ],
)
def test_parsing_limits_require_positive_exact_integers(
    kwargs: dict[str, object],
    exception_type: type[Exception],
) -> None:
    with pytest.raises(exception_type):
        DeclarativeParsingLimits(**kwargs)  # type: ignore[arg-type]
