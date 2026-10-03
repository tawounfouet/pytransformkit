from __future__ import annotations

import json
from importlib import resources
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

PACKAGED_CONTRACTS = (
    ("public_api_v1_1.json", ROOT / "contracts" / "public_api_v1_1.json"),
    ("error_codes_v1_1.json", ROOT / "contracts" / "error_codes_v1_1.json"),
)


def _packaged_json(filename: str) -> object:
    text = (
        resources.files("pytransformkit._contract_data")
        .joinpath(filename)
        .read_text(encoding="utf-8")
    )
    return json.loads(text)


def test_packaged_contract_snapshots_match_repository_authorities() -> None:
    for filename, repository_path in PACKAGED_CONTRACTS:
        expected = json.loads(repository_path.read_text(encoding="utf-8"))
        assert _packaged_json(filename) == expected
