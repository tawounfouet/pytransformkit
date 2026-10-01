"""Generate or verify the PyTransformKit V1 consumer compatibility snapshot."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import warnings
from pathlib import Path
from typing import Any

import pytransformkit
from pytransformkit.plugins import (
    PLUGIN_API_VERSION,
    PLUGIN_ENTRY_POINT_GROUP,
    PluginCompatibility,
)


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object.")
    return value


def _digest(value: object) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _legacy_alias_snapshot(names: list[str]) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for name in names:
        if name in pytransformkit.__all__:
            raise RuntimeError(
                f"Legacy compatibility name {name!r} leaked into root __all__."
            )
        with warnings.catch_warnings(record=True) as captured:
            warnings.simplefilter("always")
            value = getattr(pytransformkit, name)

        deprecations = [
            item for item in captured if item.category is DeprecationWarning
        ]
        if len(deprecations) != 1:
            raise RuntimeError(
                f"Legacy compatibility name {name!r} must emit one "
                "DeprecationWarning."
            )

        result[name] = {
            "module": getattr(value, "__module__", type(value).__module__),
            "qualname": getattr(value, "__qualname__", type(value).__qualname__),
            "warning": "DeprecationWarning",
        }
    return result


def build_snapshot(
    public_api_path: Path,
    error_catalogue_path: Path,
) -> dict[str, object]:
    public_api = _load_json(public_api_path)
    error_catalogue = _load_json(error_catalogue_path)
    legacy_names = list(public_api["root_legacy_compatibility"])

    compatibility = PluginCompatibility()

    return {
        "snapshot_version": 1,
        "source_baseline": "0.8.0",
        "candidate_line": "0.9.0 -> 1.0.0rc1 -> 1.0.0",
        "public_api_category_hashes": public_api["category_hashes"],
        "root_exports": public_api["root_exports"],
        "legacy_aliases": _legacy_alias_snapshot(legacy_names),
        "wire_contracts": public_api["wire_contracts"],
        "error_catalogue_sha256": _digest(error_catalogue),
        "plugin_contract": {
            "entry_point_group": PLUGIN_ENTRY_POINT_GROUP,
            "protocol_version": PLUGIN_API_VERSION,
            "default_framework_min": str(compatibility.framework_min),
            "default_framework_max_exclusive": str(
                compatibility.framework_max_exclusive
            ),
            "default_protocol_min": compatibility.protocol_min,
            "default_protocol_max": compatibility.protocol_max,
        },
    }


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", type=Path)
    group.add_argument("--check", type=Path)
    parser.add_argument(
        "--public-api",
        type=Path,
        default=Path("contracts/public_api_v1.json"),
    )
    parser.add_argument(
        "--errors",
        type=Path,
        default=Path("contracts/error_codes_v1.json"),
    )
    return parser.parse_args()


def main() -> int:
    args = _arguments()
    actual = build_snapshot(args.public_api, args.errors)

    if args.write is not None:
        args.write.parent.mkdir(parents=True, exist_ok=True)
        args.write.write_text(
            json.dumps(actual, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(f"Wrote V1 consumer compatibility snapshot to {args.write}")
        return 0

    expected = json.loads(args.check.read_text(encoding="utf-8"))
    if actual == expected:
        print("V1 consumer compatibility: PASS")
        return 0

    print("V1 consumer compatibility: FAIL", file=sys.stderr)
    print("--- expected", file=sys.stderr)
    print(json.dumps(expected, indent=2, sort_keys=True), file=sys.stderr)
    print("--- actual", file=sys.stderr)
    print(json.dumps(actual, indent=2, sort_keys=True), file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
