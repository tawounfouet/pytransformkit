"""Schema conversion service for CLI payload commands."""

from __future__ import annotations

import contextlib
import os
import stat
import tempfile
from pathlib import Path

from pytransformkit.cli.exceptions import (
    CLIFileSystemError,
    CLIUnsupportedOperationError,
    CLIUsageError,
)
from pytransformkit.domain.data import Schema
from pytransformkit.errors import (
    DeclarativeErrorContext,
    DeclarativeSchemaCardinalityError,
)
from pytransformkit.schema_io import dumps_schema, load_schemas
from pytransformkit.serialization import SchemaCodec

_REMOTE_SCHEMES = (
    "http://",
    "https://",
    "s3://",
    "gs://",
    "gcs://",
    "az://",
    "azure://",
    "ftp://",
    "ftps://",
    "ssh://",
)

_YAML_SUFFIXES = {".yml", ".yaml"}
_VALID_FORMATS = {"yaml", "json"}


def _reject_remote_path(path: str) -> None:
    lowered = path.lstrip().lower()
    if lowered.startswith(_REMOTE_SCHEMES):
        raise CLIUnsupportedOperationError(
            "Remote schema paths are not supported by the PyTransformKit CLI."
        )


def _normalize_format(value: str, *, option: str) -> str:
    normalized = value.strip().lower()
    if normalized not in _VALID_FORMATS:
        raise CLIUsageError(f"{option} must be one of: yaml, json; received {value!r}.")
    return normalized


def _infer_source_format(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in _YAML_SUFFIXES:
        return "yaml"
    if suffix == ".json":
        return "json"
    raise CLIUsageError(
        "Cannot infer schema input format from extension; use --from yaml|json."
    )


def _same_path(left: Path, right: Path) -> bool:
    return os.path.normcase(os.path.abspath(left)) == os.path.normcase(
        os.path.abspath(right)
    )


def _load_yaml_schema(path: str) -> tuple[Schema, str]:
    schemas = load_schemas(path)
    if len(schemas) != 1:
        raise DeclarativeSchemaCardinalityError(
            1,
            len(schemas),
            context=DeclarativeErrorContext(source=path),
        )
    name, schema = next(iter(schemas.items()))
    return schema, name


def _read_json_schema(path: Path) -> Schema:
    try:
        payload = path.read_bytes()
    except OSError as exc:
        raise CLIFileSystemError(path, str(exc)) from exc
    return SchemaCodec().from_json(payload)


def _write_new_atomic(path: Path, text: str) -> None:
    parent = path.parent
    if not parent.exists():
        raise CLIFileSystemError(path, f"Output parent does not exist: {parent}")
    if not parent.is_dir():
        raise CLIFileSystemError(path, f"Output parent is not a directory: {parent}")

    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="",
            dir=parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as stream:
            temp_path = Path(stream.name)
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())

        try:
            os.link(temp_path, path)
        except OSError as exc:
            raise CLIFileSystemError(path, str(exc)) from exc
        with contextlib.suppress(OSError):
            temp_path.unlink()
        temp_path = None
    finally:
        if temp_path is not None:
            with contextlib.suppress(OSError):
                temp_path.unlink(missing_ok=True)


def _replace_existing_atomic(path: Path, text: str) -> None:
    try:
        original = path.lstat()
    except OSError as exc:
        raise CLIFileSystemError(path, str(exc)) from exc

    if stat.S_ISLNK(original.st_mode):
        raise CLIFileSystemError(
            path,
            f"Refusing to write through symbolic link: {path}",
        )
    if not stat.S_ISREG(original.st_mode):
        raise CLIFileSystemError(path, f"Output must be a regular file: {path}")

    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as stream:
            temp_path = Path(stream.name)
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())

        os.chmod(temp_path, stat.S_IMODE(original.st_mode))

        try:
            current = path.lstat()
        except OSError as exc:
            raise CLIFileSystemError(path, str(exc)) from exc
        if stat.S_ISLNK(current.st_mode):
            raise CLIFileSystemError(
                path,
                f"Refusing to replace symbolic link: {path}",
            )
        if not stat.S_ISREG(current.st_mode):
            raise CLIFileSystemError(
                path,
                f"Output is no longer a regular file: {path}",
            )
        if (current.st_dev, current.st_ino) != (original.st_dev, original.st_ino):
            raise CLIFileSystemError(
                path,
                f"Output changed before atomic replace: {path}",
            )

        try:
            os.replace(temp_path, path)
        except OSError as exc:
            raise CLIFileSystemError(path, str(exc)) from exc
        temp_path = None
    finally:
        if temp_path is not None:
            with contextlib.suppress(OSError):
                temp_path.unlink(missing_ok=True)


def _write_output(path: Path, text: str, *, force: bool) -> None:
    if path.is_symlink():
        raise CLIFileSystemError(
            path,
            f"Refusing to write through symbolic link: {path}",
        )

    try:
        existing = path.lstat()
    except FileNotFoundError:
        existing = None
    except OSError as exc:
        raise CLIFileSystemError(path, str(exc)) from exc

    if existing is None:
        _write_new_atomic(path, text)
        return

    if not force:
        raise CLIFileSystemError(
            path,
            f"Output already exists; pass --force to replace it: {path}",
        )

    _replace_existing_atomic(path, text)


class SchemaConversionService:
    """Convert explicit local schema files between YAML and SchemaCodec JSON."""

    def convert(
        self,
        input_path: str | Path,
        *,
        to_format: str,
        from_format: str | None = None,
        name: str | None = None,
        output: str | Path | None = None,
        force: bool = False,
    ) -> str | None:
        """Convert one canonical Schema and optionally write the payload."""
        input_text = str(input_path)
        _reject_remote_path(input_text)
        source_path = Path(input_text)

        target_format = _normalize_format(to_format, option="--to")
        source_format = (
            _normalize_format(from_format, option="--from")
            if from_format is not None
            else _infer_source_format(source_path)
        )

        if force and output is None:
            raise CLIUsageError("--force requires --output.")

        output_path: Path | None = None
        if output is not None:
            output_text = str(output)
            _reject_remote_path(output_text)
            output_path = Path(output_text)
            if _same_path(source_path, output_path):
                raise CLIUsageError(
                    "schema convert input and --output must be different paths."
                )

        source_name: str | None = None
        if source_format == "yaml":
            schema, source_name = _load_yaml_schema(input_text)
        else:
            schema = _read_json_schema(source_path)

        if target_format == "json":
            payload = SchemaCodec().to_json(schema)
        else:
            yaml_name = name or source_name
            if yaml_name is None:
                raise CLIUsageError(
                    "--name is required when converting SchemaCodec JSON to YAML."
                )
            payload = dumps_schema(schema, name=yaml_name)

        if output_path is not None:
            _write_output(output_path, payload, force=force)
            return None

        return payload


__all__ = ["SchemaConversionService"]
