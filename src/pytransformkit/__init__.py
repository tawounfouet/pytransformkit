"""PyTransformKit public package."""

from importlib.metadata import PackageNotFoundError, version

from pytransformkit.domain.pipelines.pipeline import Pipeline

try:
    __version__ = version("pytransformkit")
except PackageNotFoundError:
    __version__ = "0.1.0a1"

__all__ = ["Pipeline", "__version__"]
