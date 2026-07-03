from __future__ import annotations

import re
from collections import Counter, defaultdict
from typing import Any, Dict, Iterable, List


ROLE_PATTERNS = {
    "production_threshold": [
        r"\bsqrt\{?s\}?", r"\bM_D\b", r"threshold", r"parton", r"cross.?section", r"TeV", r"large extra dimensions",
    ],
    "evaporation_branch": [
        r"Hawking", r"evap", r"temperature", r"lifetime", r"\\tau", r"dM\s*/\s*dt\s*=\s*-", r"radiation",
    ],
    "stable_branch": [
        r"stable", r"metastable", r"does not evaporate", r"long.?lived", r"remnant",
    ],
    "capture_stopping": [
        r"capture", r"trapped", r"stopp", r"velocity", r"energy loss", r"Earth", r"detector", r"matter",
    ],
    "accretion_growth": [
        r"accret", r"growth", r"Bondi", r"Eddington", r"dM\s*/\s*dt", r"cross.?section", r"\\rho", r"density",
    ],
    "astrophysical_bound": [
        r"cosmic.?ray", r"white dwarf", r"neutron star", r"astronomical", r"lifetime", r"survival", r"Sun",
    ],
    "exclusion_conclusion": [
        r"exclude", r"ruled out", r"no risk", r"no danger", r"safe", r"cannot be dangerous", r"contra",
    ],
}


ROLE_ORDER = [
    "production_threshold",
    "evaporation_branch",
    "stable_branch",
    "capture_stopping",
    "accretion_growth",
    "astrophysical_bound",
    "exclusion_conclusion",
]


BLACK_HOLE_ANCHOR = re.compile(
    r"black.?hole|micro.?black.?hole|microscopic.?black.?hole|mini.?black.?hole|\bmbh\b|schwarzschild|horizon",
    re.I,
)
COLLIDER_ANCHOR = re.compile(
    r"\blhc\b|large hadron collider|collider|parton|hadron|tev|extra dimension|planck scale|trans.?planckian",
    re.I,
)
DENSE_BODY_ANCHOR = re.compile(
    r"white dwarf|neutron star|sun|earth|dense astrophysical|astronomical bod|cosmic.?ray",
    re.I,
)
SAFETY_ANCHOR = re.compile(
    r"safety|risk|danger|catastrophic|disaster|threat|exclude|ruled out|no risk|no danger|safe",
    re.I,
)


def _hits(patterns: List[str], text: str) -> int:
    return sum(len(re.findall(pattern, text, flags=re.I)) for pattern in patterns)


def _has(pattern: re.Pattern[str], text: str) -> bool:
    return bool(pattern.search(text))


def classify_roles(text: str, formula: str = "") -> Dict[str, float]:
    blob = f"{text} {formula}"
    scores: Dict[str, float] = {}
    black_hole = _has(BLACK_HOLE_ANCHOR, blob)
    collider = _has(COLLIDER_ANCHOR, blob)
    dense_body = _has(DENSE_BODY_ANCHOR, blob)
    safety = _has(SAFETY_ANCHOR, blob)

    # Role labels are intentionally gated.  Words such as "stable", "capture",
    # "tau" and "excluded" are common in unrelated physics.  They become LHC
    # black-hole safety evidence only when attached to the relevant physical
    # object or branch.
    production_hits = _hits(ROLE_PATTERNS["production_threshold"], blob)
    if production_hits and (black_hole or collider):
        scores["production_threshold"] = min(1.0, production_hits / 3.0)

    evaporation_hits = _hits(
        [r"Hawking", r"evap", r"black.?hole temperature", r"lifetime", r"dM\s*/\s*dt\s*=\s*-", r"radiation"],
        blob,
    )
    if evaporation_hits and black_hole:
        scores["evaporation_branch"] = min(1.0, evaporation_hits / 3.0)

    stable_hits = _hits(
        [r"\bstable\b", r"metastable", r"does not evaporate", r"long.?lived", r"remnant"],
        blob,
    )
    if stable_hits and black_hole:
        scores["stable_branch"] = min(1.0, stable_hits / 3.0)

    capture_hits = _hits(
        [r"capture", r"trapped", r"stopp", r"velocity", r"energy loss", r"Earth", r"detector", r"matter"],
        blob,
    )
    if capture_hits and black_hole and (collider or dense_body or safety):
        scores["capture_stopping"] = min(1.0, capture_hits / 3.0)

    accretion_hits = _hits(
        [r"accret", r"\bgrowth\b", r"Bondi", r"Eddington", r"dM\s*/\s*dt", r"cross.?section", r"\\rho", r"density"],
        blob,
    )
    if accretion_hits and black_hole:
        scores["accretion_growth"] = min(1.0, accretion_hits / 3.0)

    astro_hits = _hits(
        [r"cosmic.?ray", r"white dwarf", r"neutron star", r"astronomical", r"survival", r"Sun", r"Earth"],
        blob,
    )
    if astro_hits and (black_hole or safety):
        scores["astrophysical_bound"] = min(1.0, astro_hits / 3.0)

    exclusion_hits = _hits(
        [r"ruled out", r"no risk", r"no danger", r"safe", r"cannot be dangerous", r"disaster", r"catastrophic"],
        blob,
    )
    if exclusion_hits and (black_hole or collider) and safety:
        scores["exclusion_conclusion"] = min(1.0, exclusion_hits / 2.0)

    f = formula
    formula_hints = {
        "production_threshold": [r"\\sqrt\{?s\}?", r"\bM_D\b", r"\bs\s*[><=]"],
        "evaporation_branch": [r"evap", r"dM\s*\\over\s*dt\s*}\s*=\s*-", r"dM\s*/\s*dt\s*=\s*-"],
        "accretion_growth": [r"\\rho", r"\\sigma\(M\)", r"dM\s*\\over\s*dt\s*}\s*=\s*\\rho", r"dM\s*/\s*dt\s*=\s*rho"],
        "astrophysical_bound": [r"t_\{?\\rm\s*WD\}?", r"t_\{?grow\}?", r"t_\{?\\rm\s*NS\}?"],
        "capture_stopping": [r"\bv\b", r"dx", r"dE", r"stopp"],
    }
    for role, patterns in formula_hints.items():
        if not any(re.search(pattern, f, flags=re.I) for pattern in patterns):
            continue
        if role in {"evaporation_branch", "accretion_growth"} and not black_hole:
            continue
        if role == "capture_stopping" and not (black_hole and (collider or dense_body or safety)):
            continue
        if role == "astrophysical_bound" and not (black_hole or safety):
            continue
        if role == "production_threshold" and not (black_hole or collider):
            continue
        if role in {"evaporation_branch", "accretion_growth"}:
            scores[role] = max(scores.get(role, 0.0), 1.25)
        else:
            scores[role] = max(scores.get(role, 0.0), 1.0)
    if (
        black_hole
        and re.search(r"\\rho|\\sigma\(M\)|dM", f, flags=re.I)
        and re.search(r"\bv\b|\\,v", f, flags=re.I)
    ):
        scores["accretion_growth"] = max(scores.get("accretion_growth", 0.0), 1.5)
    return scores


def dominant_role(scores: Dict[str, float]) -> str:
    if not scores:
        return "unclassified"
    return max(scores.items(), key=lambda kv: (kv[1], -ROLE_ORDER.index(kv[0]) if kv[0] in ROLE_ORDER else -99))[0]


def extract_claims(text: str) -> List[Dict[str, Any]]:
    patterns = [
        ("safety_claim", r"([^.!?]{0,180}(?:no risk|no danger|safe|cannot be dangerous|no basis for concerns)[^.!?]{0,180}[.!?])"),
        ("risk_claim", r"([^.!?]{0,180}(?:catastrophic|risk|danger|threat|not excluded|metastable)[^.!?]{0,180}[.!?])"),
        ("astrophysical_claim", r"([^.!?]{0,180}(?:cosmic rays|white dwarfs|neutron stars|astronomical bodies)[^.!?]{0,180}[.!?])"),
    ]
    claims: List[Dict[str, Any]] = []
    for label, pattern in patterns:
        for match in re.finditer(pattern, text, flags=re.I):
            claims.append({
                "claim_type": label,
                "text": re.sub(r"\s+", " ", match.group(1)).strip(),
                "start": match.start(),
                "end": match.end(),
            })
    claims.sort(key=lambda x: (x["start"], x["end"]))
    return claims[:200]


def build_operational_graph(witnesses: List[Dict[str, Any]]) -> Dict[str, Any]:
    nodes = []
    by_role: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for idx, witness in enumerate(witnesses):
        node_id = f"W{idx:05d}"
        role = witness.get("dominant_role", "unclassified")
        node = {
            "id": node_id,
            "source_id": witness.get("source_id"),
            "role": role,
            "formula": witness.get("formula"),
            "context": witness.get("context"),
            "fingerprint": witness.get("fingerprint"),
        }
        nodes.append(node)
        by_role[role].append(node)

    edges = []
    for source_role, target_role in zip(ROLE_ORDER, ROLE_ORDER[1:]):
        for left in by_role.get(source_role, [])[:20]:
            for right in by_role.get(target_role, [])[:20]:
                if left["source_id"] == right["source_id"]:
                    edges.append({
                        "source": left["id"],
                        "target": right["id"],
                        "edge_type": "source_local_derivation_candidate",
                        "basis": "adjacent mechanism roles in the same paper",
                    })

    role_counts = Counter(w.get("dominant_role", "unclassified") for w in witnesses)
    chains = []
    for source_id in sorted({w.get("source_id") for w in witnesses}):
        source_roles = set()
        for witness in witnesses:
            if witness.get("source_id") != source_id:
                continue
            if witness.get("dominant_role") != "unclassified":
                source_roles.add(witness.get("dominant_role"))
            for role, score in (witness.get("role_scores") or {}).items():
                if float(score) >= 0.5:
                    source_roles.add(role)
        if {"stable_branch", "accretion_growth", "astrophysical_bound"} <= source_roles:
            chains.append({
                "source_id": source_id,
                "chain_type": "stable_black_hole_risk_exclusion_branch",
                "status": "equation_witness_supported",
                "logic": [
                    "assume stable microscopic black-hole branch",
                    "evaluate capture/accretion or growth mechanism",
                    "compare with cosmic-ray production/capture in dense astronomical bodies",
                    "use observed survival/lifetime as exclusion constraint",
                ],
            })
        if {"evaporation_branch", "exclusion_conclusion"} <= source_roles:
            chains.append({
                "source_id": source_id,
                "chain_type": "evaporation_safety_branch",
                "status": "equation_witness_supported",
                "logic": [
                    "assume Hawking evaporation branch",
                    "derive short lifetime or mass-loss behavior",
                    "demote accretion risk if evaporation dominates before capture/growth",
                ],
            })

    return {
        "nodes": nodes,
        "edges": edges,
        "role_counts": dict(role_counts),
        "chain_candidates": chains,
        "claim_scope": (
            "Operational graph over extracted equation/local-context witnesses. "
            "Edges are derivation candidates when mechanism roles co-occur in a source; "
            "they are not final physics proofs without manual review."
        ),
    }
