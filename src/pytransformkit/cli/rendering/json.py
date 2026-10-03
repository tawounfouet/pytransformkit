"""Machine-readable JSON rendering for CLI reports.

This module intentionally depends only on the Python standard library and
presentation-neutral CLI models. It must not import Rich.
"""

from __future__ import annotations

import json
from collections.abc import Mapping

from pytransformkit.cli.models.errors import CLIErrorReport

CLI_REPORT_CONTRACT_VERSION = 1

class JSONRenderer:
    """Serialize CLI reports using the candidate CLI v1 envelope."""

    def render_success(
        self,
        *,
        command: str,
        data: Mapping[str, object],
    ) -> str:
        """Serialize a successful report."""
        return self._dumps(
            {
                "contract_version": CLI_REPORT_CONTRACT_VERSION,
                "ok": True,
                "command": command,
                "data": dict(data),
            }
        )

    def render_error(
        self,
        *,
        command: str,
        error: CLIErrorReport,
    ) -> str:
        """Serialize a failed report."""
        return self._dumps(
            {
                "contract_version": CLI_REPORT_CONTRACT_VERSION,
                "ok": False,
                "command": command,
                "error": error.to_public_dict(),
            }
        )

    @staticmethod
    def _dumps(payload: Mapping[str, object]) -> str:
        return (
            json.dumps(
                payload,
                ensure_ascii=False,
                sort_keys=True,
            )
            + "\n"
        )

__all__ = ["CLI_REPORT_CONTRACT_VERSION", "JSONRenderer"]
