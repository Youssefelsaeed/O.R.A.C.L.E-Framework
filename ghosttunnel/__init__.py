from __future__ import annotations

from pathlib import Path

_repo_root = Path(__file__).resolve().parents[1]
_real_pkg = _repo_root / "Ghost_Tunnel Module" / "src" / "ghosttunnel"
if _real_pkg.exists():
    __path__.append(str(_real_pkg))  # type: ignore[name-defined]
