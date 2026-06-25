from __future__ import annotations

import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parents[1]
chronoledger_src = repo_root / "Chrono_Ledger Module" / "src" / "V1"
if str(chronoledger_src) not in sys.path:
    sys.path.insert(0, str(chronoledger_src))

from main import app  # type: ignore  # noqa: E402,F401

