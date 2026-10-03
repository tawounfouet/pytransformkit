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


def _version_core(value: str) -> tuple[int, int, int]:
    match = re.match(r"^(\d+)\.(\d+)\.(\d+)", value)
    if match is None:
        raise ValueError(f"Unsupported project version {value!r}.")
    return (
        int(match.group(1)),
        int(match.group(2)),
        int(match.group(3)),
    )


def _preserves_release_line(current: str, baseline: str) -> bool:
    current_core = _version_core(current)
    baseline_core = _version_core(baseline)
    if current_core[0] != baseline_core[0]:
        return False
    if current_core < baseline_core:
        return False
    return not (current_core == baseline_core and current != baseline)


def _validate_v1(root: Path, manifest_path: Path) -> list[str]:
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
    if (
        not isinstance(rc_commit, str)
        or re.fullmatch(r"[0-9a-f]{40}", rc_commit) is None
    ):
        errors.append("release_candidate_main_commit must be a 40-character SHA")

    with (root / "pyproject.toml").open("rb") as stream:
        project = tomllib.load(stream)["project"]

    expected_version = manifest.get("project_version")
    current_version = project.get("version")
    if not isinstance(expected_version, str) or not isinstance(current_version, str):
        errors.append(
            "stable project version drift: project and baseline versions "
            "must be strings"
        )
    elif not _preserves_release_line(current_version, expected_version):
        errors.append(
            "stable project version drift: "
            f"expected frozen baseline {expected_version!r} or a later compatible "
            f"1.x version, got {current_version!r}"
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

    workflow = (root / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
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


def _validate_v1_1(root: Path, manifest_path: Path) -> list[str]:
    manifest = _load_json(manifest_path)
    errors: list[str] = []

    if manifest.get("manifest_version") != 2:
        errors.append("manifest_version must be 2")
    if manifest.get("lot") != "LOT-43":
        errors.append("lot must be LOT-43")
    if manifest.get("phase") != "declarative-schema-stable-release":
        errors.append("phase must be declarative-schema-stable-release")
    if manifest.get("project_version") != "1.1.0":
        errors.append("project_version must be 1.1.0")
    if manifest.get("release_candidate_version") != "1.1.0rc2":
        errors.append("release_candidate_version must be 1.1.0rc2")

    rc_commit = manifest.get("release_candidate_main_commit")
    if (
        not isinstance(rc_commit, str)
        or re.fullmatch(r"[0-9a-f]{40}", rc_commit) is None
    ):
        errors.append("release_candidate_main_commit must be a 40-character SHA")

    predecessor_path = root / str(
        manifest.get("predecessor_stable_manifest", "")
    )
    if not predecessor_path.is_file():
        errors.append("predecessor stable manifest is missing")
    else:
        predecessor_errors = _validate_v1(root, predecessor_path)
        if predecessor_errors:
            errors.append(
                "V1 stable predecessor no longer validates: "
                + "; ".join(predecessor_errors)
            )

    with (root / "pyproject.toml").open("rb") as stream:
        project = tomllib.load(stream)["project"]

    current_version = project.get("version")
    allowed_versions = {
        manifest.get("release_candidate_version"),
        manifest.get("project_version"),
    }
    if current_version not in allowed_versions:
        errors.append(
            "1.1 stable promotion version drift: "
            f"expected one of {sorted(str(v) for v in allowed_versions)!r}, "
            f"got {current_version!r}"
        )

    if project.get("requires-python") != manifest.get("requires_python"):
        errors.append("requires-python drifted from the 1.1 stable manifest")

    optional_dependencies = project.get("optional-dependencies", {})
    additions = set(manifest.get("stable_runtime_extra_additions", []))
    missing_extras = sorted(additions - set(optional_dependencies))
    if missing_extras:
        errors.append(f"missing 1.1 stable extras: {missing_extras!r}")

    core_dependencies = [
        str(value).lower() for value in project.get("dependencies", [])
    ]
    if any(value.startswith("pyyaml") for value in core_dependencies):
        errors.append("PyYAML must remain optional and absent from core dependencies")

    workflow = (root / ".github" / "workflows" / "ci.yml").read_text(
        encoding="utf-8"
    )
    if _python_matrix(workflow) != manifest.get("python_versions", []):
        errors.append("Python CI matrix drifted from the 1.1 stable manifest")

    jobs = _workflow_jobs(workflow)
    missing_jobs = sorted(set(manifest.get("required_ci_jobs", [])) - jobs)
    if missing_jobs:
        errors.append(f"missing 1.1 stable CI jobs: {missing_jobs!r}")

    missing_paths = [
        relative
        for relative in manifest.get("required_paths", [])
        if not (root / relative).is_file()
    ]
    if missing_paths:
        errors.append(f"missing 1.1 stable evidence paths: {missing_paths!r}")

    public_v1 = _load_json(root / "contracts" / "public_api_v1.json")
    public_v1_1 = _load_json(
        root / str(manifest.get("public_api_contract", ""))
    )
    if public_v1_1.get("predecessor") != "contracts/public_api_v1.json":
        errors.append("1.1 public API successor predecessor drifted")
    if public_v1_1.get("v1_baseline_category_hashes") != public_v1.get(
        "category_hashes"
    ):
        errors.append("V1 public API baseline changed in the 1.1 successor")

    unchanged_v1 = public_v1_1.get("unchanged_v1", {})
    if unchanged_v1.get("root_exports") != public_v1.get("root_exports"):
        errors.append("V1 root exports changed in the 1.1 successor")
    if unchanged_v1.get("root_legacy_compatibility") != public_v1.get(
        "root_legacy_compatibility"
    ):
        errors.append("V1 legacy compatibility names changed in the 1.1 successor")
    if unchanged_v1.get("engine_ids") != public_v1.get("engine_ids"):
        errors.append("V1 engine IDs changed in the 1.1 successor")
    if unchanged_v1.get("wire_contracts") != public_v1.get("wire_contracts"):
        errors.append("V1 wire contracts changed in the 1.1 successor")

    expected_exports = manifest.get("schema_io_exports", [])
    if public_v1_1.get("schema_io_exports") != expected_exports:
        errors.append("schema_io stable export surface drifted")

    public_additions = public_v1_1.get("additions", {})
    if public_additions.get("stable_runtime_extras") != manifest.get(
        "stable_runtime_extra_additions"
    ):
        errors.append("1.1 stable runtime extra additions drifted")

    expected_schema_wire = manifest.get("schema_wire_contract")
    actual_schema_wire = public_v1.get("wire_contracts", {}).get("SchemaCodec")
    if actual_schema_wire != expected_schema_wire:
        errors.append("SchemaCodec wire contract changed during 1.1 promotion")

    errors_v1 = _load_json(root / "contracts" / "error_codes_v1.json")
    errors_v1_1 = _load_json(
        root / str(manifest.get("error_catalogue_contract", ""))
    )
    if errors_v1_1.get("predecessor") != "contracts/error_codes_v1.json":
        errors.append("1.1 error catalogue predecessor drifted")

    v1_entries = errors_v1.get("entries", {})
    successor_entries = errors_v1_1.get("entries", {})
    for name, entry in v1_entries.items():
        if successor_entries.get(name) != entry:
            errors.append(f"V1 public error changed in 1.1 successor: {name}")
            break

    actual_declarative_codes = sorted(
        entry.get("code")
        for name, entry in successor_entries.items()
        if name.startswith("DeclarativeSchema")
    )
    if actual_declarative_codes != manifest.get("declarative_error_codes", []):
        errors.append("stable PTK-DECL error-code set drifted")

    artifact_policy = manifest.get("artifact_policy", {})
    for key in (
        "wheel_required",
        "sdist_required",
        "twine_check_equivalent_required",
        "clean_core_install_required",
        "yaml_extra_install_required",
        "sha256_record_required",
    ):
        if artifact_policy.get(key) is not True:
            errors.append(f"artifact_policy.{key} must remain true")

    release_policy = manifest.get("release_policy", {})
    for key in (
        "new_features_allowed",
        "architecture_changes_allowed",
        "v1_baseline_drift_allowed",
        "declarative_api_drift_allowed",
        "wire_contract_drift_allowed",
        "error_code_drift_allowed",
    ):
        if release_policy.get(key) is not False:
            errors.append(f"release_policy.{key} must be false")

    return errors


def validate(root: Path, manifest_path: Path) -> list[str]:
    manifest = _load_json(manifest_path)
    if manifest.get("lot") == "LOT-43":
        return _validate_v1_1(root, manifest_path)
    return _validate_v1(root, manifest_path)


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
