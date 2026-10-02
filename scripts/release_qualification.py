"""Validate the LOT-27 release-candidate qualification manifest."""

from __future__ import annotations

import argparse
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
    match = re.search(
        r"python-version:\s*\[([^\]]+)\]",
        workflow,
    )
    if match is None:
        return []
    return re.findall(r'"([^"]+)"', match.group(1))


def _version_core(value: str) -> tuple[int, int, int]:
    match = re.match(r"^(\\d+)\\.(\\d+)\\.(\\d+)", value)
    if match is None:
        raise ValueError(f"Unsupported project version {value!r}.")
    return tuple(int(part) for part in match.groups())


def _preserves_release_line(current: str, baseline: str) -> bool:
    current_core = _version_core(current)
    baseline_core = _version_core(baseline)
    if current_core[0] != baseline_core[0]:
        return False
    if current_core < baseline_core:
        return False
    if current_core == baseline_core and current != baseline:
        return False
    return True


def validate(root: Path, manifest_path: Path) -> list[str]:
    manifest = _load_json(manifest_path)
    errors: list[str] = []

    if manifest.get("manifest_version") != 1:
        errors.append("manifest_version must be 1")
    if manifest.get("lot") != "LOT-27":
        errors.append("lot must be LOT-27")
    if manifest.get("release_candidate_target") != "1.0.0rc1":
        errors.append("release_candidate_target must be 1.0.0rc1")

    with (root / "pyproject.toml").open("rb") as stream:
        project = tomllib.load(stream)["project"]

    expected_version = manifest.get("project_version")
    current_version = project.get("version")
    if not isinstance(expected_version, str) or not isinstance(current_version, str):
        errors.append("project version drift: project and baseline versions must be strings")
    elif not _preserves_release_line(current_version, expected_version):
        errors.append(
            "project version drift: "
            f"expected frozen baseline {expected_version!r} or a later compatible "
            f"1.x version, got {current_version!r}"
        )

    expected_requires_python = manifest.get("requires_python")
    if project.get("requires-python") != expected_requires_python:
        errors.append(
            "requires-python drift: "
            f"expected {expected_requires_python!r}, "
            f"got {project.get('requires-python')!r}"
        )

    actual_extras = set(project.get("optional-dependencies", {}))
    expected_extras = set(manifest.get("extras", []))
    missing_extras = sorted(expected_extras - actual_extras)
    if missing_extras:
        errors.append(
            "extra-name drift: frozen V1 extras disappeared: "
            f"{missing_extras!r}"
        )

    workflow_path = root / ".github" / "workflows" / "ci.yml"
    workflow = workflow_path.read_text(encoding="utf-8")

    actual_python_versions = _python_matrix(workflow)
    expected_python_versions = manifest.get("python_versions", [])
    if actual_python_versions != expected_python_versions:
        errors.append(
            "Python CI matrix drift: "
            f"expected {expected_python_versions!r}, "
            f"got {actual_python_versions!r}"
        )

    jobs = _workflow_jobs(workflow)
    missing_jobs = sorted(set(manifest.get("required_ci_jobs", [])) - jobs)
    if missing_jobs:
        errors.append(f"missing required CI jobs: {missing_jobs!r}")

    missing_paths = [
        relative
        for relative in manifest.get("required_paths", [])
        if not (root / relative).is_file()
    ]
    if missing_paths:
        errors.append(f"missing release evidence paths: {missing_paths!r}")

    public_api = _load_json(root / "contracts" / "public_api_v1.json")
    expected_hashes = manifest.get("frozen_api_category_hashes", {})
    actual_hashes = public_api.get("category_hashes", {})
    if actual_hashes != expected_hashes:
        errors.append("frozen V1 public API category hashes drifted")

    expected_engine_ids = sorted(manifest.get("engine_ids", []))
    actual_engine_ids = sorted(public_api.get("engine_ids", []))
    if actual_engine_ids != expected_engine_ids:
        errors.append(
            f"engine-id drift: expected {expected_engine_ids!r}, "
            f"got {actual_engine_ids!r}"
        )

    stable = set(manifest.get("stable_engines", []))
    provisional = set(manifest.get("provisional_engines", []))
    if stable & provisional:
        errors.append("stable_engines and provisional_engines must be disjoint")
    if stable | provisional != set(expected_engine_ids):
        errors.append(
            "stable/provisional engine partition must cover every official engine ID"
        )

    artifact_policy = manifest.get("artifact_policy", {})
    for key in (
        "wheel_required",
        "sdist_required",
        "clean_install_required",
        "core_optional_dependency_isolation_required",
    ):
        if artifact_policy.get(key) is not True:
            errors.append(f"artifact_policy.{key} must remain true")

    post_rc1_policy = manifest.get("post_rc1_policy", {})
    if post_rc1_policy.get("architecture_changes_allowed") is not False:
        errors.append("post_rc1_policy.architecture_changes_allowed must be false")
    if post_rc1_policy.get("feature_changes_allowed") is not False:
        errors.append("post_rc1_policy.feature_changes_allowed must be false")
    if post_rc1_policy.get("blocker_fixes_only") is not True:
        errors.append("post_rc1_policy.blocker_fixes_only must be true")

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
        args.check if args.check.is_absolute() else (root / args.check)
    ).resolve()

    errors = validate(root, manifest_path)
    if errors:
        print("Release qualification manifest: FAIL", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("Release qualification manifest: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
