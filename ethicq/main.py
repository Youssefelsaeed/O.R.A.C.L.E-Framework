from __future__ import annotations

import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parents[1]
ethicq_root = repo_root / "Ethic-Q Module"
if str(ethicq_root) not in sys.path:
    sys.path.insert(0, str(ethicq_root))

from main import app  # type: ignore  # noqa: E402,F401

