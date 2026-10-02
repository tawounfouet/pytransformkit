"""Closed declarative TypeDefinition ↔ canonical DataType mapping."""

from __future__ import annotations

from pytransformkit.domain.data import (
    BinaryType,
    BooleanType,
    DataType,
    DateType,
    DecimalType,
    DurationType,
    FloatType,
    IntegerType,
    ListType,
    MapType,
    StringType,
    StructField,
    StructType,
    TimestampType,
    TimeType,
    UnknownType,
)
from pytransformkit.errors import (
    DeclarativeSchemaExportError,
    DeclarativeSchemaTypeError,
)
from pytransformkit.schema_io._model import (
    BinaryTypeDefinition,
    BooleanTypeDefinition,
    DateTypeDefinition,
    DecimalTypeDefinition,
    DurationTypeDefinition,
    FloatTypeDefinition,
    IntegerTypeDefinition,
    ListTypeDefinition,
    MapTypeDefinition,
    StringTypeDefinition,
    StructFieldDefinition,
    StructTypeDefinition,
    TimestampTypeDefinition,
    TimeTypeDefinition,
    TypeDefinition,
    UnknownTypeDefinition,
)

_SUPPORTED_DEFINITION_TYPES = frozenset(
    {
        StringTypeDefinition,
        BooleanTypeDefinition,
        IntegerTypeDefinition,
        FloatTypeDefinition,
        DecimalTypeDefinition,
        BinaryTypeDefinition,
        DateTypeDefinition,
        TimeTypeDefinition,
        TimestampTypeDefinition,
        DurationTypeDefinition,
        UnknownTypeDefinition,
        ListTypeDefinition,
        StructTypeDefinition,
        MapTypeDefinition,
    }
)

_SUPPORTED_DATA_TYPES = frozenset(
    {
        StringType,
        BooleanType,
        IntegerType,
        FloatType,
        DecimalType,
        BinaryType,
        DateType,
        TimeType,
        TimestampType,
        DurationType,
        UnknownType,
        ListType,
        StructType,
        MapType,
    }
)


class DeclarativeTypeResolver:
    """Resolve normalized declarative type definitions into Domain DataTypes."""

    def resolve(self, definition: TypeDefinition) -> DataType:
        """Resolve one definition recursively using the closed V1 mapping."""
        if type(definition) not in _SUPPORTED_DEFINITION_TYPES:
            raise DeclarativeSchemaTypeError(
                message=(
                    "Unsupported declarative TypeDefinition subclass "
                    f"{type(definition).__name__!r}."
                )
            )

        if isinstance(definition, StringTypeDefinition):
            return StringType()
        if isinstance(definition, BooleanTypeDefinition):
            return BooleanType()
        if isinstance(definition, IntegerTypeDefinition):
            return IntegerType(bits=definition.bits, signed=definition.signed)
        if isinstance(definition, FloatTypeDefinition):
            return FloatType(bits=definition.bits)
        if isinstance(definition, DecimalTypeDefinition):
            return DecimalType(
                precision=definition.precision,
                scale=definition.scale,
            )
        if isinstance(definition, BinaryTypeDefinition):
            return BinaryType()
        if isinstance(definition, DateTypeDefinition):
            return DateType()
        if isinstance(definition, TimeTypeDefinition):
            return TimeType(unit=definition.unit)
        if isinstance(definition, TimestampTypeDefinition):
            return TimestampType(
                unit=definition.unit,
                timezone=definition.timezone,
            )
        if isinstance(definition, DurationTypeDefinition):
            return DurationType(unit=definition.unit)
        if isinstance(definition, UnknownTypeDefinition):
            return UnknownType()
        if isinstance(definition, ListTypeDefinition):
            return ListType(
                element_type=self.resolve(definition.element_type),
                element_nullable=definition.element_nullable,
            )
        if isinstance(definition, StructTypeDefinition):
            return StructType(
                fields=tuple(
                    StructField(
                        name=field.name,
                        data_type=self.resolve(field.data_type),
                        nullable=field.nullable,
                    )
                    for field in definition.fields
                )
            )
        if isinstance(definition, MapTypeDefinition):
            return MapType(
                key_type=self.resolve(definition.key_type),
                value_type=self.resolve(definition.value_type),
                value_nullable=definition.value_nullable,
            )

        raise AssertionError("Supported TypeDefinition dispatch is not exhaustive.")


class DeclarativeTypeExporter:
    """Export canonical Domain DataTypes into normalized TypeDefinitions."""

    def export(self, data_type: DataType) -> TypeDefinition:
        """Export one canonical type recursively using the closed V1 mapping."""
        if type(data_type) not in _SUPPORTED_DATA_TYPES:
            raise DeclarativeSchemaExportError(
                "Unsupported canonical DataType subclass "
                f"{type(data_type).__name__!r}."
            )

        if isinstance(data_type, StringType):
            return StringTypeDefinition()
        if isinstance(data_type, BooleanType):
            return BooleanTypeDefinition()
        if isinstance(data_type, IntegerType):
            self._require_bool(data_type.signed, name="IntegerType.signed")
            return IntegerTypeDefinition(
                bits=data_type.bits,
                signed=data_type.signed,
            )
        if isinstance(data_type, FloatType):
            return FloatTypeDefinition(bits=data_type.bits)
        if isinstance(data_type, DecimalType):
            return DecimalTypeDefinition(
                precision=data_type.precision,
                scale=data_type.scale,
            )
        if isinstance(data_type, BinaryType):
            return BinaryTypeDefinition()
        if isinstance(data_type, DateType):
            return DateTypeDefinition()
        if isinstance(data_type, TimeType):
            return TimeTypeDefinition(unit=data_type.unit)
        if isinstance(data_type, TimestampType):
            return TimestampTypeDefinition(
                unit=data_type.unit,
                timezone=data_type.timezone,
            )
        if isinstance(data_type, DurationType):
            return DurationTypeDefinition(unit=data_type.unit)
        if isinstance(data_type, UnknownType):
            return UnknownTypeDefinition()
        if isinstance(data_type, ListType):
            self._require_bool(
                data_type.element_nullable,
                name="ListType.element_nullable",
            )
            return ListTypeDefinition(
                element_type=self.export(data_type.element_type),
                element_nullable=data_type.element_nullable,
            )
        if isinstance(data_type, StructType):
            return StructTypeDefinition(
                fields=tuple(
                    self._export_struct_field(field) for field in data_type.fields
                )
            )
        if isinstance(data_type, MapType):
            self._require_bool(
                data_type.value_nullable,
                name="MapType.value_nullable",
            )
            return MapTypeDefinition(
                key_type=self.export(data_type.key_type),
                value_type=self.export(data_type.value_type),
                value_nullable=data_type.value_nullable,
            )

        raise AssertionError("Supported DataType dispatch is not exhaustive.")

    def _export_struct_field(
        self,
        field: StructField,
    ) -> StructFieldDefinition:
        self._require_bool(field.nullable, name="StructField.nullable")
        return StructFieldDefinition(
            name=field.name,
            data_type=self.export(field.data_type),
            nullable=field.nullable,
        )

    @staticmethod
    def _require_bool(value: object, *, name: str) -> None:
        if type(value) is not bool:
            raise DeclarativeSchemaExportError(
                f"{name} must be a bool for declarative V1 export."
            )
