"""Generate or verify the frozen PyTransformKit CLI v1 contract."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from pytransformkit.cli.public_contract import build_cli_contract


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", type=Path)
    group.add_argument("--check", type=Path)
    return parser.parse_args()


def _load(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> int:
    args = _arguments()
    actual = build_cli_contract()

    if args.write is not None:
        _write(args.write, actual)
        print(f"Wrote CLI v1 contract to {args.write}")
        return 0

    expected = _load(args.check)
    if actual == expected:
        print("CLI v1 contract: PASS")
        return 0

    print("CLI v1 contract: FAIL", file=sys.stderr)
    print("--- expected baseline", file=sys.stderr)
    print(
        json.dumps(expected, ensure_ascii=False, indent=2, sort_keys=True),
        file=sys.stderr,
    )
    print("--- actual runtime", file=sys.stderr)
    print(
        json.dumps(actual, ensure_ascii=False, indent=2, sort_keys=True),
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
