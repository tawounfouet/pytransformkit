from __future__ import annotations

import pytest

from pytransformkit.domain.data import (
    BinaryType,
    BooleanType,
    DateType,
    DecimalType,
    DurationType,
    Field,
    FloatType,
    IntegerType,
    ListType,
    MapType,
    Schema,
    StringType,
    StructField,
    StructType,
    TimestampType,
    TimeType,
    UnknownType,
)
from pytransformkit.errors import (
    DeclarativeSchemaCardinalityError,
    DeclarativeSchemaDuplicateFieldError,
)
from pytransformkit.schema_io._api import (
    _DeclarativeSchemaLoader,
    _loads_schema,
    _loads_schemas,
)
from pytransformkit.schema_io._compiler import SchemaDocumentCompiler
from pytransformkit.schema_io._model import SchemaDocument

pytest.importorskip("yaml")


def test_yaml_single_schema_compiles_equal_to_direct_python_schema() -> None:
    compiled = _loads_schema(
        """
version: 1
schema:
  name: customers
  fields:
    - name: customer_id
      type: int64
      nullable: false
      description: Stable identifier
    - name: email
      type: string
      nullable: true
"""
    )

    expected = Schema(
        fields=(
            Field(
                name="customer_id",
                data_type=IntegerType(bits=64, signed=True),
                nullable=False,
                description="Stable identifier",
            ),
            Field(
                name="email",
                data_type=StringType(),
                nullable=True,
            ),
        )
    )

    assert compiled == expected


def test_yaml_loading_pipeline_covers_every_canonical_datatype_family() -> None:
    compiled = _loads_schema(
        """
version: 1
schema:
  name: all_types
  fields:
    - name: text
      type: string
    - name: flag
      type: boolean
    - name: signed
      type: int32
    - name: unsigned
      type: uint16
    - name: ratio
      type: float32
    - name: amount
      type:
        decimal:
          precision: 18
          scale: 2
    - name: payload
      type: binary
    - name: business_date
      type: date
    - name: local_time
      type:
        time:
          unit: ns
    - name: occurred_at
      type:
        timestamp:
          unit: ms
          timezone: UTC
    - name: elapsed
      type:
        duration:
          unit: s
    - name: uncertain
      type: unknown
    - name: tags
      type:
        list:
          element:
            type: string
          element_nullable: false
    - name: address
      type:
        struct:
          fields:
            - name: city
              type: string
              nullable: false
    - name: attributes
      type:
        map:
          key:
            type: string
          value:
            type: int64
          value_nullable: false
"""
    )

    assert compiled == Schema(
        fields=(
            Field("text", StringType()),
            Field("flag", BooleanType()),
            Field("signed", IntegerType(bits=32, signed=True)),
            Field("unsigned", IntegerType(bits=16, signed=False)),
            Field("ratio", FloatType(bits=32)),
            Field("amount", DecimalType(precision=18, scale=2)),
            Field("payload", BinaryType()),
            Field("business_date", DateType()),
            Field("local_time", TimeType(unit="ns")),
            Field(
                "occurred_at",
                TimestampType(unit="ms", timezone="UTC"),
            ),
            Field("elapsed", DurationType(unit="s")),
            Field("uncertain", UnknownType()),
            Field(
                "tags",
                ListType(
                    element_type=StringType(),
                    element_nullable=False,
                ),
            ),
            Field(
                "address",
                StructType(
                    fields=(
                        StructField(
                            name="city",
                            data_type=StringType(),
                            nullable=False,
                        ),
                    )
                ),
            ),
            Field(
                "attributes",
                MapType(
                    key_type=StringType(),
                    value_type=IntegerType(),
                    value_nullable=False,
                ),
            ),
        )
    )


def test_multi_schema_loading_preserves_declaration_order() -> None:
    compiled = _loads_schemas(
        """
version: 1
schemas:
  customers:
    fields:
      - name: id
        type: int64
  orders:
    fields:
      - name: id
        type: int64
"""
    )

    assert tuple(compiled) == ("customers", "orders")
    assert compiled["customers"].names() == ("id",)
    assert compiled["orders"].names() == ("id",)


def test_multi_schema_loader_accepts_one_schema_document() -> None:
    compiled = _loads_schemas(
        """
version: 1
schema:
  name: customers
  fields: []
"""
    )

    assert tuple(compiled) == ("customers",)
    assert compiled["customers"] == Schema(fields=())


def test_single_schema_loader_rejects_multi_schema_document() -> None:
    with pytest.raises(DeclarativeSchemaCardinalityError) as error:
        _loads_schema(
            """
version: 1
schemas:
  customers:
    fields: []
  orders:
    fields: []
""",
            source="schemas.yml",
        )

    assert str(error.value.code) == "PTK-DECL-009"
    assert error.value.required_count == 1
    assert error.value.actual_count == 2
    assert error.value.source == "schemas.yml"


class _SpyDocumentCompiler(SchemaDocumentCompiler):
    def __init__(self) -> None:
        super().__init__()
        self.called = False

    def compile(
        self,
        document: SchemaDocument,
        *,
        source: str | None = None,
    ) -> dict[str, Schema]:
        self.called = True
        return super().compile(document, source=source)


def test_multi_schema_pipeline_validates_whole_document_before_compilation() -> None:
    compiler = _SpyDocumentCompiler()
    loader = _DeclarativeSchemaLoader(compiler=compiler)

    with pytest.raises(DeclarativeSchemaDuplicateFieldError) as error:
        loader.loads_schemas(
            """
version: 1
schemas:
  valid:
    fields:
      - name: id
        type: int64
  invalid:
    fields:
      - name: id
        type: int64
      - name: id
        type: string
""",
            source="schemas.yml",
        )

    assert str(error.value.code) == "PTK-DECL-007"
    assert compiler.called is False


def test_loading_is_deterministic_for_equal_input() -> None:
    text = """
version: 1
schema:
  name: customers
  fields:
    - name: id
      type: integer
      nullable: false
"""

    first = _loads_schema(text)
    second = _loads_schema(text)

    assert first == second
