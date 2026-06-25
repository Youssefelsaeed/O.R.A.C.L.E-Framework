"""Production vs candidate feature schema validation."""
from __future__ import annotations

from typing import Any, Dict, List, Optional


def validate_feature_schema(
    candidate_features: List[str],
    production_features: List[str],
) -> Dict[str, Any]:
    cand = [str(f).strip() for f in candidate_features]
    prod = [str(f).strip() for f in production_features]
    cand_set = set(cand)
    prod_set = set(prod)
    missing = sorted(prod_set - cand_set)
    extra = sorted(cand_set - prod_set)
    order_match = cand == prod if prod else True
    compatible = len(missing) == 0 and order_match and len(cand) == len(prod)
    return {
        "compatible": compatible,
        "missing_in_candidate": missing,
        "extra_in_candidate": extra[:50],
        "order_match": order_match,
        "candidate_feature_count": len(cand),
        "production_feature_count": len(prod),
        "status": "ok" if compatible else "schema_mismatch",
    }


def load_production_feature_schema_from_engine(engine: Any) -> List[str]:
    names = getattr(engine, "xgb_feature_names", None) or []
    return [str(n).strip() for n in names]
