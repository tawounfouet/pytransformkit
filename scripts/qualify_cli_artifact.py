"""Create a clean environment, install one built artifact, and smoke it."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import venv
from pathlib import Path


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--venv", type=Path, required=True)
    parser.add_argument("--dist", type=Path, default=Path("dist"))
    parser.add_argument("--kind", choices=("wheel", "sdist"), required=True)
    parser.add_argument("--extras", default="")
    parser.add_argument(
        "--mode",
        choices=("core", "cli", "cli-yaml", "cli-no-yaml"),
        required=True,
    )
    parser.add_argument(
        "--smoke-script",
        type=Path,
        default=Path("scripts/cli_artifact_smoke.py"),
    )
    return parser.parse_args()


def _python(venv_path: Path) -> Path:
    scripts = "Scripts" if os.name == "nt" else "bin"
    executable = "python.exe" if os.name == "nt" else "python"
    return venv_path / scripts / executable


def _artifact(dist: Path, kind: str) -> Path:
    pattern = "*.whl" if kind == "wheel" else "*.tar.gz"
    matches = sorted(dist.glob(pattern))
    if len(matches) != 1:
        raise SystemExit(
            f"Expected exactly one {kind} artifact in {dist}; found {matches!r}."
        )
    return matches[0].resolve()


def _run(*args: str) -> None:
    subprocess.run(args, check=True)


def main() -> int:
    args = _args()
    artifact = _artifact(args.dist, args.kind)

    if args.venv.exists():
        shutil.rmtree(args.venv)
    venv.EnvBuilder(with_pip=True, clear=True).create(args.venv)
    python = _python(args.venv)

    _run(str(python), "-m", "pip", "install", "--upgrade", "pip")

    requirement = artifact.as_uri()
    if args.extras:
        requirement = f"pytransformkit[{args.extras}] @ {requirement}"
    _run(str(python), "-m", "pip", "install", requirement)
    _run(str(python), "-m", "pip", "check")

    if args.mode == "cli-no-yaml":
        _run(
            str(python),
            "-m",
            "pip",
            "uninstall",
            "--yes",
            "PyYAML",
        )

    _run(
        str(python),
        str(args.smoke_script.resolve()),
        "--mode",
        args.mode,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
