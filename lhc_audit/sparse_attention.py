from __future__ import annotations

import math
from collections import Counter, defaultdict
from typing import Any, Dict, Iterable, List, Sequence, Set, Tuple

from .evidence_contract import SLOT_CONTRACTS, classify_receipt


ROUTES = [
    "transport_flow",
    "constraint_closure",
    "spectral_operator",
    "boundary_weak_form",
    "commutator_incompatibility",
    "discrete_protocol",
]


def active_routes(node: Dict[str, Any], threshold: float = 0.12) -> Set[str]:
    profile = node.get("route_profile") or {}
    return {
        route for route in ROUTES
        if float(profile.get(route, 0.0) or 0.0) >= threshold
    }


def route_cosine(left: Dict[str, Any], right: Dict[str, Any]) -> float:
    lp = left.get("route_profile") or {}
    rp = right.get("route_profile") or {}
    dot = sum(float(lp.get(route, 0.0) or 0.0) * float(rp.get(route, 0.0) or 0.0) for route in ROUTES)
    ln = math.sqrt(sum(float(lp.get(route, 0.0) or 0.0) ** 2 for route in ROUTES))
    rn = math.sqrt(sum(float(rp.get(route, 0.0) or 0.0) ** 2 for route in ROUTES))
    return dot / (ln * rn) if ln > 0.0 and rn > 0.0 else 0.0


def strict_receipt_ids(nodes: Sequence[Dict[str, Any]], usable_ids: Set[str]) -> Tuple[Set[str], Dict[str, List[str]]]:
    receipt_ids: Set[str] = set()
    grades: Dict[str, List[str]] = defaultdict(list)
    for node in nodes:
        node_id = str(node.get("id") or "")
        if node_id not in usable_ids:
            continue
        for slot in SLOT_CONTRACTS:
            grade, _ = classify_receipt(node, slot)
            if grade:
                receipt_ids.add(node_id)
                grades[node_id].append(f"{slot['slot_id']}:{grade}")
    return receipt_ids, dict(grades)


def _edge_key(edge: Dict[str, Any]) -> Tuple[str, str, str]:
    return (
        str(edge.get("source") or ""),
        str(edge.get("target") or ""),
        str(edge.get("edge_type") or "unknown"),
    )


def _graph_edges(graph: Dict[str, Any]) -> List[Dict[str, Any]]:
    seen: Set[Tuple[str, str, str]] = set()
    edges: List[Dict[str, Any]] = []
    for name in ("edges", "analog_edges"):
        for edge in graph.get(name) or []:
            key = _edge_key(edge)
            if key[0] and key[1] and key not in seen:
                seen.add(key)
                edges.append(edge)
    return edges


def _route_idf(nodes: Iterable[Dict[str, Any]]) -> Dict[str, float]:
    rows = list(nodes)
    counts = Counter(route for node in rows for route in active_routes(node))
    n = max(1, len(rows))
    return {route: math.log((n + 1) / (counts.get(route, 0) + 1)) + 1.0 for route in ROUTES}


def _mean(values: Iterable[float], default: float = 0.0) -> float:
    items = list(values)
    return sum(items) / len(items) if items else default


def build_graph_sparse_attention(graph: Dict[str, Any], *, top_k: int = 40) -> Dict[str, Any]:
    nodes = list(graph.get("nodes") or [])
    node_by_id = {str(node.get("id") or ""): node for node in nodes}
    usable_ids = set(str(node_id) for node_id in (graph.get("usable_node_ids") or []))
    usable_nodes = [node for node in nodes if str(node.get("id") or "") in usable_ids]
    receipt_ids, receipt_grades = strict_receipt_ids(nodes, usable_ids)
    all_edges = [
        edge for edge in _graph_edges(graph)
        if str(edge.get("source") or "") in usable_ids and str(edge.get("target") or "") in usable_ids
    ]

    degree: Counter[str] = Counter()
    for edge in all_edges:
        degree[str(edge["source"])] += 1
        degree[str(edge["target"])] += 1

    idf = _route_idf(usable_nodes)
    scored_edges: List[Dict[str, Any]] = []
    for edge in all_edges:
        source_id = str(edge["source"])
        target_id = str(edge["target"])
        if source_id not in receipt_ids and target_id not in receipt_ids:
            continue
        left = node_by_id[source_id]
        right = node_by_id[target_id]
        left_routes = active_routes(left)
        right_routes = active_routes(right)
        shared = left_routes & right_routes
        introduced = right_routes - left_routes
        removed = left_routes - right_routes
        union = left_routes | right_routes
        cosine = float(edge.get("route_cosine") or route_cosine(left, right))
        rarity = _mean((idf[route] for route in union), default=1.0)
        transition_information = _mean((idf[route] for route in introduced | removed), default=0.0)
        hub_penalty = math.sqrt(max(1, degree[source_id]) * max(1, degree[target_id]))
        case_factor = 1.35 if source_id in receipt_ids and target_id in receipt_ids else 1.0
        edge_type_factor = 1.0 if edge.get("edge_type") == "source_local_route_transition" else 0.8
        raw_score = (
            max(0.05, cosine)
            * rarity
            * (1.0 + 0.35 * transition_information)
            * case_factor
            * edge_type_factor
            / hub_penalty
        )
        scored_edges.append({
            "source": source_id,
            "target": target_id,
            "source_paper": left.get("source_id"),
            "target_paper": right.get("source_id"),
            "edge_type": edge.get("edge_type"),
            "route_cosine": cosine,
            "shared_routes": sorted(shared),
            "introduced_routes": sorted(introduced),
            "removed_routes": sorted(removed),
            "hub_penalty": hub_penalty,
            "rarity_weight": rarity,
            "transition_information": transition_information,
            "raw_attention": raw_score,
            "source_receipt_grades": receipt_grades.get(source_id, []),
            "target_receipt_grades": receipt_grades.get(target_id, []),
        })

    total = sum(edge["raw_attention"] for edge in scored_edges)
    for edge in scored_edges:
        edge["attention"] = edge["raw_attention"] / total if total > 0.0 else 0.0
    scored_edges.sort(key=lambda edge: edge["attention"], reverse=True)

    node_attention: Counter[str] = Counter()
    transition_attention: Counter[Tuple[str, str]] = Counter()
    for edge in scored_edges:
        score = float(edge["attention"])
        node_attention[edge["source"]] += score / 2.0
        node_attention[edge["target"]] += score / 2.0
        left_routes = active_routes(node_by_id[edge["source"]]) or {"route_sparse"}
        right_routes = active_routes(node_by_id[edge["target"]]) or {"route_sparse"}
        share = score / max(1, len(left_routes) * len(right_routes))
        for left_route in left_routes:
            for right_route in right_routes:
                transition_attention[(left_route, right_route)] += share

    top_nodes = []
    for node_id, score in node_attention.most_common(top_k):
        node = node_by_id[node_id]
        top_nodes.append({
            "node_id": node_id,
            "source_id": node.get("source_id"),
            "attention": score,
            "routes": sorted(active_routes(node)),
            "receipt_grades": receipt_grades.get(node_id, []),
            "formula": " ".join(str(node.get("formula") or "").split()),
        })

    route_prevalence = Counter(route for node in usable_nodes for route in active_routes(node))
    receipt_route_prevalence = Counter(
        route for node in usable_nodes
        if str(node.get("id") or "") in receipt_ids
        for route in active_routes(node)
    )
    return {
        "report_type": "lhc_graph_sparse_attention",
        "readiness": "usable" if scored_edges else "no_connected_strict_receipts",
        "method": (
            "Edge attention = route similarity x inverse-frequency route weight x transition information "
            "x strict-receipt factor / geometric-mean endpoint degree."
        ),
        "usable_node_count": len(usable_nodes),
        "graph_edge_count": len(all_edges),
        "strict_receipt_node_count": len(receipt_ids),
        "attended_edge_count": len(scored_edges),
        "route_idf": idf,
        "route_prevalence": dict(route_prevalence.most_common()),
        "strict_receipt_route_prevalence": dict(receipt_route_prevalence.most_common()),
        "top_edges": scored_edges[:top_k],
        "top_nodes": top_nodes,
        "route_transition_attention": [
            {"source_route": left, "target_route": right, "attention": score}
            for (left, right), score in transition_attention.most_common(top_k)
        ],
    }
