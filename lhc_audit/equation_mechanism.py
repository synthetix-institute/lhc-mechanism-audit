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


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def compact(text: Any, limit: int = 360) -> str:
    value = " ".join(str(text or "").split())
    return value if len(value) <= limit else value[: limit - 3] + "..."


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


def build_equation_mechanism_graph(out_dir: Path) -> Dict[str, Any]:
    witnesses = read_json(out_dir / "equation_witnesses.json").get("witnesses", [])
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
            "vector_nonzero": fp.get("vector_nonzero"),
            "vector_l1": fp.get("vector_l1"),
        }
        nodes.append(node)

    role_counts = Counter(node.get("text_role") for node in nodes)
    route_counts = Counter()
    signature_counts = Counter(tuple(node["route_signature"]) for node in nodes)
    status_counts = Counter(node["pair_status"] for node in nodes)
    constructor_role_counts = Counter()
    transition_counts = Counter()
    for node in nodes:
        for route, score in node["route_profile"].items():
            if score >= 0.12:
                route_counts[route] += 1
        for role in node.get("constructor_roles") or []:
            constructor_role_counts[role] += 1
        for label in node.get("transition_labels") or []:
            transition_counts[label] += 1

    edges: List[Dict[str, Any]] = []
    by_source: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for node in nodes:
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
    for node in nodes:
        buckets[tuple(node["route_signature"])].append(node)
    for signature, bucket in buckets.items():
        if signature == ("route_sparse",) or len(bucket) < 2:
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

    graph = {
        "report_type": "lhc_equation_mechanism_graph",
        "readiness": "usable" if nodes else "no_hyperion_fingerprints",
        "source_witness_count": len(witnesses),
        "fingerprinted_node_count": len(nodes),
        "skipped": dict(skipped),
        "route_counts": dict(route_counts),
        "route_signature_counts": {" + ".join(k): v for k, v in signature_counts.most_common()},
        "text_role_counts": {str(k): v for k, v in role_counts.most_common()},
        "pair_status_counts": dict(status_counts),
        "constructor_role_counts": dict(constructor_role_counts),
        "transition_label_counts": dict(transition_counts.most_common(40)),
        "nodes": nodes,
        "edges": edges,
        "analog_edges": analog_edges,
        "claim_scope": (
            "Hyperion-style equation mechanism graph built from operator/substrate fingerprints stored on equation witnesses. "
            "Text labels are retained as weak human-readable annotations, but route profiles and constructor frames are the mechanism evidence."
        ),
    }
    (out_dir / "equation_mechanism_graph.json").write_text(json.dumps(graph, indent=2, ensure_ascii=False), encoding="utf-8")
    (out_dir / "equation_mechanism_graph.md").write_text(render_equation_mechanism_report(graph), encoding="utf-8")
    return graph


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
    lines.append(f"- source-local route-transition edges: `{len(graph.get('edges', []))}`")
    lines.append(f"- cross-source route analogues: `{len(graph.get('analog_edges', []))}`")
    lines.append("")
    lines.append("## Six-Route Evidence")
    lines.append("")
    for route, count in Counter(graph.get("route_counts") or {}).most_common():
        lines.append(f"- `{route}`: `{count}` nodes — {ROUTE_EXPLANATIONS.get(route, 'route evidence')}.")
    lines.append("")
    lines.append("## Dominant Route Signatures")
    lines.append("")
    for signature, count in list((graph.get("route_signature_counts") or {}).items())[:12]:
        lines.append(f"- `{signature}`: `{count}`")
    lines.append("")
    lines.append("## Constructor Frame Quality")
    lines.append("")
    for status, count in Counter(graph.get("pair_status_counts") or {}).most_common():
        lines.append(f"- `{status}`: `{count}`")
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
    lines.append("## Cross-Source Route Analogues")
    lines.append("")
    analog_edges = graph.get("analog_edges") or []
    if not analog_edges:
        lines.append("No high-cosine cross-source route analogues were found under the current threshold.")
    for edge in analog_edges[:20]:
        lines.append(
            f"- `{edge.get('left_source_id')}` -> `{edge.get('right_source_id')}`: "
            f"`{' + '.join(edge.get('route_signature') or [])}`, cosine `{float(edge.get('route_cosine', 0.0)):.3f}`"
        )
    if len(analog_edges) > 20:
        lines.append(f"- ... `{len(analog_edges) - 20}` additional cross-source analogues omitted.")
    lines.append("")
    lines.append("## Mechanism Examples")
    lines.append("")
    examples = sorted(
        graph.get("nodes") or [],
        key=lambda n: (
            len(n.get("constructor_roles") or []),
            sum(float(v) for v in (n.get("route_profile") or {}).values()),
            int(n.get("vector_nonzero") or 0),
        ),
        reverse=True,
    )
    for node in examples[:12]:
        routes = ", ".join(f"{k}={float(v):.2f}" for k, v in (node.get("route_profile") or {}).items())
        lines.append(f"### `{node.get('source_id')}` / `{node.get('id')}`")
        lines.append("")
        lines.append(f"- route signature: `{' + '.join(node.get('route_signature') or [])}`")
        lines.append(f"- route evidence: {routes or '`none`'}")
        lines.append(f"- constructor roles: `{', '.join(node.get('constructor_roles') or []) or 'none'}`")
        lines.append(f"- pair status: `{node.get('pair_status')}`")
        lines.append("")
        lines.append("Formula:")
        lines.append("")
        lines.append("```text")
        lines.append(compact(node.get("formula"), 420))
        lines.append("```")
        lines.append("")
    lines.append("## Boundary")
    lines.append("")
    lines.append("This graph does not prove physical equivalence. It separates equation-level mechanism evidence from provenance and word-level selection, making route analogies inspectable.")
    return "\n".join(lines).rstrip() + "\n"
