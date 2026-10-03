from __future__ import annotations

import platform
from importlib.metadata import version

from pytransformkit.cli.models.reports import VersionReport
from pytransformkit.cli.services.version import VersionService


def test_version_service_reports_installed_package_and_python_versions() -> None:
    report = VersionService().inspect()

    assert report == VersionReport(
        pytransformkit=version("pytransformkit"),
        python=platform.python_version(),
    )
    assert report.to_data() == {
        "pytransformkit": version("pytransformkit"),
        "python": platform.python_version(),
    }
