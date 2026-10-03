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


def build_v1_1_catalogue(baseline_file: Path) -> dict[str, object]:
    """Build the exact 1.1 successor while preserving every V1 entry."""
    baseline = json.loads(baseline_file.read_text(encoding="utf-8"))
    current = build_catalogue()
    mismatches = _baseline_mismatches(baseline, current)
    if mismatches:
        raise RuntimeError(
            "Cannot freeze 1.1 error catalogue because V1 entries drifted: "
            + "; ".join(mismatches)
        )

    entries = current["entries"]
    if not isinstance(entries, dict):
        raise RuntimeError("Error catalogue entries must be a mapping.")

    expected_declarative_codes = {f"PTK-DECL-{index:03d}" for index in range(14)}
    actual_declarative_codes = {
        entry["code"]
        for name, entry in entries.items()
        if name.startswith("DeclarativeSchema")
    }
    if actual_declarative_codes != expected_declarative_codes:
        raise RuntimeError(
            "Declarative error code set is incomplete or unexpected: "
            f"expected={sorted(expected_declarative_codes)!r}, "
            f"actual={sorted(actual_declarative_codes)!r}."
        )

    return {
        "catalogue_version": 2,
        "contract": "pytransformkit.errors.v1",
        "framework_line": "1.1.x",
        "predecessor": "contracts/error_codes_v1.json",
        "entries": entries,
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
    parser.add_argument(
        "--line",
        choices=("1.0", "1.1"),
        default="1.0",
    )
    parser.add_argument(
        "--baseline",
        type=Path,
        default=Path("contracts/error_codes_v1.json"),
    )
    return parser.parse_args()


def main() -> int:
    args = _arguments()
    if args.line == "1.0":
        actual = build_catalogue()
        pass_message = "V1 error catalogue: PASS"
    else:
        actual = build_v1_1_catalogue(args.baseline)
        pass_message = "V1.1 error catalogue: PASS"

    if args.write is not None:
        args.write.parent.mkdir(parents=True, exist_ok=True)
        args.write.write_text(
            json.dumps(actual, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(f"Wrote error catalogue to {args.write}")
        return 0

    expected = json.loads(args.check.read_text(encoding="utf-8"))
    if args.line == "1.0":
        mismatches = _baseline_mismatches(expected, actual)
        if not mismatches:
            print(pass_message)
            return 0
    else:
        mismatches = []
        if actual == expected:
            print(pass_message)
            return 0

    print("Error catalogue: FAIL", file=sys.stderr)
    for mismatch in mismatches:
        print(f"- {mismatch}", file=sys.stderr)
    print("--- expected baseline", file=sys.stderr)
    print(json.dumps(expected, indent=2, sort_keys=True), file=sys.stderr)
    print("--- actual catalogue", file=sys.stderr)
    print(json.dumps(actual, indent=2, sort_keys=True), file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
