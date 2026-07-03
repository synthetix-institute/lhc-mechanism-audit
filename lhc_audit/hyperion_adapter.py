from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict


def load_hyperion_featurizer(root: str | None):
    if root:
        path = Path(root).expanduser().resolve()
        if str(path) not in sys.path:
            sys.path.insert(0, str(path))
    try:
        from hyperion_lib.anchors.operator_substrate_featurizer import featurize_formula_pair

        return featurize_formula_pair
    except Exception:
        return None


def fingerprint_pair(source: str, target: str, relation: str, *, knowledgeparser_root: str | None) -> Dict[str, Any]:
    featurize = load_hyperion_featurizer(knowledgeparser_root)
    if featurize is None:
        return {
            "available": False,
            "reason": "Hyperion operator/substrate featurizer not importable.",
        }
    fp = featurize(source, target, relation)
    data = fp.to_dict()
    vector = data.get("vector")
    if vector is not None:
        data["vector_l1"] = float(sum(abs(float(x)) for x in vector))
        data["vector_nonzero"] = int(sum(1 for x in vector if abs(float(x)) > 1e-8))
        data.pop("vector", None)
    data["available"] = True
    # Ensure all nested structures are JSON-safe.
    return json.loads(json.dumps(data, ensure_ascii=False, default=str))
