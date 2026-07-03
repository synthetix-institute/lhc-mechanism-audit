from __future__ import annotations

import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


ROUTE_ORDER = [
    "transport_flow",
    "constraint_closure",
    "spectral_operator",
    "boundary_weak_form",
    "commutator_incompatibility",
    "discrete_protocol",
]

ROUTE_EXPLANATIONS = {
    "transport_flow": "state change, flux, rate, propagation or dynamical update",
    "constraint_closure": "balance, normalization, residual, conservation or closure condition",
    "spectral_operator": "operator, generator, mode, eigenvalue, expectation or spectral readout",
    "boundary_weak_form": "domain, interface, boundary, weak/test form or realization condition",
    "commutator_incompatibility": "non-commutation, incompatibility, bracket or order dependence",
    "discrete_protocol": "algorithmic, measurement, recurrence, intervention or ordered update protocol",
}

USABLE_PAIR_STATUSES = {"complete_constructor_pair", "partial_constructor_pair"}
RICH_ANALOGUE_MIN_ACTIVE_ROUTES = 2
CASE_PATTERNS = {
    "black_hole": re.compile(
        r"\b(?:black\s+hole|black-hole|micro(?:scopic)?\s+black\s+hole|mini\s+black\s+hole|"
        r"mbh|schwarzschild|horizon|r_s)\b",
        re.I,
    ),
    "collider_threshold": re.compile(
        r"\b(?:lhc|large\s+hadron\s+collider|collider|tev|parton|planck|extra\s+dimension|"
        r"production\s+threshold|threshold)\b|\\sqrt\{s\}|M_D\b",
        re.I,
    ),
    "evaporation_branch": re.compile(
        r"\b(?:hawking|evaporat|lifetime|temperature|mass\s+loss|decay\s+time|short\s+lived)\b|"
        r"dM\s*\\over\s*dt|\\dot\{?M\}?",
        re.I,
    ),
    "accretion_growth": re.compile(
        r"\b(?:accretion|accrete|bondi|eddington|growth|capture\s+rate|mass\s+rate|"
        r"swallow|absorb)\b|\\dot\{?M\}?|dM\s*\\over\s*dt|\\rho\s*\\,?\\sigma",
        re.I,
    ),
    "astrophysical_bound": re.compile(
        r"\b(?:cosmic\s+ray|white\s+dwarf|neutron\s+star|dense\s+star|sun|earth|astronomical|"
        r"survival|observed\s+survival)\b|t_\{?\\rm\s*WD\}?",
        re.I,
    ),
    "capture_stopping": re.compile(
        r"\b(?:capture|captured|trapped|stopping|energy\s+loss|slowing|matter\s+crossing|"
        r"detector\s+material)\b",
        re.I,
    ),
    "safety_risk": re.compile(
        r"\b(?:safety|risk|danger|catastroph|disaster|excluded|exclusion|safe|no\s+risk|"
        r"no\s+danger)\b",
        re.I,
    ),
}
CASE_COMPLEMENT_CATEGORIES = {
    "collider_threshold",
    "evaporation_branch",
    "accretion_growth",
    "astrophysical_bound",
    "capture_stopping",
    "safety_risk",
}
LOCAL_MECHANISM_CASE_CATEGORIES = {
    "collider_threshold",
    "evaporation_branch",
    "accretion_growth",
    "astrophysical_bound",
    "capture_stopping",
}
LOCAL_DIRECT_SAFETY_MECHANISMS = {
    "evaporation_branch",
    "accretion_growth",
    "capture_stopping",
    "safety_risk",
}
PROSE_WORD_STOP = {
    "begin",
    "end",
    "frac",
    "sqrt",
    "left",
    "right",
    "over",
    "quad",
    "qquad",
    "mathrm",
    "mathbf",
    "mathcal",
    "operatorname",
    "lambda",
    "sigma",
    "rho",
    "tau",
    "omega",
    "theta",
    "alpha",
    "beta",
    "gamma",
    "delta",
    "epsilon",
    "varepsilon",
    "propto",
    "sim",
    "grow",
    "evap",
}
PROSE_ARTIFACT_RE = re.compile(
    r"\$|\\(?:cite|ref|eqref|label|caption|section|subsection|paragraph)\b|"
    r"includegraphics|bibliography|bibitem|begin\{figure|begin\{table|"
    r"\b(?:The|These|Those|This|We|Recall|Fortunately|Analogous|Comparable|"
    r"models|copies|emission|observed|discussed|predict|larger|smaller|"
    r"existing|limits|depends|reside|study|found)\b",
    re.I,
)
RELATION_RE = re.compile(r"=|<|>|\\le|\\ge|\\sim|\\propto|\\to|\\rightarrow|->|\\mapsto")
MATH_SYMBOL_RE = re.compile(r"\\[A-Za-z]+|[_^{}=<>+\-*/]|\\(?:le|ge|sim|propto|to|rightarrow)")
WORD_RE = re.compile(r"\b[A-Za-z]{4,}\b")


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def source_case_texts(out_dir: Path) -> Dict[str, str]:
    """Return weak source-level text for case filtering.

    This is deliberately separated from route construction.  Source text can
    make a clean equation relevant to the LHC black-hole case, but it cannot
    create route evidence or make a formula pass the mechanism gate.
    """
    source_text: Dict[str, List[str]] = defaultdict(list)

    sources_path = out_dir / "sources.json"
    if sources_path.exists():
        for source in read_json(sources_path).get("sources", []):
            sid = str(source.get("source_id") or "")
            metadata = source.get("metadata") or {}
            if sid:
                source_text[sid].append(str(metadata.get("title") or ""))
                source_text[sid].append(str(metadata.get("arxiv_id") or ""))

    provenance_path = out_dir / "provenance_graph.json"
    if provenance_path.exists():
        for node in read_json(provenance_path).get("nodes", []):
            sid = str(node.get("source_id") or "")
            if sid and node.get("text"):
                source_text[sid].append(str(node.get("text") or ""))

    return {sid: " ".join(parts) for sid, parts in source_text.items()}


def compact(text: Any, limit: int = 360) -> str:
    value = " ".join(str(text or "").split())
    return value if len(value) <= limit else value[: limit - 3] + "..."


def category_hits(text: str) -> List[str]:
    return [name for name, pattern in CASE_PATTERNS.items() if pattern.search(text)]


def case_evidence(formula: Any, context: Any, source_id: Any, source_text: str) -> Dict[str, Any]:
    """Classify whether a usable equation belongs to the LHC black-hole case.

    The classifier is intentionally conservative:
    - local formula/context hits carry more weight than source-level hits;
    - a source-level black-hole mention alone is not sufficient;
    - the mechanism graph itself still depends on equation fingerprints.
    """
    local_text = f"{formula or ''} {context or ''}"
    source_blob = f"{source_id or ''} {source_text or ''}"
    local_categories = category_hits(local_text)
    source_categories = category_hits(source_blob)
    local_set = set(local_categories)
    source_set = set(source_categories)
    all_set = local_set | source_set

    score = 2 * len(local_set) + len(source_set)
    if "black_hole" in local_set and (all_set & CASE_COMPLEMENT_CATEGORIES):
        score += 3
    if "black_hole" in source_set and (local_set & (CASE_COMPLEMENT_CATEGORIES - {"safety_risk"})):
        score += 2
    if {"black_hole", "collider_threshold"} <= all_set and (
        local_set & {"evaporation_branch", "accretion_growth", "astrophysical_bound", "capture_stopping"}
    ):
        score += 2
    if {"black_hole", "accretion_growth", "astrophysical_bound"} <= all_set:
        score += 2

    case_relevant = (
        ("black_hole" in local_set and bool(all_set & CASE_COMPLEMENT_CATEGORIES))
        or ("black_hole" in source_set and bool(local_set & (CASE_COMPLEMENT_CATEGORIES - {"safety_risk"})))
        or ({"black_hole", "collider_threshold"} <= all_set and bool(local_set & CASE_COMPLEMENT_CATEGORIES))
    )
    local_direct_mechanism = bool(local_set & LOCAL_DIRECT_SAFETY_MECHANISMS)
    direct_safety_case = "black_hole" in local_set and "collider_threshold" in local_set and local_direct_mechanism
    astrophysical_analogue = (
        "black_hole" in local_set
        and "astrophysical_bound" in local_set
        and not direct_safety_case
    )
    branch_labels: List[str] = []
    if direct_safety_case:
        branch_labels.append("direct_lhc_safety")
    if astrophysical_analogue:
        branch_labels.append("astrophysical_black_hole_analogue")
    if "black_hole" in local_set and "evaporation_branch" in local_set:
        branch_labels.append("evaporation_branch")
    if "black_hole" in local_set and ("accretion_growth" in local_set or "capture_stopping" in local_set):
        branch_labels.append("stable_growth_or_capture_branch")
    if "black_hole" in local_set and "collider_threshold" in local_set:
        branch_labels.append("production_threshold_branch")

    return {
        "case_relevant": bool(case_relevant),
        "direct_safety_case": bool(direct_safety_case),
        "astrophysical_analogue": bool(astrophysical_analogue),
        "score": int(score),
        "local_categories": sorted(local_set),
        "source_categories": sorted(source_set),
        "categories": sorted(all_set),
        "branch_labels": branch_labels,
    }


def formula_detail_score(formula: Any, routes: Dict[str, float], roles: Iterable[str]) -> int:
    """Rank equations for display without changing the mechanism gate.

    Formula-core cleaning decides whether a node can enter the graph.  This
    score only decides which case-relevant receipts are most useful to inspect:
    equations with rates, bounds, multiple symbols and constructor roles are
    displayed ahead of isolated scale fragments such as ``~ 2 M_sun``.
    """
    value = " ".join(str(formula or "").split())
    score = 0
    symbol_count = len(MATH_SYMBOL_RE.findall(value))
    role_count = len(list(roles or []))
    active_route_count = sum(1 for route_score in routes.values() if float(route_score) >= 0.12)

    if len(value) >= 24:
        score += 1
    if len(value) >= 55:
        score += 1
    if len(value) >= 110:
        score += 1
    if RELATION_RE.search(value):
        score += 1
    if symbol_count >= 6:
        score += 1
    if symbol_count >= 12:
        score += 1
    if active_route_count >= 2:
        score += 1
    if active_route_count >= 3:
        score += 1
    if role_count >= 3:
        score += 1
    if re.search(r"d[A-Za-z]?\s*\\over\s*d[tT]|\\dot\{?M\}?|\\partial|\\langle|\\lesssim|\\gtrsim", value):
        score += 2
    if re.search(r"\\rho|\\sigma|\\sqrt\{s\}|M_D|t_\{?\\rm|r_s|\\Phi|\\Omega|\\lambda", value):
        score += 1
    if re.search(r"^\s*(?:\\sim|>|<|\\lesssim|\\gtrsim)?\s*\d", value) and len(value) < 28:
        score -= 3
    if re.fullmatch(r"\\?sim\s*[\d^\-{}\\.\\\sA-Za-z_/]+", value) and len(value) < 36:
        score -= 3
    return score


def formula_quality_flags(text: Any) -> List[str]:
    value = " ".join(str(text or "").split())
    flags: List[str] = []
    if not value:
        return ["empty"]
    if PROSE_ARTIFACT_RE.search(value):
        flags.append("prose_or_latex_artifact")
    words = [word.lower() for word in WORD_RE.findall(value)]
    prose_words = [word for word in words if word not in PROSE_WORD_STOP]
    math_symbols = len(MATH_SYMBOL_RE.findall(value))
    if not RELATION_RE.search(value):
        flags.append("no_relation_operator")
    if prose_words and len(prose_words) > max(6, math_symbols):
        flags.append("word_heavy_formula")
    if re.search(r"[.!?]\s+[A-Z][a-z]{2,}", value):
        flags.append("sentence_boundary_inside_formula")
    if len(value) > 420 and len(prose_words) > 8:
        flags.append("long_prose_fragment")
    return flags or ["formula_core"]


def is_formula_core(text: Any) -> bool:
    flags = set(formula_quality_flags(text))
    hard = {
        "empty",
        "prose_or_latex_artifact",
        "no_relation_operator",
        "word_heavy_formula",
        "sentence_boundary_inside_formula",
        "long_prose_fragment",
    }
    return not bool(flags & hard)


def route_profile(fp: Dict[str, Any]) -> Dict[str, float]:
    raw = fp.get("route_evidence") or {}
    out: Dict[str, float] = {}
    for route in ROUTE_ORDER:
        try:
            value = float(raw.get(route, 0.0))
        except Exception:
            value = 0.0
        if value > 0.0:
            out[route] = value
    return out


def supplemented_route_profile(fp: Dict[str, Any], formula: str) -> Dict[str, float]:
    """Return route evidence with formula-level supplements for common TeX forms.

    This is not a semantic keyword layer.  It catches equation constructions
    that the generic V2 route patterns can miss, especially TeX variants such
    as ``dM\\over dt``.
    """
    routes = dict(route_profile(fp))
    text = str(formula or "")
    frame = fp.get("source_frame") or {}
    target_frame = fp.get("target_frame") or {}
    constructor_roles = set(constructor_roles_from_frames(frame, target_frame))

    if re.search(r"d[A-Za-z]?\s*\\over\s*d[tT]|d[A-Za-z]?\s*/\s*d[tT]|\\dot|\\partial_t", text):
        routes["transport_flow"] = max(routes.get("transport_flow", 0.0), 0.75)
    if re.search(r"\\rho|\\sigma\s*\(|flux|current|\\nabla|\\partial_i", text, re.I):
        routes["transport_flow"] = max(routes.get("transport_flow", 0.0), 0.45)
    if re.search(r"=\s*0|<|>|\\le|\\ge|\\propto|\\sim|constraint|bound", text, re.I):
        routes["constraint_closure"] = max(routes.get("constraint_closure", 0.0), 0.45)
    if re.search(r"\\lambda|eigen|spectrum|H\\s*\\psi|L\\s*\\psi", text, re.I):
        routes["spectral_operator"] = max(routes.get("spectral_operator", 0.0), 0.55)
    if re.search(r"\\Omega|\\partial\\s*\\Omega|boundary|surface|interface|r_s|horizon", text, re.I):
        routes["boundary_weak_form"] = max(routes.get("boundary_weak_form", 0.0), 0.45)
    if re.search(r"\[[^\]]+,[^\]]+\]|AB\s*-\s*BA|\\{[^{}]+,[^{}]+\\}", text):
        routes["commutator_incompatibility"] = max(routes.get("commutator_incompatibility", 0.0), 0.55)
    if re.search(r"n\+1|\\rightarrow|->|\\mapsto|step|iterate", text, re.I):
        routes["discrete_protocol"] = max(routes.get("discrete_protocol", 0.0), 0.45)

    if "closure_constraints" in constructor_roles:
        routes["constraint_closure"] = max(routes.get("constraint_closure", 0.0), 0.35)
    if "operator_apparatus" in constructor_roles or "readout_current" in constructor_roles:
        routes["spectral_operator"] = max(routes.get("spectral_operator", 0.0), 0.25)
    if "real_substrate_geometry" in constructor_roles and re.search(r"\\partial|boundary|horizon|surface", text, re.I):
        routes["boundary_weak_form"] = max(routes.get("boundary_weak_form", 0.0), 0.35)

    return {route: float(value) for route, value in routes.items() if value > 0.0}


def route_signature(routes: Dict[str, float], threshold: float = 0.12) -> Tuple[str, ...]:
    active = [route for route, score in sorted(routes.items(), key=lambda kv: (-kv[1], kv[0])) if score >= threshold]
    return tuple(active[:4]) if active else ("route_sparse",)


def route_cosine(left: Dict[str, float], right: Dict[str, float]) -> float:
    dot = sum(left.get(route, 0.0) * right.get(route, 0.0) for route in ROUTE_ORDER)
    ln = math.sqrt(sum(left.get(route, 0.0) ** 2 for route in ROUTE_ORDER))
    rn = math.sqrt(sum(right.get(route, 0.0) ** 2 for route in ROUTE_ORDER))
    if ln <= 0.0 or rn <= 0.0:
        return 0.0
    return float(dot / (ln * rn))


def fingerprint_available(witness: Dict[str, Any]) -> bool:
    fp = witness.get("fingerprint") or {}
    return bool(fp.get("available")) and bool(fp.get("route_evidence"))


def pair_status(fp: Dict[str, Any]) -> str:
    audit = fp.get("pair_audit") or {}
    return str(audit.get("status") or "unknown")


def constructor_roles(fp: Dict[str, Any]) -> List[str]:
    audit = fp.get("pair_audit") or {}
    roles = audit.get("present_roles") or []
    return [str(role) for role in roles]


def constructor_roles_from_frames(source_frame: Dict[str, Any], target_frame: Dict[str, Any] | None = None) -> List[str]:
    roles: List[str] = []
    for frame in (source_frame or {}, target_frame or {}):
        if not isinstance(frame, dict):
            continue
        for role in (
            "selector",
            "real_substrate_geometry",
            "operator_apparatus",
            "closure_constraints",
            "readout_current",
            "protocol_order",
        ):
            if frame.get(role) and role not in roles:
                roles.append(role)
    return roles


def is_usable_node(node: Dict[str, Any]) -> bool:
    if node.get("pair_status") not in USABLE_PAIR_STATUSES:
        return False
    if not node.get("formula_core"):
        return False
    if tuple(node.get("route_signature") or []) == ("route_sparse",):
        return False
    return True


def is_case_relevant_node(node: Dict[str, Any]) -> bool:
    case = node.get("case_evidence") or {}
    return is_usable_node(node) and bool(case.get("case_relevant"))


def has_local_case_mechanism(node: Dict[str, Any]) -> bool:
    case = node.get("case_evidence") or {}
    local = set(case.get("local_categories") or [])
    return "black_hole" in local and bool(local & LOCAL_MECHANISM_CASE_CATEGORIES)


def is_evidence_grade_case_node(node: Dict[str, Any]) -> bool:
    return (
        is_case_relevant_node(node)
        and has_local_case_mechanism(node)
        and int(node.get("formula_detail_score") or 0) >= 4
    )


def is_direct_safety_case_node(node: Dict[str, Any]) -> bool:
    case = node.get("case_evidence") or {}
    return is_evidence_grade_case_node(node) and bool(case.get("direct_safety_case"))


def is_astrophysical_analogue_node(node: Dict[str, Any]) -> bool:
    case = node.get("case_evidence") or {}
    return is_evidence_grade_case_node(node) and bool(case.get("astrophysical_analogue"))


def is_production_threshold_node(node: Dict[str, Any]) -> bool:
    case = node.get("case_evidence") or {}
    return is_evidence_grade_case_node(node) and "production_threshold_branch" in set(case.get("branch_labels") or [])


def is_rich_signature(signature: Tuple[str, ...]) -> bool:
    if signature == ("route_sparse",):
        return False
    return len(signature) >= RICH_ANALOGUE_MIN_ACTIVE_ROUTES


def build_equation_mechanism_graph(out_dir: Path) -> Dict[str, Any]:
    witnesses = read_json(out_dir / "equation_witnesses.json").get("witnesses", [])
    case_text_by_source = source_case_texts(out_dir)
    nodes: List[Dict[str, Any]] = []
    skipped = Counter()

    for index, witness in enumerate(witnesses):
        fp = witness.get("fingerprint") or {}
        if not fingerprint_available(witness):
            skipped["no_hyperion_fingerprint"] += 1
            continue
        routes = supplemented_route_profile(fp, str(witness.get("formula") or ""))
        signature = route_signature(routes)
        node = {
            "id": f"E{index:05d}",
            "source_id": witness.get("source_id"),
            "formula": witness.get("formula"),
            "formula_core": is_formula_core(witness.get("formula")),
            "formula_quality_flags": formula_quality_flags(witness.get("formula")),
            "context": witness.get("context"),
            "text_role": witness.get("dominant_role"),
            "route_profile": routes,
            "route_signature": list(signature),
            "pair_status": pair_status(fp),
            "constructor_roles": constructor_roles(fp),
            "transition_labels": fp.get("transition_labels") or [],
            "route_role_interactions": fp.get("route_role_interactions") or [],
            "source_frame_audit": fp.get("source_frame_audit") or {},
            "target_frame_audit": fp.get("target_frame_audit") or {},
            "case_evidence": case_evidence(
                witness.get("formula"),
                witness.get("context"),
                witness.get("source_id"),
                case_text_by_source.get(str(witness.get("source_id")), ""),
            ),
            "formula_detail_score": formula_detail_score(
                witness.get("formula"),
                routes,
                constructor_roles(fp),
            ),
            "vector_nonzero": fp.get("vector_nonzero"),
            "vector_l1": fp.get("vector_l1"),
        }
        nodes.append(node)

    usable_nodes = [node for node in nodes if is_usable_node(node)]
    case_nodes = [node for node in usable_nodes if is_case_relevant_node(node)]
    evidence_grade_case_nodes = [node for node in case_nodes if is_evidence_grade_case_node(node)]
    direct_safety_case_nodes = [node for node in evidence_grade_case_nodes if is_direct_safety_case_node(node)]
    astrophysical_analogue_nodes = [node for node in evidence_grade_case_nodes if is_astrophysical_analogue_node(node)]
    production_threshold_nodes = [node for node in evidence_grade_case_nodes if is_production_threshold_node(node)]
    artifact_nodes = [node for node in nodes if node.get("pair_status") not in USABLE_PAIR_STATUSES or not node.get("formula_core")]
    formula_quality_counts = Counter(flag for node in nodes for flag in (node.get("formula_quality_flags") or []))
    case_category_counts = Counter(category for node in case_nodes for category in ((node.get("case_evidence") or {}).get("categories") or []))
    case_branch_counts = Counter(label for node in evidence_grade_case_nodes for label in ((node.get("case_evidence") or {}).get("branch_labels") or []))

    role_counts = Counter(node.get("text_role") for node in usable_nodes)
    route_counts = Counter()
    route_counts_all = Counter()
    signature_counts = Counter(tuple(node["route_signature"]) for node in usable_nodes)
    status_counts = Counter(node["pair_status"] for node in nodes)
    constructor_role_counts = Counter()
    transition_counts = Counter()
    for node in nodes:
        for route, score in node["route_profile"].items():
            if score >= 0.12:
                route_counts_all[route] += 1
    for node in usable_nodes:
        for route, score in node["route_profile"].items():
            if score >= 0.12:
                route_counts[route] += 1
        for role in node.get("constructor_roles") or []:
            constructor_role_counts[role] += 1
        for label in node.get("transition_labels") or []:
            transition_counts[label] += 1

    edges: List[Dict[str, Any]] = []
    by_source: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for node in usable_nodes:
        by_source[str(node.get("source_id"))].append(node)
    for source_id, source_nodes in by_source.items():
        for left, right in zip(source_nodes, source_nodes[1:]):
            overlap = sorted(set(left["route_signature"]) & set(right["route_signature"]))
            cosine = route_cosine(left["route_profile"], right["route_profile"])
            if overlap or cosine >= 0.5:
                edges.append({
                    "source": left["id"],
                    "target": right["id"],
                    "source_id": source_id,
                    "edge_type": "source_local_route_transition",
                    "route_overlap": overlap,
                    "route_cosine": cosine,
                    "left_signature": left["route_signature"],
                    "right_signature": right["route_signature"],
                })

    analog_edges: List[Dict[str, Any]] = []
    buckets: Dict[Tuple[str, ...], List[Dict[str, Any]]] = defaultdict(list)
    for node in usable_nodes:
        buckets[tuple(node["route_signature"])].append(node)
    for signature, bucket in buckets.items():
        if not is_rich_signature(signature) or len(bucket) < 2:
            continue
        by_distinct_source: Dict[str, Dict[str, Any]] = {}
        for node in bucket:
            sid = str(node.get("source_id"))
            if sid not in by_distinct_source:
                by_distinct_source[sid] = node
        representatives = list(by_distinct_source.values())[:8]
        for i, left in enumerate(representatives):
            for right in representatives[i + 1:]:
                cosine = route_cosine(left["route_profile"], right["route_profile"])
                if cosine >= 0.85:
                    analog_edges.append({
                        "source": left["id"],
                        "target": right["id"],
                        "edge_type": "cross_source_route_analogue",
                        "route_signature": list(signature),
                        "route_cosine": cosine,
                        "left_source_id": left.get("source_id"),
                        "right_source_id": right.get("source_id"),
                    })

    node_by_id = {node["id"]: node for node in nodes}
    case_source_local_edges: List[Dict[str, Any]] = []
    for edge in edges:
        left = node_by_id.get(str(edge.get("source")))
        right = node_by_id.get(str(edge.get("target")))
        if left and right and (is_case_relevant_node(left) or is_case_relevant_node(right)):
            case_source_local_edges.append(edge)

    case_internal_analog_edges: List[Dict[str, Any]] = []
    case_transfer_analog_edges: List[Dict[str, Any]] = []
    evidence_grade_case_internal_analog_edges: List[Dict[str, Any]] = []
    evidence_grade_case_transfer_analog_edges: List[Dict[str, Any]] = []
    for edge in analog_edges:
        left = node_by_id.get(str(edge.get("source")))
        right = node_by_id.get(str(edge.get("target")))
        if not left or not right:
            continue
        left_case = is_case_relevant_node(left)
        right_case = is_case_relevant_node(right)
        if left_case and right_case:
            case_internal_analog_edges.append(edge)
        elif left_case or right_case:
            case_transfer_analog_edges.append(edge)
        left_evidence_case = is_evidence_grade_case_node(left)
        right_evidence_case = is_evidence_grade_case_node(right)
        if left_evidence_case and right_evidence_case:
            evidence_grade_case_internal_analog_edges.append(edge)
        elif left_evidence_case or right_evidence_case:
            evidence_grade_case_transfer_analog_edges.append(edge)

    graph = {
        "report_type": "lhc_equation_mechanism_graph",
        "readiness": "usable" if nodes else "no_hyperion_fingerprints",
        "source_witness_count": len(witnesses),
        "fingerprinted_node_count": len(nodes),
        "usable_mechanism_node_count": len(usable_nodes),
        "case_relevant_mechanism_node_count": len(case_nodes),
        "evidence_grade_case_mechanism_node_count": len(evidence_grade_case_nodes),
        "direct_lhc_safety_mechanism_node_count": len(direct_safety_case_nodes),
        "astrophysical_analogue_mechanism_node_count": len(astrophysical_analogue_nodes),
        "production_threshold_mechanism_node_count": len(production_threshold_nodes),
        "artifact_or_unusable_node_count": len(artifact_nodes),
        "skipped": dict(skipped),
        "route_counts": dict(route_counts),
        "route_counts_all_fingerprinted": dict(route_counts_all),
        "route_signature_counts": {" + ".join(k): v for k, v in signature_counts.most_common()},
        "text_role_counts": {str(k): v for k, v in role_counts.most_common()},
        "pair_status_counts": dict(status_counts),
        "constructor_role_counts": dict(constructor_role_counts),
        "transition_label_counts": dict(transition_counts.most_common(40)),
        "formula_quality_counts": dict(formula_quality_counts.most_common()),
        "case_category_counts": dict(case_category_counts.most_common()),
        "case_branch_counts": dict(case_branch_counts.most_common()),
        "nodes": nodes,
        "usable_node_ids": [node["id"] for node in usable_nodes],
        "case_relevant_node_ids": [node["id"] for node in case_nodes],
        "evidence_grade_case_node_ids": [node["id"] for node in evidence_grade_case_nodes],
        "direct_lhc_safety_node_ids": [node["id"] for node in direct_safety_case_nodes],
        "astrophysical_analogue_node_ids": [node["id"] for node in astrophysical_analogue_nodes],
        "production_threshold_node_ids": [node["id"] for node in production_threshold_nodes],
        "edges": edges,
        "case_source_local_edges": case_source_local_edges,
        "analog_edges": analog_edges,
        "case_internal_analog_edges": case_internal_analog_edges,
        "case_transfer_analog_edges": case_transfer_analog_edges,
        "evidence_grade_case_internal_analog_edges": evidence_grade_case_internal_analog_edges,
        "evidence_grade_case_transfer_analog_edges": evidence_grade_case_transfer_analog_edges,
        "claim_scope": (
            "Hyperion-style equation mechanism graph built from operator/substrate fingerprints stored on equation witnesses. "
            "Text labels are retained as weak human-readable annotations, but route profiles and constructor frames are the mechanism evidence."
        ),
    }
    (out_dir / "equation_mechanism_graph.json").write_text(json.dumps(graph, indent=2, ensure_ascii=False), encoding="utf-8")
    (out_dir / "equation_mechanism_graph.md").write_text(render_equation_mechanism_report(graph), encoding="utf-8")
    return graph


def sorted_example_nodes(nodes: Iterable[Dict[str, Any]], case_first: bool = False) -> List[Dict[str, Any]]:
    return sorted(
        list(nodes),
        key=lambda n: (
            int(n.get("formula_detail_score") or 0),
            int((n.get("case_evidence") or {}).get("score") or 0) if case_first else 0,
            1 if n.get("pair_status") == "complete_constructor_pair" else 0,
            len(n.get("constructor_roles") or []),
            sum(float(v) for v in (n.get("route_profile") or {}).values()),
            int(n.get("vector_nonzero") or 0),
        ),
        reverse=True,
    )


def append_node_examples(lines: List[str], nodes: Iterable[Dict[str, Any]], limit: int = 12, include_case: bool = False) -> None:
    examples = sorted_example_nodes(nodes, case_first=include_case)
    if not examples:
        lines.append("No examples passed this gate.")
        lines.append("")
        return
    for node in examples[:limit]:
        routes = ", ".join(f"{k}={float(v):.2f}" for k, v in (node.get("route_profile") or {}).items())
        lines.append(f"### `{node.get('source_id')}` / `{node.get('id')}`")
        lines.append("")
        lines.append(f"- route signature: `{' + '.join(node.get('route_signature') or [])}`")
        lines.append(f"- route evidence: {routes or '`none`'}")
        lines.append(f"- constructor roles: `{', '.join(node.get('constructor_roles') or []) or 'none'}`")
        lines.append(f"- pair status: `{node.get('pair_status')}`")
        if include_case:
            case = node.get("case_evidence") or {}
            lines.append(f"- case score: `{case.get('score', 0)}`")
            lines.append(f"- formula-window case categories: `{', '.join(case.get('local_categories') or []) or 'none'}`")
            lines.append(f"- source case categories: `{', '.join(case.get('source_categories') or []) or 'none'}`")
            lines.append(f"- branch labels: `{', '.join(case.get('branch_labels') or []) or 'none'}`")
            lines.append(f"- formula detail score: `{node.get('formula_detail_score', 0)}`")
        lines.append("")
        lines.append("Formula:")
        lines.append("")
        lines.append("```text")
        lines.append(compact(node.get("formula"), 420))
        lines.append("```")
        lines.append("")
    if len(examples) > limit:
        lines.append(f"- ... `{len(examples) - limit}` additional examples omitted.")
        lines.append("")


def render_equation_mechanism_report(graph: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append("# Equation Mechanism Graph")
    lines.append("")
    lines.append("This report uses Hyperion operator/substrate fingerprints, not claim provenance, as the primary evidence layer.")
    lines.append("Text role labels are retained only as weak annotations.")
    lines.append("")
    lines.append("## Scale")
    lines.append("")
    lines.append(f"- source equation witnesses: `{graph.get('source_witness_count')}`")
    lines.append(f"- fingerprinted mechanism nodes: `{graph.get('fingerprinted_node_count')}`")
    lines.append(f"- usable non-artifact mechanism nodes: `{graph.get('usable_mechanism_node_count')}`")
    lines.append(f"- LHC-black-hole case-relevant mechanism nodes: `{graph.get('case_relevant_mechanism_node_count')}`")
    lines.append(f"- evidence-grade case mechanism nodes: `{graph.get('evidence_grade_case_mechanism_node_count')}`")
    lines.append(f"- direct LHC-safety mechanism nodes: `{graph.get('direct_lhc_safety_mechanism_node_count')}`")
    lines.append(f"- astrophysical analogue mechanism nodes: `{graph.get('astrophysical_analogue_mechanism_node_count')}`")
    lines.append(f"- collider-threshold/selection mechanism nodes: `{graph.get('production_threshold_mechanism_node_count')}`")
    lines.append(f"- artifact or unusable nodes retained for audit: `{graph.get('artifact_or_unusable_node_count')}`")
    lines.append(f"- source-local route-transition edges: `{len(graph.get('edges', []))}`")
    lines.append(f"- case-relevant source-local route-transition edges: `{len(graph.get('case_source_local_edges', []))}`")
    lines.append(f"- rich cross-source route analogues: `{len(graph.get('analog_edges', []))}`")
    lines.append(f"- case-internal rich analogues: `{len(graph.get('case_internal_analog_edges', []))}`")
    lines.append(f"- case-transfer rich analogues: `{len(graph.get('case_transfer_analog_edges', []))}`")
    lines.append(f"- evidence-grade case-internal rich analogues: `{len(graph.get('evidence_grade_case_internal_analog_edges', []))}`")
    lines.append(f"- evidence-grade case-transfer rich analogues: `{len(graph.get('evidence_grade_case_transfer_analog_edges', []))}`")
    lines.append("")
    lines.append("## Main Finding")
    lines.append("")
    lines.append(
        "This corpus does not contain formula-clean direct LHC-safety mechanisms under the current gates. "
        "It contains one collider-threshold/selection hook and a larger set of astrophysical black-hole mechanisms. "
        "The evidence therefore supports a mechanism-translation audit: use accretion, evaporation, capture, mass-growth "
        "and compact-object survival mechanisms as constraints on the collider branch, rather than treating the problem "
        "as a provenance dispute over who said safe or dangerous."
    )
    lines.append("")
    lines.append("## Six-Route Evidence")
    lines.append("")
    lines.append("Counts below use only non-artifact constructor pairs.")
    lines.append("")
    for route, count in Counter(graph.get("route_counts") or {}).most_common():
        lines.append(f"- `{route}`: `{count}` nodes — {ROUTE_EXPLANATIONS.get(route, 'route evidence')}.")
    lines.append("")
    lines.append("## Dominant Route Signatures")
    lines.append("")
    for signature, count in list((graph.get("route_signature_counts") or {}).items())[:12]:
        lines.append(f"- `{signature}`: `{count}`")
    lines.append("")
    lines.append("## Case-Relevant Mechanism Evidence")
    lines.append("")
    lines.append(
        "This gate asks whether a formula-clean mechanism node is locally attached to the LHC black-hole safety case. "
        "Source-level words can support relevance, but they do not create route evidence."
    )
    lines.append(
        "Evidence-grade receipts require the formula window itself to contain the black-hole case and a mechanism category; "
        "source-level relevance alone is not enough."
    )
    lines.append("")
    for category, count in Counter(graph.get("case_category_counts") or {}).most_common():
        lines.append(f"- `{category}`: `{count}`")
    if not graph.get("case_category_counts"):
        lines.append("- No formula-clean mechanism nodes passed the LHC black-hole case gate.")
    lines.append("")
    lines.append("Evidence-grade branch counts:")
    lines.append("")
    for branch, count in Counter(graph.get("case_branch_counts") or {}).most_common():
        lines.append(f"- `{branch}`: `{count}`")
    if not graph.get("case_branch_counts"):
        lines.append("- No evidence-grade case branches were found.")
    lines.append("")
    lines.append("Interpretation:")
    lines.append("")
    lines.append(
        "If direct LHC-safety receipts are sparse while astrophysical black-hole analogues are present, "
        "the result should not be read as a failure of the mechanism graph. It means the inspectable scientific "
        "substrate is mostly adjacent physics: accretion, evaporation, capture, mass growth and astrophysical "
        "survival bounds. The safety argument must therefore be audited by translating those mechanisms into the "
        "collider branch, rather than by counting who asserted safety or danger."
    )
    lines.append(
        "Collider-threshold/selection candidates are separated because they can show where a collider event selection or "
        "formation condition enters the case, but they are not by themselves accretion, evaporation or safety mechanisms."
    )
    lines.append("")
    lines.append("## Constructor Frame Quality")
    lines.append("")
    for status, count in Counter(graph.get("pair_status_counts") or {}).most_common():
        lines.append(f"- `{status}`: `{count}`")
    lines.append("")
    lines.append("## Formula-Core Quality")
    lines.append("")
    for flag, count in Counter(graph.get("formula_quality_counts") or {}).most_common():
        lines.append(f"- `{flag}`: `{count}`")
    lines.append("")
    lines.append("## Constructor Roles Present")
    lines.append("")
    for role, count in Counter(graph.get("constructor_role_counts") or {}).most_common():
        lines.append(f"- `{role}`: `{count}`")
    lines.append("")
    lines.append("## Frequent Transition Labels")
    lines.append("")
    for label, count in list((graph.get("transition_label_counts") or {}).items())[:20]:
        lines.append(f"- `{label}`: `{count}`")
    lines.append("")
    lines.append("## Global Cross-Source Route Analogues")
    lines.append("")
    lines.append("These route analogues are formula-clean but not necessarily LHC-case-specific.")
    lines.append("")
    analog_edges = graph.get("analog_edges") or []
    if not analog_edges:
        lines.append("No high-cosine rich cross-source route analogues were found under the current threshold.")
    for edge in analog_edges[:20]:
        lines.append(
            f"- `{edge.get('left_source_id')}` -> `{edge.get('right_source_id')}`: "
            f"`{' + '.join(edge.get('route_signature') or [])}`, cosine `{float(edge.get('route_cosine', 0.0)):.3f}`"
        )
    if len(analog_edges) > 20:
        lines.append(f"- ... `{len(analog_edges) - 20}` additional cross-source analogues omitted.")
    lines.append("")
    lines.append("## Case-Relevant Cross-Source Route Analogues")
    lines.append("")
    case_internal = graph.get("evidence_grade_case_internal_analog_edges") or []
    case_transfer = graph.get("evidence_grade_case_transfer_analog_edges") or []
    if not case_internal and not case_transfer:
        lines.append("No high-cosine evidence-grade case route analogues were found under the current threshold.")
    if case_internal:
        lines.append("Internal to the LHC black-hole case:")
        lines.append("")
        for edge in case_internal[:12]:
            lines.append(
                f"- `{edge.get('left_source_id')}` -> `{edge.get('right_source_id')}`: "
                f"`{' + '.join(edge.get('route_signature') or [])}`, cosine `{float(edge.get('route_cosine', 0.0)):.3f}`"
            )
        lines.append("")
    if case_transfer:
        lines.append("Transfer analogues from the case to other formula-clean sources:")
        lines.append("")
        for edge in case_transfer[:12]:
            lines.append(
                f"- `{edge.get('left_source_id')}` -> `{edge.get('right_source_id')}`: "
                f"`{' + '.join(edge.get('route_signature') or [])}`, cosine `{float(edge.get('route_cosine', 0.0)):.3f}`"
            )
        lines.append("")
    lines.append("## Case-Relevant Mechanism Examples")
    lines.append("")
    nodes = graph.get("nodes") or []
    direct_ids = set(graph.get("direct_lhc_safety_node_ids") or [])
    analogue_ids = set(graph.get("astrophysical_analogue_node_ids") or [])
    lines.append("### Direct LHC-Safety Receipts")
    lines.append("")
    if direct_ids:
        append_node_examples(lines, [node for node in nodes if node.get("id") in direct_ids], limit=8, include_case=True)
    else:
        lines.append("No formula-clean direct LHC-safety mechanism passed the current gate.")
        lines.append("This is the substantive result: the selected corpus supports an indirect mechanism audit through adjacent black-hole physics.")
        lines.append("")
    production_ids = set(graph.get("production_threshold_node_ids") or [])
    lines.append("### Collider-Threshold/Selection Candidates")
    lines.append("")
    append_node_examples(lines, [node for node in nodes if node.get("id") in (production_ids - direct_ids)], limit=8, include_case=True)
    lines.append("### Astrophysical Black-Hole Analogues")
    lines.append("")
    append_node_examples(lines, [node for node in nodes if node.get("id") in analogue_ids], limit=8, include_case=True)
    lines.append("### Other Evidence-Grade Case Nodes")
    lines.append("")
    evidence_case_ids = set(graph.get("evidence_grade_case_node_ids") or [])
    used_case_ids = direct_ids | production_ids | analogue_ids
    remaining_evidence_case_ids = evidence_case_ids - used_case_ids
    if evidence_case_ids:
        append_node_examples(lines, [node for node in nodes if node.get("id") in remaining_evidence_case_ids], limit=8, include_case=True)
    else:
        case_ids = set(graph.get("case_relevant_node_ids") or [])
        append_node_examples(lines, [node for node in nodes if node.get("id") in case_ids], include_case=True)
    lines.append("## Global Mechanism Examples")
    lines.append("")
    lines.append("These are formula-clean global examples from the operational graph, not LHC-specific receipts.")
    lines.append("")
    usable_ids = set(graph.get("usable_node_ids") or [])
    append_node_examples(lines, [node for node in nodes if node.get("id") in usable_ids])
    lines.append("## Boundary")
    lines.append("")
    lines.append("This graph does not prove physical equivalence. It separates equation-level mechanism evidence from provenance and word-level selection, making route analogies inspectable.")
    return "\n".join(lines).rstrip() + "\n"
