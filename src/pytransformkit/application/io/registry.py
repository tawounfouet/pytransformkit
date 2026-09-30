"""Explicit Reader/Writer registry for physical resource resolution."""

from __future__ import annotations

from pytransformkit.application.io.ports import Reader, Writer
from pytransformkit.errors.io import UnsupportedResourceSchemeError


class ResourceIORegistry:
    """Resolve Readers and Writers explicitly by ResourceReference scheme."""

    def __init__(self) -> None:
        self._readers: dict[str, Reader] = {}
        self._writers: dict[str, Writer] = {}

    def register_reader(self, reader: Reader) -> None:
        if not isinstance(reader, Reader):
            raise TypeError("reader must satisfy the Reader protocol.")
        for scheme in reader.schemes:
            normalized = _scheme(scheme)
            if normalized in self._readers:
                raise ValueError(
                    f"Reader already registered for scheme {normalized!r}."
                )
            self._readers[normalized] = reader

    def register_writer(self, writer: Writer) -> None:
        if not isinstance(writer, Writer):
            raise TypeError("writer must satisfy the Writer protocol.")
        for scheme in writer.schemes:
            normalized = _scheme(scheme)
            if normalized in self._writers:
                raise ValueError(
                    f"Writer already registered for scheme {normalized!r}."
                )
            self._writers[normalized] = writer

    def reader_for(self, scheme: str) -> Reader:
        normalized = _scheme(scheme)
        try:
            return self._readers[normalized]
        except KeyError as error:
            raise UnsupportedResourceSchemeError(
                f"No Reader is registered for resource scheme {normalized!r}."
            ) from error

    def writer_for(self, scheme: str) -> Writer:
        normalized = _scheme(scheme)
        try:
            return self._writers[normalized]
        except KeyError as error:
            raise UnsupportedResourceSchemeError(
                f"No Writer is registered for resource scheme {normalized!r}."
            ) from error


def _scheme(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("resource scheme must not be empty.")
    return value.strip().lower()
