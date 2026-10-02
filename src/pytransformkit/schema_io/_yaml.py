"""Hardened optional YAML adapter for declarative schema V1."""

from __future__ import annotations

import importlib
import math
import re
from dataclasses import dataclass
from typing import Any, NoReturn

from pytransformkit.errors import (
    DeclarativeErrorContext,
    DeclarativeSchemaDependencyError,
    DeclarativeSchemaDuplicateKeyError,
    DeclarativeSchemaError,
    DeclarativeSchemaLimitError,
    DeclarativeSchemaParseError,
    DeclarativeSchemaTypeError,
    DeclarativeSchemaUnknownPropertyError,
    DeclarativeSchemaValidationError,
    DeclarativeSchemaVersionError,
)
from pytransformkit.schema_io._model import (
    BinaryTypeDefinition,
    BooleanTypeDefinition,
    DateTypeDefinition,
    DecimalTypeDefinition,
    DurationTypeDefinition,
    FieldDefinition,
    FloatTypeDefinition,
    IntegerTypeDefinition,
    ListTypeDefinition,
    MapTypeDefinition,
    SchemaDefinition,
    SchemaDocument,
    StringTypeDefinition,
    StructFieldDefinition,
    StructTypeDefinition,
    TimestampTypeDefinition,
    TimeTypeDefinition,
    TypeDefinition,
    UnknownTypeDefinition,
)

DEFAULT_MAX_DECLARATIVE_PAYLOAD_BYTES = 1_048_576
DEFAULT_MAX_DECLARATIVE_NESTING_DEPTH = 64
DEFAULT_MAX_DECLARATIVE_SCHEMAS = 256
DEFAULT_MAX_DECLARATIVE_FIELDS_PER_SCHEMA = 10_000
DEFAULT_MAX_DECLARATIVE_FIELD_NODES = 50_000

_TIME_UNITS = frozenset({"s", "ms", "us", "ns"})
_SIMPLE_TYPE_NAMES = (
    "string",
    "boolean",
    "int8",
    "int16",
    "int32",
    "int64",
    "uint8",
    "uint16",
    "uint32",
    "uint64",
    "integer",
    "float32",
    "float64",
    "float",
    "binary",
    "date",
    "time",
    "timestamp",
    "duration",
    "unknown",
)
_STRUCTURED_TYPE_NAMES = (
    "decimal",
    "time",
    "timestamp",
    "duration",
    "list",
    "struct",
    "map",
)
_ALL_TYPE_NAMES = tuple(dict.fromkeys((*_SIMPLE_TYPE_NAMES, *_STRUCTURED_TYPE_NAMES)))

_BOOL_PATTERN = re.compile(r"^(?:true|True|TRUE|false|False|FALSE)$")
_INT_PATTERN = re.compile(r"^[-+]?(?:0|[1-9][0-9]*)$")
_FLOAT_PATTERN = re.compile(
    r"^[-+]?(?:(?:[0-9]+\.[0-9]*|\.[0-9]+)"
    r"(?:[eE][-+]?[0-9]+)?|[0-9]+[eE][-+]?[0-9]+)$"
)
_NULL_PATTERN = re.compile(r"^(?:~|null|Null|NULL|)$")
_NON_FINITE_SPELLINGS = frozenset(
    {
        ".nan",
        ".inf",
        "+.inf",
        "-.inf",
        "nan",
        "+nan",
        "-nan",
        "infinity",
        "+infinity",
        "-infinity",
    }
)
_MISSING = object()


@dataclass(frozen=True, slots=True)
class DeclarativeParsingLimits:
    """Internal defensive limits for untrusted declarative YAML."""

    max_payload_bytes: int = DEFAULT_MAX_DECLARATIVE_PAYLOAD_BYTES
    max_nesting_depth: int = DEFAULT_MAX_DECLARATIVE_NESTING_DEPTH
    max_schemas: int = DEFAULT_MAX_DECLARATIVE_SCHEMAS
    max_fields_per_schema: int = DEFAULT_MAX_DECLARATIVE_FIELDS_PER_SCHEMA
    max_total_field_nodes: int = DEFAULT_MAX_DECLARATIVE_FIELD_NODES

    def __post_init__(self) -> None:
        for name, value in (
            ("max_payload_bytes", self.max_payload_bytes),
            ("max_nesting_depth", self.max_nesting_depth),
            ("max_schemas", self.max_schemas),
            ("max_fields_per_schema", self.max_fields_per_schema),
            ("max_total_field_nodes", self.max_total_field_nodes),
        ):
            if type(value) is not int:
                raise TypeError(f"{name} must be an int.")
            if value <= 0:
                raise ValueError(f"{name} must be greater than zero.")


@dataclass(slots=True)
class _SourceMarks:
    mapping_starts: dict[int, tuple[int, int]]
    key_marks: dict[int, dict[object, tuple[int, int]]]
    value_marks: dict[int, dict[object, tuple[int, int]]]
    sequence_starts: dict[int, tuple[int, int]]
    item_marks: dict[int, list[tuple[int, int]]]


class DeclarativeSafeLoader:
    """Factory for a PyTransformKit-owned, loader-local SafeLoader subclass."""

    @staticmethod
    def build(yaml_module: Any) -> Any:
        loader_type = type(
            "DeclarativeSafeLoader",
            (yaml_module.SafeLoader,),
            {},
        )

        loader_type.yaml_implicit_resolvers = {
            initial: list(resolvers)
            for initial, resolvers in (
                yaml_module.SafeLoader.yaml_implicit_resolvers.items()
            )
        }

        removed_tags = {
            "tag:yaml.org,2002:bool",
            "tag:yaml.org,2002:int",
            "tag:yaml.org,2002:float",
            "tag:yaml.org,2002:null",
            "tag:yaml.org,2002:timestamp",
        }
        for initial, resolvers in tuple(loader_type.yaml_implicit_resolvers.items()):
            loader_type.yaml_implicit_resolvers[initial] = [
                (tag, pattern) for tag, pattern in resolvers if tag not in removed_tags
            ]

        loader_type.add_implicit_resolver(
            "tag:yaml.org,2002:bool",
            _BOOL_PATTERN,
            list("tTfF"),
        )
        loader_type.add_implicit_resolver(
            "tag:yaml.org,2002:int",
            _INT_PATTERN,
            list("-+0123456789"),
        )
        loader_type.add_implicit_resolver(
            "tag:yaml.org,2002:float",
            _FLOAT_PATTERN,
            list("-+0123456789."),
        )
        loader_type.add_implicit_resolver(
            "tag:yaml.org,2002:null",
            _NULL_PATTERN,
            ["~", "n", "N", None],
        )

        default_mapping_tag = yaml_module.resolver.BaseResolver.DEFAULT_MAPPING_TAG
        default_sequence_tag = yaml_module.resolver.BaseResolver.DEFAULT_SEQUENCE_TAG

        def construct_mapping(
            loader: Any,
            node: Any,
            deep: bool = False,
        ) -> dict[object, object]:
            if not isinstance(node, yaml_module.nodes.MappingNode):
                raise DeclarativeSchemaParseError(
                    "Expected a YAML mapping node.",
                    context=_context_from_mark(
                        getattr(loader, "_ptk_source", None),
                        node.start_mark,
                    ),
                )

            mapping: dict[object, object] = {}
            key_marks: dict[object, tuple[int, int]] = {}
            value_marks: dict[object, tuple[int, int]] = {}
            loader._ptk_mapping_starts[id(mapping)] = _position(node.start_mark)

            for key_node, value_node in node.value:
                if key_node.tag == "tag:yaml.org,2002:merge":
                    raise DeclarativeSchemaParseError(
                        "YAML merge keys are forbidden.",
                        context=_context_from_mark(
                            getattr(loader, "_ptk_source", None),
                            key_node.start_mark,
                        ),
                    )

                key = loader.construct_object(key_node, deep=deep)
                try:
                    hash(key)
                except TypeError as exc:
                    raise DeclarativeSchemaParseError(
                        "YAML mapping keys must be hashable scalars.",
                        context=_context_from_mark(
                            getattr(loader, "_ptk_source", None),
                            key_node.start_mark,
                        ),
                    ) from exc

                if key in mapping:
                    first_line, first_column = key_marks[key]
                    raise DeclarativeSchemaDuplicateKeyError(
                        _bounded_key(key),
                        context=_context_from_mark(
                            getattr(loader, "_ptk_source", None),
                            key_node.start_mark,
                        ),
                        first_context=DeclarativeErrorContext(
                            source=getattr(loader, "_ptk_source", None),
                            line=first_line,
                            column=first_column,
                        ),
                    )

                mapping[key] = loader.construct_object(value_node, deep=deep)
                key_marks[key] = _position(key_node.start_mark)
                value_marks[key] = _position(value_node.start_mark)

            loader._ptk_key_marks[id(mapping)] = key_marks
            loader._ptk_value_marks[id(mapping)] = value_marks
            return mapping

        def construct_sequence(
            loader: Any,
            node: Any,
            deep: bool = False,
        ) -> list[object]:
            if not isinstance(node, yaml_module.nodes.SequenceNode):
                raise DeclarativeSchemaParseError(
                    "Expected a YAML sequence node.",
                    context=_context_from_mark(
                        getattr(loader, "_ptk_source", None),
                        node.start_mark,
                    ),
                )

            values = [loader.construct_object(child, deep=deep) for child in node.value]
            loader._ptk_sequence_starts[id(values)] = _position(node.start_mark)
            loader._ptk_item_marks[id(values)] = [
                _position(child.start_mark) for child in node.value
            ]
            return values

        loader_type.add_constructor(default_mapping_tag, construct_mapping)
        loader_type.add_constructor(default_sequence_tag, construct_sequence)
        return loader_type


class YamlSchemaParser:
    """Parse untrusted YAML into a normalized SchemaDocument."""

    def __init__(
        self,
        limits: DeclarativeParsingLimits | None = None,
    ) -> None:
        self._limits = limits or DeclarativeParsingLimits()

    def parse(
        self,
        text: str | bytes,
        *,
        source: str | None = None,
    ) -> SchemaDocument:
        """Parse exactly one hardened declarative YAML document."""
        normalized_text, payload_bytes = self._normalize_input(text, source=source)
        if payload_bytes > self._limits.max_payload_bytes:
            raise DeclarativeSchemaLimitError(
                "payload_bytes",
                self._limits.max_payload_bytes,
                payload_bytes,
                context=DeclarativeErrorContext(source=source, object_path="$"),
            )

        yaml_module = _load_yaml_module()
        loader_type = DeclarativeSafeLoader.build(yaml_module)

        self._preflight(
            yaml_module,
            loader_type,
            normalized_text,
            source=source,
        )
        value, marks = self._construct_plain_values(
            yaml_module,
            loader_type,
            normalized_text,
            source=source,
        )
        self._audit_plain_values(value, source=source)

        decoder = _DeclarativeDecoder(
            source=source,
            marks=marks,
            limits=self._limits,
        )
        return decoder.decode(value)

    def _normalize_input(
        self,
        text: str | bytes,
        *,
        source: str | None,
    ) -> tuple[str, int]:
        if isinstance(text, bytes):
            payload_bytes = len(text)
            try:
                return text.decode("utf-8-sig"), payload_bytes
            except UnicodeDecodeError as exc:
                raise DeclarativeSchemaParseError(
                    "Declarative YAML must be valid UTF-8.",
                    context=DeclarativeErrorContext(source=source, object_path="$"),
                ) from exc

        if not isinstance(text, str):
            raise TypeError("text must be str or bytes.")

        try:
            encoded = text.encode("utf-8")
        except UnicodeEncodeError as exc:
            raise DeclarativeSchemaParseError(
                "Declarative YAML text must be UTF-8 encodable.",
                context=DeclarativeErrorContext(source=source, object_path="$"),
            ) from exc

        normalized = text[1:] if text.startswith("\ufeff") else text
        return normalized, len(encoded)

    def _preflight(
        self,
        yaml_module: Any,
        loader_type: Any,
        text: str,
        *,
        source: str | None,
    ) -> None:
        try:
            for token in yaml_module.scan(text, Loader=loader_type):
                if isinstance(token, yaml_module.tokens.AnchorToken):
                    self._parse_error(
                        "YAML anchors are forbidden.",
                        source=source,
                        mark=token.start_mark,
                    )
                if isinstance(token, yaml_module.tokens.AliasToken):
                    self._parse_error(
                        "YAML aliases are forbidden.",
                        source=source,
                        mark=token.start_mark,
                    )
                if isinstance(token, yaml_module.tokens.TagToken):
                    self._parse_error(
                        "Explicit YAML tags are forbidden.",
                        source=source,
                        mark=token.start_mark,
                    )
                if (
                    isinstance(token, yaml_module.tokens.ScalarToken)
                    and token.style is None
                    and token.value.lower() in _NON_FINITE_SPELLINGS
                ):
                    self._parse_error(
                        "Non-finite YAML numeric values are forbidden.",
                        source=source,
                        mark=token.start_mark,
                    )

            document_count = sum(
                isinstance(event, yaml_module.events.DocumentStartEvent)
                for event in yaml_module.parse(text, Loader=loader_type)
            )
            if document_count != 1:
                raise DeclarativeSchemaParseError(
                    "Exactly one YAML document is required.",
                    context=DeclarativeErrorContext(source=source, object_path="$"),
                )
        except DeclarativeSchemaError:
            raise
        except yaml_module.YAMLError as exc:
            raise DeclarativeSchemaParseError(
                "Malformed or unsupported YAML input.",
                context=_context_from_mark(
                    source,
                    getattr(exc, "problem_mark", None),
                    object_path="$",
                ),
            ) from exc

    def _construct_plain_values(
        self,
        yaml_module: Any,
        loader_type: Any,
        text: str,
        *,
        source: str | None,
    ) -> tuple[object, _SourceMarks]:
        loader = loader_type(text)
        loader._ptk_source = source
        loader._ptk_mapping_starts = {}
        loader._ptk_key_marks = {}
        loader._ptk_value_marks = {}
        loader._ptk_sequence_starts = {}
        loader._ptk_item_marks = {}

        try:
            value = loader.get_single_data()
            marks = _SourceMarks(
                mapping_starts=loader._ptk_mapping_starts,
                key_marks=loader._ptk_key_marks,
                value_marks=loader._ptk_value_marks,
                sequence_starts=loader._ptk_sequence_starts,
                item_marks=loader._ptk_item_marks,
            )
            return value, marks
        except DeclarativeSchemaError:
            raise
        except yaml_module.YAMLError as exc:
            raise DeclarativeSchemaParseError(
                "Malformed or unsupported YAML input.",
                context=_context_from_mark(
                    source,
                    getattr(exc, "problem_mark", None),
                    object_path="$",
                ),
            ) from exc
        finally:
            loader.dispose()

    def _audit_plain_values(
        self,
        root: object,
        *,
        source: str | None,
    ) -> None:
        stack: list[tuple[object, int]] = [(root, 1)]
        seen_containers: set[int] = set()

        while stack:
            value, depth = stack.pop()

            if type(value) is dict:
                container_id = id(value)
                if container_id in seen_containers:
                    raise DeclarativeSchemaParseError(
                        "Cyclic or aliased YAML value graphs are forbidden.",
                        context=DeclarativeErrorContext(
                            source=source,
                            object_path="$",
                        ),
                    )
                seen_containers.add(container_id)

                if depth > self._limits.max_nesting_depth:
                    raise DeclarativeSchemaLimitError(
                        "nesting_depth",
                        self._limits.max_nesting_depth,
                        depth,
                        context=DeclarativeErrorContext(
                            source=source,
                            object_path="$",
                        ),
                    )

                for key, child in value.items():
                    self._audit_scalar_or_container(key, source=source)
                    child_depth = depth + 1 if type(child) in (dict, list) else depth
                    stack.append((child, child_depth))
                continue

            if type(value) is list:
                container_id = id(value)
                if container_id in seen_containers:
                    raise DeclarativeSchemaParseError(
                        "Cyclic or aliased YAML value graphs are forbidden.",
                        context=DeclarativeErrorContext(
                            source=source,
                            object_path="$",
                        ),
                    )
                seen_containers.add(container_id)

                if depth > self._limits.max_nesting_depth:
                    raise DeclarativeSchemaLimitError(
                        "nesting_depth",
                        self._limits.max_nesting_depth,
                        depth,
                        context=DeclarativeErrorContext(
                            source=source,
                            object_path="$",
                        ),
                    )

                for child in value:
                    child_depth = depth + 1 if type(child) in (dict, list) else depth
                    stack.append((child, child_depth))
                continue

            self._audit_scalar_or_container(value, source=source)

    @staticmethod
    def _audit_scalar_or_container(
        value: object,
        *,
        source: str | None,
    ) -> None:
        if type(value) in (dict, list):
            return
        if type(value) not in (str, int, float, bool, type(None)):
            raise DeclarativeSchemaParseError(
                f"Unsupported YAML value type {type(value).__name__!r}.",
                context=DeclarativeErrorContext(source=source, object_path="$"),
            )
        if type(value) is float and not math.isfinite(value):
            raise DeclarativeSchemaParseError(
                "Non-finite YAML numeric values are forbidden.",
                context=DeclarativeErrorContext(source=source, object_path="$"),
            )

    @staticmethod
    def _parse_error(
        message: str,
        *,
        source: str | None,
        mark: Any,
    ) -> NoReturn:
        raise DeclarativeSchemaParseError(
            message,
            context=_context_from_mark(source, mark, object_path="$"),
        )


class _DeclarativeDecoder:
    def __init__(
        self,
        *,
        source: str | None,
        marks: _SourceMarks,
        limits: DeclarativeParsingLimits,
    ) -> None:
        self._source = source
        self._marks = marks
        self._limits = limits
        self._field_nodes = 0

    def decode(self, root: object) -> SchemaDocument:
        mapping = self._require_mapping(root, path="$")
        self._require_string_keys(mapping, path="$")

        if "version" not in mapping:
            raise DeclarativeSchemaVersionError(
                None,
                supported_versions=(1,),
                context=self._context(path="version"),
            )
        version = mapping["version"]
        if type(version) is not int or version != 1:
            raise DeclarativeSchemaVersionError(
                version,
                supported_versions=(1,),
                context=self._context(
                    path="version",
                    mapping=mapping,
                    key="version",
                    value=True,
                ),
            )

        self._reject_unknown(
            mapping,
            allowed=("version", "schema", "schemas"),
            path="$",
        )

        has_schema = "schema" in mapping
        has_schemas = "schemas" in mapping
        if has_schema == has_schemas:
            raise DeclarativeSchemaValidationError(
                "Exactly one of 'schema' or 'schemas' is required.",
                context=self._context(path="$"),
            )

        if has_schema:
            if self._limits.max_schemas < 1:
                raise AssertionError("Positive parsing limits are required.")
            schema = self._decode_schema(
                mapping["schema"],
                path="schema",
                multi_schema_name=None,
            )
            return SchemaDocument(version=1, schemas=(schema,))

        schemas_mapping = self._require_mapping(
            mapping["schemas"],
            path="schemas",
            parent=mapping,
            parent_key="schemas",
        )
        self._require_string_keys(schemas_mapping, path="schemas")
        if len(schemas_mapping) > self._limits.max_schemas:
            raise DeclarativeSchemaLimitError(
                "schemas",
                self._limits.max_schemas,
                len(schemas_mapping),
                context=self._context(
                    path="schemas",
                    mapping=mapping,
                    key="schemas",
                    value=True,
                ),
            )

        schemas: list[SchemaDefinition] = []
        for schema_name, schema_body in schemas_mapping.items():
            if not isinstance(schema_name, str):
                raise AssertionError("String-key validation must run first.")
            self._require_non_blank_string(
                schema_name,
                path=f"schemas.{schema_name}",
                mapping=schemas_mapping,
                key=schema_name,
                use_value_mark=False,
                label="Schema name",
            )
            schemas.append(
                self._decode_schema(
                    schema_body,
                    path=f"schemas.{schema_name}",
                    multi_schema_name=schema_name,
                )
            )

        return SchemaDocument(version=1, schemas=tuple(schemas))

    def _decode_schema(
        self,
        value: object,
        *,
        path: str,
        multi_schema_name: str | None,
    ) -> SchemaDefinition:
        mapping = self._require_mapping(value, path=path)
        self._require_string_keys(mapping, path=path)

        if multi_schema_name is None:
            self._reject_unknown(
                mapping,
                allowed=("name", "fields"),
                path=path,
            )
            self._require_key(mapping, "name", path=path)
            name = self._require_non_blank_string(
                mapping["name"],
                path=f"{path}.name",
                mapping=mapping,
                key="name",
                use_value_mark=True,
                label="Schema name",
            )
        else:
            self._reject_unknown(
                mapping,
                allowed=("fields",),
                path=path,
            )
            name = multi_schema_name

        self._require_key(mapping, "fields", path=path)
        fields_value = mapping["fields"]
        fields = self._require_sequence(
            fields_value,
            path=f"{path}.fields",
            parent=mapping,
            parent_key="fields",
        )
        if len(fields) > self._limits.max_fields_per_schema:
            raise DeclarativeSchemaLimitError(
                "fields_per_schema",
                self._limits.max_fields_per_schema,
                len(fields),
                context=self._context(
                    path=f"{path}.fields",
                    mapping=mapping,
                    key="fields",
                    value=True,
                ),
            )

        decoded_fields = tuple(
            self._decode_field(
                field,
                path=f"{path}.fields[{index}]",
                sequence=fields,
                index=index,
            )
            for index, field in enumerate(fields)
        )
        return SchemaDefinition(name=name, fields=decoded_fields)

    def _decode_field(
        self,
        value: object,
        *,
        path: str,
        sequence: list[object],
        index: int,
    ) -> FieldDefinition:
        self._count_field_node(path=path, sequence=sequence, index=index)
        mapping = self._require_mapping(
            value,
            path=path,
            sequence=sequence,
            index=index,
        )
        self._require_string_keys(mapping, path=path)
        self._reject_unknown(
            mapping,
            allowed=("name", "type", "nullable", "description"),
            path=path,
        )
        self._require_key(mapping, "name", path=path)
        self._require_key(mapping, "type", path=path)

        name = self._require_non_blank_string(
            mapping["name"],
            path=f"{path}.name",
            mapping=mapping,
            key="name",
            use_value_mark=True,
            label="Field name",
        )
        nullable = self._decode_bool_property(
            mapping,
            "nullable",
            path=f"{path}.nullable",
            default=True,
            type_error=False,
        )

        description: str | None = None
        if "description" in mapping:
            description = self._require_non_blank_string(
                mapping["description"],
                path=f"{path}.description",
                mapping=mapping,
                key="description",
                use_value_mark=True,
                label="Field description",
            )

        data_type = self._decode_type(
            mapping["type"],
            path=f"{path}.type",
            parent=mapping,
            parent_key="type",
        )
        return FieldDefinition(
            name=name,
            data_type=data_type,
            nullable=nullable,
            description=description,
        )

    def _decode_struct_field(
        self,
        value: object,
        *,
        path: str,
        sequence: list[object],
        index: int,
    ) -> StructFieldDefinition:
        self._count_field_node(path=path, sequence=sequence, index=index)
        mapping = self._require_mapping(
            value,
            path=path,
            sequence=sequence,
            index=index,
            type_error=True,
        )
        self._require_string_keys(mapping, path=path, type_error=True)
        self._reject_unknown(
            mapping,
            allowed=("name", "type", "nullable"),
            path=path,
        )
        self._require_key(mapping, "name", path=path, type_error=True)
        self._require_key(mapping, "type", path=path, type_error=True)

        name = self._require_non_blank_string(
            mapping["name"],
            path=f"{path}.name",
            mapping=mapping,
            key="name",
            use_value_mark=True,
            label="Struct field name",
            type_error=True,
        )
        nullable = self._decode_bool_property(
            mapping,
            "nullable",
            path=f"{path}.nullable",
            default=True,
            type_error=True,
        )
        data_type = self._decode_type(
            mapping["type"],
            path=f"{path}.type",
            parent=mapping,
            parent_key="type",
        )
        return StructFieldDefinition(
            name=name,
            data_type=data_type,
            nullable=nullable,
        )

    def _decode_type(
        self,
        value: object,
        *,
        path: str,
        parent: dict[object, object] | None = None,
        parent_key: object | None = None,
    ) -> TypeDefinition:
        if isinstance(value, str):
            return self._decode_simple_type(
                value,
                path=path,
                parent=parent,
                key=parent_key,
            )

        if type(value) is not dict:
            self._raise_type_error(
                "Type declaration must be a string or single-key mapping.",
                path=path,
                mapping=parent,
                key=parent_key,
            )

        mapping = value
        self._require_string_keys(mapping, path=path, type_error=True)
        if len(mapping) != 1:
            self._raise_type_error(
                "Structured type declarations must contain exactly one discriminator.",
                path=path,
                mapping=mapping,
            )

        discriminator = next(iter(mapping))
        if not isinstance(discriminator, str):
            raise AssertionError("String-key validation must run first.")
        body = mapping[discriminator]
        if discriminator not in _STRUCTURED_TYPE_NAMES:
            raise DeclarativeSchemaTypeError(
                discriminator,
                expected_type_names=_ALL_TYPE_NAMES,
                context=self._context(
                    path=path,
                    mapping=mapping,
                    key=discriminator,
                    value=False,
                ),
            )

        body_path = f"{path}.{discriminator}"
        if discriminator == "decimal":
            return self._decode_decimal(
                body,
                path=body_path,
                parent=mapping,
                key=discriminator,
            )
        if discriminator == "time":
            return TimeTypeDefinition(
                unit=self._decode_temporal_body(
                    body,
                    path=body_path,
                    parent=mapping,
                    key=discriminator,
                )
            )
        if discriminator == "timestamp":
            return self._decode_timestamp(
                body,
                path=body_path,
                parent=mapping,
                key=discriminator,
            )
        if discriminator == "duration":
            return DurationTypeDefinition(
                unit=self._decode_temporal_body(
                    body,
                    path=body_path,
                    parent=mapping,
                    key=discriminator,
                )
            )
        if discriminator == "list":
            return self._decode_list(
                body,
                path=body_path,
                parent=mapping,
                key=discriminator,
            )
        if discriminator == "struct":
            return self._decode_struct(
                body,
                path=body_path,
                parent=mapping,
                key=discriminator,
            )
        if discriminator == "map":
            return self._decode_map(
                body,
                path=body_path,
                parent=mapping,
                key=discriminator,
            )

        raise AssertionError("Structured type dispatch is not exhaustive.")

    def _decode_simple_type(
        self,
        name: str,
        *,
        path: str,
        parent: dict[object, object] | None,
        key: object | None,
    ) -> TypeDefinition:
        if name == "string":
            return StringTypeDefinition()
        if name == "boolean":
            return BooleanTypeDefinition()
        if name in {"int8", "int16", "int32", "int64"}:
            return IntegerTypeDefinition(bits=int(name[3:]), signed=True)
        if name in {"uint8", "uint16", "uint32", "uint64"}:
            return IntegerTypeDefinition(bits=int(name[4:]), signed=False)
        if name == "integer":
            return IntegerTypeDefinition()
        if name == "float32":
            return FloatTypeDefinition(bits=32)
        if name in {"float64", "float"}:
            return FloatTypeDefinition(bits=64)
        if name == "binary":
            return BinaryTypeDefinition()
        if name == "date":
            return DateTypeDefinition()
        if name == "time":
            return TimeTypeDefinition()
        if name == "timestamp":
            return TimestampTypeDefinition()
        if name == "duration":
            return DurationTypeDefinition()
        if name == "unknown":
            return UnknownTypeDefinition()

        raise DeclarativeSchemaTypeError(
            name,
            expected_type_names=_ALL_TYPE_NAMES,
            context=self._context(
                path=path,
                mapping=parent,
                key=key,
                value=True,
            ),
        )

    def _decode_decimal(
        self,
        value: object,
        *,
        path: str,
        parent: dict[object, object],
        key: object,
    ) -> DecimalTypeDefinition:
        mapping = self._require_mapping(
            value,
            path=path,
            parent=parent,
            parent_key=key,
            type_error=True,
        )
        self._require_string_keys(mapping, path=path, type_error=True)
        self._reject_unknown(mapping, allowed=("precision", "scale"), path=path)
        self._require_key(mapping, "precision", path=path, type_error=True)
        self._require_key(mapping, "scale", path=path, type_error=True)

        precision = self._require_int(
            mapping["precision"],
            path=f"{path}.precision",
            mapping=mapping,
            key="precision",
        )
        scale = self._require_int(
            mapping["scale"],
            path=f"{path}.scale",
            mapping=mapping,
            key="scale",
        )
        if precision <= 0:
            self._raise_type_error(
                "Decimal precision must be greater than zero.",
                path=f"{path}.precision",
                mapping=mapping,
                key="precision",
            )
        if scale < 0:
            self._raise_type_error(
                "Decimal scale must be non-negative.",
                path=f"{path}.scale",
                mapping=mapping,
                key="scale",
            )
        if scale > precision:
            self._raise_type_error(
                "Decimal scale must not exceed precision.",
                path=f"{path}.scale",
                mapping=mapping,
                key="scale",
            )
        return DecimalTypeDefinition(precision=precision, scale=scale)

    def _decode_temporal_body(
        self,
        value: object,
        *,
        path: str,
        parent: dict[object, object],
        key: object,
    ) -> str:
        mapping = self._require_mapping(
            value,
            path=path,
            parent=parent,
            parent_key=key,
            type_error=True,
        )
        self._require_string_keys(mapping, path=path, type_error=True)
        self._reject_unknown(mapping, allowed=("unit",), path=path)
        self._require_key(mapping, "unit", path=path, type_error=True)
        return self._require_time_unit(
            mapping["unit"],
            path=f"{path}.unit",
            mapping=mapping,
            key="unit",
        )

    def _decode_timestamp(
        self,
        value: object,
        *,
        path: str,
        parent: dict[object, object],
        key: object,
    ) -> TimestampTypeDefinition:
        mapping = self._require_mapping(
            value,
            path=path,
            parent=parent,
            parent_key=key,
            type_error=True,
        )
        self._require_string_keys(mapping, path=path, type_error=True)
        self._reject_unknown(mapping, allowed=("unit", "timezone"), path=path)
        self._require_key(mapping, "unit", path=path, type_error=True)

        unit = self._require_time_unit(
            mapping["unit"],
            path=f"{path}.unit",
            mapping=mapping,
            key="unit",
        )
        timezone: str | None = None
        if "timezone" in mapping:
            timezone = self._require_non_blank_string(
                mapping["timezone"],
                path=f"{path}.timezone",
                mapping=mapping,
                key="timezone",
                use_value_mark=True,
                label="Timestamp timezone",
                type_error=True,
            )
        return TimestampTypeDefinition(unit=unit, timezone=timezone)

    def _decode_list(
        self,
        value: object,
        *,
        path: str,
        parent: dict[object, object],
        key: object,
    ) -> ListTypeDefinition:
        mapping = self._require_mapping(
            value,
            path=path,
            parent=parent,
            parent_key=key,
            type_error=True,
        )
        self._require_string_keys(mapping, path=path, type_error=True)
        self._reject_unknown(
            mapping,
            allowed=("element", "element_nullable"),
            path=path,
        )
        self._require_key(mapping, "element", path=path, type_error=True)

        element_type = self._decode_type_holder(
            mapping["element"],
            path=f"{path}.element",
            parent=mapping,
            parent_key="element",
        )
        element_nullable = self._decode_bool_property(
            mapping,
            "element_nullable",
            path=f"{path}.element_nullable",
            default=True,
            type_error=True,
        )
        return ListTypeDefinition(
            element_type=element_type,
            element_nullable=element_nullable,
        )

    def _decode_struct(
        self,
        value: object,
        *,
        path: str,
        parent: dict[object, object],
        key: object,
    ) -> StructTypeDefinition:
        mapping = self._require_mapping(
            value,
            path=path,
            parent=parent,
            parent_key=key,
            type_error=True,
        )
        self._require_string_keys(mapping, path=path, type_error=True)
        self._reject_unknown(mapping, allowed=("fields",), path=path)
        self._require_key(mapping, "fields", path=path, type_error=True)

        fields = self._require_sequence(
            mapping["fields"],
            path=f"{path}.fields",
            parent=mapping,
            parent_key="fields",
            type_error=True,
        )
        return StructTypeDefinition(
            fields=tuple(
                self._decode_struct_field(
                    field,
                    path=f"{path}.fields[{index}]",
                    sequence=fields,
                    index=index,
                )
                for index, field in enumerate(fields)
            )
        )

    def _decode_map(
        self,
        value: object,
        *,
        path: str,
        parent: dict[object, object],
        key: object,
    ) -> MapTypeDefinition:
        mapping = self._require_mapping(
            value,
            path=path,
            parent=parent,
            parent_key=key,
            type_error=True,
        )
        self._require_string_keys(mapping, path=path, type_error=True)
        self._reject_unknown(
            mapping,
            allowed=("key", "value", "value_nullable"),
            path=path,
        )
        self._require_key(mapping, "key", path=path, type_error=True)
        self._require_key(mapping, "value", path=path, type_error=True)

        key_type = self._decode_type_holder(
            mapping["key"],
            path=f"{path}.key",
            parent=mapping,
            parent_key="key",
        )
        value_type = self._decode_type_holder(
            mapping["value"],
            path=f"{path}.value",
            parent=mapping,
            parent_key="value",
        )
        value_nullable = self._decode_bool_property(
            mapping,
            "value_nullable",
            path=f"{path}.value_nullable",
            default=True,
            type_error=True,
        )
        return MapTypeDefinition(
            key_type=key_type,
            value_type=value_type,
            value_nullable=value_nullable,
        )

    def _decode_type_holder(
        self,
        value: object,
        *,
        path: str,
        parent: dict[object, object],
        parent_key: object,
    ) -> TypeDefinition:
        mapping = self._require_mapping(
            value,
            path=path,
            parent=parent,
            parent_key=parent_key,
            type_error=True,
        )
        self._require_string_keys(mapping, path=path, type_error=True)
        self._reject_unknown(mapping, allowed=("type",), path=path)
        self._require_key(mapping, "type", path=path, type_error=True)
        return self._decode_type(
            mapping["type"],
            path=f"{path}.type",
            parent=mapping,
            parent_key="type",
        )

    def _decode_bool_property(
        self,
        mapping: dict[object, object],
        key: str,
        *,
        path: str,
        default: bool,
        type_error: bool,
    ) -> bool:
        value = mapping.get(key, _MISSING)
        if value is _MISSING:
            return default
        if type(value) is not bool:
            if type_error:
                self._raise_type_error(
                    f"{key} must be a boolean.",
                    path=path,
                    mapping=mapping,
                    key=key,
                )
            raise DeclarativeSchemaValidationError(
                f"{key} must be a boolean.",
                context=self._context(
                    path=path,
                    mapping=mapping,
                    key=key,
                    value=True,
                ),
            )
        return value

    def _require_time_unit(
        self,
        value: object,
        *,
        path: str,
        mapping: dict[object, object],
        key: object,
    ) -> str:
        if not isinstance(value, str) or value not in _TIME_UNITS:
            self._raise_type_error(
                f"Temporal unit must be one of {sorted(_TIME_UNITS)!r}.",
                path=path,
                mapping=mapping,
                key=key,
            )
        return value

    def _require_int(
        self,
        value: object,
        *,
        path: str,
        mapping: dict[object, object],
        key: object,
    ) -> int:
        if type(value) is not int:
            self._raise_type_error(
                "Expected an integer.",
                path=path,
                mapping=mapping,
                key=key,
            )
        return value

    def _require_non_blank_string(
        self,
        raw_value: object,
        *,
        path: str,
        mapping: dict[object, object],
        key: object,
        use_value_mark: bool,
        label: str,
        type_error: bool = False,
    ) -> str:
        if not isinstance(raw_value, str) or not raw_value.strip():
            message = f"{label} must be a non-empty string."
            if type_error:
                self._raise_type_error(
                    message,
                    path=path,
                    mapping=mapping,
                    key=key,
                )
            raise DeclarativeSchemaValidationError(
                message,
                context=self._context(
                    path=path,
                    mapping=mapping,
                    key=key,
                    value=use_value_mark,
                ),
            )
        return raw_value

    def _require_mapping(
        self,
        value: object,
        *,
        path: str,
        parent: dict[object, object] | None = None,
        parent_key: object | None = None,
        sequence: list[object] | None = None,
        index: int | None = None,
        type_error: bool = False,
    ) -> dict[object, object]:
        if type(value) is dict:
            return value

        message = "Expected a mapping."
        if type_error:
            self._raise_type_error(
                message,
                path=path,
                mapping=parent,
                key=parent_key,
                sequence=sequence,
                index=index,
            )
        raise DeclarativeSchemaValidationError(
            message,
            context=self._context(
                path=path,
                mapping=parent,
                key=parent_key,
                value=True,
                sequence=sequence,
                index=index,
            ),
        )

    def _require_sequence(
        self,
        value: object,
        *,
        path: str,
        parent: dict[object, object] | None = None,
        parent_key: object | None = None,
        type_error: bool = False,
    ) -> list[object]:
        if type(value) is list:
            return value

        message = "Expected a sequence."
        if type_error:
            self._raise_type_error(
                message,
                path=path,
                mapping=parent,
                key=parent_key,
            )
        raise DeclarativeSchemaValidationError(
            message,
            context=self._context(
                path=path,
                mapping=parent,
                key=parent_key,
                value=True,
            ),
        )

    def _require_string_keys(
        self,
        mapping: dict[object, object],
        *,
        path: str,
        type_error: bool = False,
    ) -> None:
        for key in mapping:
            if isinstance(key, str):
                continue
            message = "Declarative mapping keys must be strings."
            if type_error:
                self._raise_type_error(
                    message,
                    path=path,
                    mapping=mapping,
                    key=key,
                )
            raise DeclarativeSchemaValidationError(
                message,
                context=self._context(
                    path=path,
                    mapping=mapping,
                    key=key,
                    value=False,
                ),
            )

    def _reject_unknown(
        self,
        mapping: dict[object, object],
        *,
        allowed: tuple[str, ...],
        path: str,
    ) -> None:
        allowed_set = set(allowed)
        for key in mapping:
            if not isinstance(key, str):
                continue
            if key in allowed_set:
                continue
            property_path = f"{path}.{key}" if path != "$" else key
            raise DeclarativeSchemaUnknownPropertyError(
                key,
                allowed_properties=allowed,
                context=self._context(
                    path=property_path,
                    mapping=mapping,
                    key=key,
                    value=False,
                ),
            )

    def _require_key(
        self,
        mapping: dict[object, object],
        key: str,
        *,
        path: str,
        type_error: bool = False,
    ) -> None:
        if key in mapping:
            return
        message = f"Missing required property {key!r}."
        property_path = f"{path}.{key}" if path != "$" else key
        if type_error:
            self._raise_type_error(message, path=property_path)
        raise DeclarativeSchemaValidationError(
            message,
            context=self._context(path=property_path),
        )

    def _count_field_node(
        self,
        *,
        path: str,
        sequence: list[object],
        index: int,
    ) -> None:
        self._field_nodes += 1
        if self._field_nodes > self._limits.max_total_field_nodes:
            raise DeclarativeSchemaLimitError(
                "total_field_nodes",
                self._limits.max_total_field_nodes,
                self._field_nodes,
                context=self._context(
                    path=path,
                    sequence=sequence,
                    index=index,
                ),
            )

    def _raise_type_error(
        self,
        message: str,
        *,
        path: str,
        mapping: dict[object, object] | None = None,
        key: object | None = None,
        sequence: list[object] | None = None,
        index: int | None = None,
    ) -> NoReturn:
        raise DeclarativeSchemaTypeError(
            message=message,
            context=self._context(
                path=path,
                mapping=mapping,
                key=key,
                value=True,
                sequence=sequence,
                index=index,
            ),
        )

    def _context(
        self,
        *,
        path: str,
        mapping: dict[object, object] | None = None,
        key: object | None = None,
        value: bool = False,
        sequence: list[object] | None = None,
        index: int | None = None,
    ) -> DeclarativeErrorContext:
        position: tuple[int, int] | None = None

        if mapping is not None and key is not None:
            marks = (self._marks.value_marks if value else self._marks.key_marks).get(
                id(mapping), {}
            )
            try:
                position = marks.get(key)
            except TypeError:
                position = None
            if position is None:
                position = self._marks.mapping_starts.get(id(mapping))

        if sequence is not None and index is not None:
            item_marks = self._marks.item_marks.get(id(sequence), [])
            if 0 <= index < len(item_marks):
                position = item_marks[index]
            if position is None:
                position = self._marks.sequence_starts.get(id(sequence))

        if position is None:
            return DeclarativeErrorContext(
                source=self._source,
                object_path=path,
            )

        line, column = position
        return DeclarativeErrorContext(
            source=self._source,
            line=line,
            column=column,
            object_path=path,
        )


def _load_yaml_module() -> Any:
    try:
        return importlib.import_module("yaml")
    except ImportError as exc:
        raise DeclarativeSchemaDependencyError("PyYAML") from exc


def _position(mark: Any) -> tuple[int, int]:
    return (int(mark.line) + 1, int(mark.column) + 1)


def _context_from_mark(
    source: str | None,
    mark: Any,
    *,
    object_path: str | None = None,
) -> DeclarativeErrorContext:
    if mark is None:
        return DeclarativeErrorContext(
            source=source,
            object_path=object_path,
        )
    line, column = _position(mark)
    return DeclarativeErrorContext(
        source=source,
        line=line,
        column=column,
        object_path=object_path,
    )


def _bounded_key(key: object) -> str:
    rendered = key if isinstance(key, str) else repr(key)
    if len(rendered) <= 256:
        return rendered
    return rendered[:253] + "..."
