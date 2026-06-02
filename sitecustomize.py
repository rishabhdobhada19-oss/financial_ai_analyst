from __future__ import annotations

import os
from pathlib import Path

_MPLCONFIGDIR = Path(__file__).resolve().parent / "data" / ".matplotlib"
_MPLCONFIGDIR.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(_MPLCONFIGDIR))
