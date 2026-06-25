from __future__ import annotations

import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parents[1]
qauth_src = repo_root / "Q-AuthCore Module" / "src"
if str(qauth_src) not in sys.path:
    sys.path.insert(0, str(qauth_src))

from V1.main import app  # type: ignore  # noqa: E402,F401

