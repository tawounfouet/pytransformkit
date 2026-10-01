"""Validate the LOT-28 PyTransformKit 1.0.0 stable release freeze."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import tomllib
from pathlib import Path
from typing import Any


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


def _workflow_jobs(workflow: str) -> set[str]:
    jobs: set[str] = set()
    in_jobs = False
    for line in workflow.splitlines():
        if line == "jobs:":
            in_jobs = True
            continue
        if not in_jobs:
            continue
        match = re.fullmatch(r"  ([a-z0-9][a-z0-9-]*):", line)
        if match is not None:
            jobs.add(match.group(1))
    return jobs


def _python_matrix(workflow: str) -> list[str]:
    match = re.search(r"python-version:\s*\[([^\]]+)\]", workflow)
    if match is None:
        return []
    return re.findall(r'"([^"]+)"', match.group(1))


def validate(root: Path, manifest_path: Path) -> list[str]:
    manifest = _load_json(manifest_path)
    errors: list[str] = []

    if manifest.get("manifest_version") != 1:
        errors.append("manifest_version must be 1")
    if manifest.get("lot") != "LOT-28":
        errors.append("lot must be LOT-28")
    if manifest.get("phase") != "stable-release":
        errors.append("phase must be stable-release")
    if manifest.get("release_candidate_version") != "1.0.0rc1":
        errors.append("release_candidate_version must be 1.0.0rc1")

    rc_commit = manifest.get("release_candidate_main_commit")
    if not isinstance(rc_commit, str) or re.fullmatch(r"[0-9a-f]{40}", rc_commit) is None:
        errors.append("release_candidate_main_commit must be a 40-character SHA")

    with (root / "pyproject.toml").open("rb") as stream:
        project = tomllib.load(stream)["project"]

    expected_version = manifest.get("project_version")
    if project.get("version") != expected_version:
        errors.append(
            "stable project version drift: "
            f"expected {expected_version!r}, got {project.get('version')!r}"
        )

    classifiers = set(project.get("classifiers", []))
    if "Development Status :: 5 - Production/Stable" not in classifiers:
        errors.append("stable package classifier is missing")

    expected_requires_python = manifest.get("requires_python")
    if project.get("requires-python") != expected_requires_python:
        errors.append(
            "requires-python drift: "
            f"expected {expected_requires_python!r}, "
            f"got {project.get('requires-python')!r}"
        )

    workflow = (root / ".github" / "workflows" / "ci.yml").read_text(
        encoding="utf-8"
    )
    if _python_matrix(workflow) != manifest.get("python_versions", []):
        errors.append("Python CI matrix drifted from the stable manifest")

    jobs = _workflow_jobs(workflow)
    missing_jobs = sorted(set(manifest.get("required_ci_jobs", [])) - jobs)
    if missing_jobs:
        errors.append(f"missing stable-release CI jobs: {missing_jobs!r}")

    missing_paths = [
        relative
        for relative in manifest.get("required_paths", [])
        if not (root / relative).is_file()
    ]
    if missing_paths:
        errors.append(f"missing stable-release evidence paths: {missing_paths!r}")

    public_api = _load_json(root / "contracts" / "public_api_v1.json")
    expected_hashes = manifest.get("frozen_api_category_hashes", {})
    if public_api.get("category_hashes") != expected_hashes:
        errors.append("V1 public API changed after the RC freeze")

    release_qualification = _load_json(
        root / "contracts" / "release_qualification_v1.json"
    )
    if release_qualification.get("project_version") != expected_version:
        errors.append("release qualification does not target the stable version")
    if release_qualification.get("frozen_api_category_hashes") != expected_hashes:
        errors.append("release qualification API hashes drifted")

    consumer = _load_json(root / "contracts" / "consumer_compatibility_v1.json")
    if consumer.get("source_baseline") != "0.8.0":
        errors.append("consumer compatibility source baseline must remain 0.8.0")
    if not str(consumer.get("candidate_line", "")).endswith("1.0.0"):
        errors.append("consumer compatibility candidate line must end at 1.0.0")
    if consumer.get("public_api_category_hashes") != expected_hashes:
        errors.append("consumer compatibility API hashes drifted")
    if consumer.get("wire_contracts") != public_api.get("wire_contracts"):
        errors.append("consumer wire contracts drifted from the public API freeze")
    if consumer.get("plugin_contract") != manifest.get("plugin_contract"):
        errors.append("plugin protocol V1 contract drifted")

    error_catalogue = _load_json(root / "contracts" / "error_codes_v1.json")
    if _digest(error_catalogue) != manifest.get("error_catalogue_sha256"):
        errors.append("V1 public error-code catalogue drifted")

    stable = set(manifest.get("stable_engines", []))
    provisional = set(manifest.get("provisional_engines", []))
    engine_ids = set(public_api.get("engine_ids", []))
    if stable & provisional:
        errors.append("stable and provisional engine sets must be disjoint")
    if stable | provisional != engine_ids:
        errors.append("stable/provisional engine partition must cover engine IDs")

    policy = manifest.get("release_policy", {})
    for key in (
        "new_features_allowed",
        "architecture_changes_allowed",
        "public_api_drift_allowed",
        "wire_contract_drift_allowed",
        "error_code_drift_allowed",
    ):
        if policy.get(key) is not False:
            errors.append(f"release_policy.{key} must be false")

    return errors


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", type=Path, required=True)
    parser.add_argument("--root", type=Path, default=Path("."))
    return parser.parse_args()


def main() -> int:
    args = _arguments()
    root = args.root.resolve()
    manifest_path = (
        args.check if args.check.is_absolute() else root / args.check
    ).resolve()

    errors = validate(root, manifest_path)
    if errors:
        print("Stable release freeze: FAIL", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("Stable release freeze: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
