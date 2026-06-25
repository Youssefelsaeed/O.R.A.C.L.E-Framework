"""Local IBM ART discovery, sys.path injection, and import helpers."""
from __future__ import annotations

import importlib
import sys
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[2]

ART_FOLDER_CANDIDATES = [
    ROOT / "ART - IBM" / "adversarial-robustness-toolbox-main",
    ROOT / "adversarial-robustness-toolbox-main",
    ROOT / "tools" / "adversarial-robustness-toolbox-main",
]

ART_ZIP_CANDIDATES = [
    ROOT / "adversarial-robustness-toolbox-main.zip",
    ROOT / "ART - IBM" / "adversarial-robustness-toolbox-main.zip",
    ROOT / "tools" / "adversarial-robustness-toolbox-main.zip",
]

EXTRACT_TARGET = ROOT / "tools" / "adversarial-robustness-toolbox-main"


def _is_art_root(path: Path) -> bool:
    return path.is_dir() and (path / "art").is_dir() and (path / "setup.py").exists()


def locate_art_source() -> Optional[Path]:
    for candidate in ART_FOLDER_CANDIDATES:
        if _is_art_root(candidate):
            return candidate.resolve()
    return None


def locate_art_zip() -> Optional[Path]:
    for z in ART_ZIP_CANDIDATES:
        if z.is_file():
            return z.resolve()
    return None


def extract_art_zip(zip_path: Path, target: Path = EXTRACT_TARGET) -> Path:
    target.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(target.parent)
    nested = target.parent / "adversarial-robustness-toolbox-main"
    if _is_art_root(nested):
        return nested.resolve()
    if _is_art_root(target):
        return target.resolve()
    for child in target.parent.iterdir():
        if _is_art_root(child):
            return child.resolve()
    return target.resolve()


def add_art_to_path(source: Path) -> None:
    src = str(source.resolve())
    if src not in sys.path:
        sys.path.insert(0, src)


def try_import_art() -> Tuple[bool, Optional[str], Optional[str]]:
    try:
        art = importlib.import_module("art")
        version = getattr(art, "__version__", None)
        if version is None:
            try:
                from art import __version__ as art_ver  # type: ignore

                version = str(art_ver)
            except Exception:
                version = "unknown"
        return True, str(version), None
    except Exception as exc:
        return False, None, str(exc)


def ensure_art_on_path() -> Dict[str, Any]:
    """Add local ART source to sys.path if needed; does not pip install."""
    ok, version, err = try_import_art()
    if ok:
        return {
            "art_available": True,
            "art_version": version,
            "source_path": None,
            "import_error": None,
        }

    source = locate_art_source()
    zip_extracted = False
    if source is None:
        z = locate_art_zip()
        if z is not None:
            source = extract_art_zip(z)
            zip_extracted = True

    if source is not None:
        add_art_to_path(source)
        ok, version, err = try_import_art()
        if ok:
            return {
                "art_available": True,
                "art_version": version,
                "source_path": str(source),
                "zip_extracted": zip_extracted,
                "import_error": None,
            }

    return {
        "art_available": False,
        "art_version": None,
        "source_path": str(source) if source else None,
        "zip_extracted": zip_extracted,
        "import_error": err,
    }


def recommended_install_command(source: Optional[Path] = None) -> str:
    src = source or locate_art_source() or EXTRACT_TARGET
    return f'pip install -e "{src.resolve()}"'
