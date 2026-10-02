"""Generate or verify the stable PyTransformKit V1 error-code catalogue."""

from __future__ import annotations

import argparse
import inspect
import json
import re
import sys
from pathlib import Path

import pytransformkit.errors as errors
from pytransformkit.errors import PyTransformKitError

ERROR_CODE_PATTERN = re.compile(r"^PTK-[A-Z]+-[0-9]{3}$")


def build_catalogue() -> dict[str, object]:
    entries: dict[str, dict[str, str]] = {}
    seen_codes: dict[str, str] = {}

    for name in errors.__all__:
        value = getattr(errors, name)
        if not inspect.isclass(value) or not issubclass(value, PyTransformKitError):
            continue

        code = str(value.error_code)
        if ERROR_CODE_PATTERN.fullmatch(code) is None:
            raise RuntimeError(f"{name} exposes invalid V1 error code {code!r}.")
        previous = seen_codes.get(code)
        if previous is not None:
            raise RuntimeError(
                f"Duplicate V1 error code {code!r}: {previous} and {name}."
            )
        seen_codes[code] = name

        parent = next(
            (
                base.__name__
                for base in value.__mro__[1:]
                if issubclass(base, PyTransformKitError)
            ),
            "Exception",
        )
        entries[name] = {
            "code": code,
            "parent": parent,
        }

    if "PyTransformKitError" not in entries:
        raise RuntimeError(
            "PyTransformKitError must be part of the V1 error catalogue."
        )

    return {
        "catalogue_version": 1,
        "contract": "pytransformkit.errors.v1",
        "entries": dict(sorted(entries.items())),
    }


def _baseline_mismatches(
    expected: dict[str, object],
    actual: dict[str, object],
) -> list[str]:
    mismatches: list[str] = []

    for key in ("catalogue_version", "contract"):
        if actual.get(key) != expected.get(key):
            mismatches.append(
                f"{key} changed: expected={expected.get(key)!r}, "
                f"actual={actual.get(key)!r}"
            )

    expected_entries = expected.get("entries")
    actual_entries = actual.get("entries")
    if not isinstance(expected_entries, dict) or not isinstance(actual_entries, dict):
        return [*mismatches, "error catalogue entries must be mappings"]

    for name, expected_entry in expected_entries.items():
        actual_entry = actual_entries.get(name)
        if actual_entry != expected_entry:
            mismatches.append(
                f"{name} changed: expected={expected_entry!r}, actual={actual_entry!r}"
            )

    return mismatches


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", type=Path)
    group.add_argument("--check", type=Path)
    return parser.parse_args()


def main() -> int:
    args = _arguments()
    actual = build_catalogue()

    if args.write is not None:
        args.write.parent.mkdir(parents=True, exist_ok=True)
        args.write.write_text(
            json.dumps(actual, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(f"Wrote V1 error catalogue to {args.write}")
        return 0

    expected = json.loads(args.check.read_text(encoding="utf-8"))
    mismatches = _baseline_mismatches(expected, actual)
    if not mismatches:
        print("V1 error catalogue: PASS")
        return 0

    print("V1 error catalogue: FAIL", file=sys.stderr)
    for mismatch in mismatches:
        print(f"- {mismatch}", file=sys.stderr)
    print("--- expected baseline", file=sys.stderr)
    print(json.dumps(expected, indent=2, sort_keys=True), file=sys.stderr)
    print("--- actual catalogue", file=sys.stderr)
    print(json.dumps(actual, indent=2, sort_keys=True), file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
