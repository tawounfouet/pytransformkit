"""Runtime binding contracts between logical plans and physical data."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from pytransformkit.domain.resources import (
    CredentialReference,
    ResourceReference,
    RetrySafety,
    WriteMode,
)


class InputBindingKind(StrEnum):
    NATIVE = "native"
    RESOURCE = "resource"


# Pre-1.0 compatibility name retained while LOT-20 promotes WriteMode.
OutputMode = WriteMode


@dataclass(frozen=True, slots=True)
class InputBinding:
    """Associate one named logical input with physical runtime data."""

    input_name: str
    kind: InputBindingKind
    native_value: object | None = None
    engine_id: str | None = None
    resource: ResourceReference | None = None
    credential: CredentialReference | None = None

    def __post_init__(self) -> None:
        if not self.input_name or not self.input_name.strip():
            raise ValueError("InputBinding input_name must not be empty.")
        if not isinstance(self.kind, InputBindingKind):
            raise TypeError("InputBinding kind must be an InputBindingKind.")

        if self.kind is InputBindingKind.NATIVE:
            if self.native_value is None:
                raise ValueError("Native InputBinding requires native_value.")
            if not self.engine_id or not self.engine_id.strip():
                raise ValueError("Native InputBinding requires engine_id.")
            if self.resource is not None:
                raise ValueError(
                    "Native InputBinding must not also contain a ResourceReference."
                )
            if self.credential is not None:
                raise ValueError(
                    "Native InputBinding must not contain CredentialReference."
                )
            return

        if self.resource is None:
            raise ValueError("Resource InputBinding requires ResourceReference.")
        if self.native_value is not None or self.engine_id is not None:
            raise ValueError(
                "Resource InputBinding must not contain native runtime values."
            )
        if self.credential is not None and not isinstance(
            self.credential,
            CredentialReference,
        ):
            raise TypeError("InputBinding credential must be CredentialReference.")

    @classmethod
    def from_native(
        cls,
        input_name: str,
        value: object,
        *,
        engine: str,
    ) -> InputBinding:
        return cls(
            input_name=input_name,
            kind=InputBindingKind.NATIVE,
            native_value=value,
            engine_id=engine,
        )

    @classmethod
    def from_resource(
        cls,
        input_name: str,
        resource: ResourceReference,
        *,
        credential: CredentialReference | None = None,
    ) -> InputBinding:
        return cls(
            input_name=input_name,
            kind=InputBindingKind.RESOURCE,
            resource=resource,
            credential=credential,
        )

    @property
    def portable(self) -> bool:
        return self.kind is InputBindingKind.RESOURCE


@dataclass(frozen=True, slots=True)
class OutputBinding:
    """Declare physical materialization for one named logical output."""

    output_name: str
    resource: ResourceReference
    mode: WriteMode = WriteMode.CREATE_NEW
    credential: CredentialReference | None = None
    retry_safety: RetrySafety = RetrySafety.UNKNOWN

    def __post_init__(self) -> None:
        if not self.output_name or not self.output_name.strip():
            raise ValueError("OutputBinding output_name must not be empty.")
        if not isinstance(self.resource, ResourceReference):
            raise TypeError("OutputBinding resource must be a ResourceReference.")
        if not isinstance(self.mode, WriteMode):
            raise TypeError("OutputBinding mode must be a WriteMode.")
        if self.credential is not None and not isinstance(
            self.credential,
            CredentialReference,
        ):
            raise TypeError("OutputBinding credential must be CredentialReference.")
        if not isinstance(self.retry_safety, RetrySafety):
            raise TypeError("OutputBinding retry_safety must be RetrySafety.")

    @classmethod
    def to_resource(
        cls,
        output_name: str,
        resource: ResourceReference,
        *,
        mode: WriteMode | str = WriteMode.CREATE_NEW,
        credential: CredentialReference | None = None,
        retry_safety: RetrySafety = RetrySafety.UNKNOWN,
    ) -> OutputBinding:
        return cls(
            output_name=output_name,
            resource=resource,
            mode=mode if isinstance(mode, WriteMode) else WriteMode(mode),
            credential=credential,
            retry_safety=retry_safety,
        )
