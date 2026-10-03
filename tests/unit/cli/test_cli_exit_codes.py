from __future__ import annotations

from pytransformkit.cli.exit_codes import ExitCode


def test_cli_exit_code_catalogue_matches_candidate_v1_contract() -> None:
    assert {member.name: member.value for member in ExitCode} == {
        "SUCCESS": 0,
        "GENERAL_ERROR": 1,
        "INVALID_USAGE": 2,
        "INVALID_SCHEMA": 10,
        "MISSING_OPTIONAL_DEPENDENCY": 11,
        "FILESYSTEM_ERROR": 12,
        "UNSUPPORTED_OPERATION": 13,
        "INTERNAL_ERROR": 70,
        "INTERRUPTED": 130,
        "BROKEN_PIPE": 141,
    }
