#!/usr/bin/env python3
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from plainly.cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
