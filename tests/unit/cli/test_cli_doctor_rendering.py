from __future__ import annotations

import pytest

pytest.importorskip("typer")
pytest.importorskip("rich")

from pytransformkit.cli.commands import doctor as doctor_module
from pytransformkit.cli.exit_codes import ExitCode
from pytransformkit.cli.models.reports import (
    DoctorCheck,
    DoctorCheckStatus,
    DoctorReport,
    DoctorStatus,
)


def test_render_doctor_returns_general_error_for_fatal_report(
    monkeypatch,
    capsys,
) -> None:
    report = DoctorReport(
        status=DoctorStatus.ERROR,
        checks=(
            DoctorCheck(
                name="python",
                status=DoctorCheckStatus.INCOMPATIBLE,
                version="3.15.0",
            ),
        ),
    )
    monkeypatch.setattr(
        doctor_module.DoctorService,
        "inspect",
        lambda self: report,
    )

    exit_code = doctor_module.render_doctor(
        quiet=True,
        no_color=True,
    )

    assert exit_code is ExitCode.GENERAL_ERROR
    captured = capsys.readouterr()
    assert "Doctor: error" in captured.out


def test_render_doctor_degraded_report_is_process_success(
    monkeypatch,
    capsys,
) -> None:
    report = DoctorReport(
        status=DoctorStatus.DEGRADED,
        checks=(
            DoctorCheck(
                name="pandas",
                status=DoctorCheckStatus.MISSING,
            ),
        ),
    )
    monkeypatch.setattr(
        doctor_module.DoctorService,
        "inspect",
        lambda self: report,
    )

    exit_code = doctor_module.render_doctor(
        quiet=True,
        no_color=True,
    )

    assert exit_code is ExitCode.SUCCESS
    captured = capsys.readouterr()
    assert "Doctor: degraded" in captured.out
