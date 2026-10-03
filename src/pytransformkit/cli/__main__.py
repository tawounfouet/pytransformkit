"""Execute the optional PyTransformKit CLI as a Python module."""

from __future__ import annotations

from .bootstrap import main


if __name__ == "__main__":
    raise SystemExit(main())
