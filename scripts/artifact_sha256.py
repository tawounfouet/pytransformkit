"""Write deterministic SHA-256 evidence for built distributions."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dist", type=Path, default=Path("dist"))
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    args = _args()
    artifacts = sorted(
        path
        for path in args.dist.iterdir()
        if path.is_file() and path.suffix in {".whl", ".gz"}
    )
    if not artifacts:
        raise SystemExit(f"No distribution artifacts found in {args.dist}.")

    lines = [f"{_sha256(path)}  {path.name}" for path in artifacts]
    args.output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(args.output.read_text(encoding="utf-8"), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
