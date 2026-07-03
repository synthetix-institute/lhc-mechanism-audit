#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


ROUTES = [
    "transport_flow",
    "constraint_closure",
    "spectral_operator",
    "boundary_weak_form",
    "commutator_incompatibility",
    "discrete_protocol",
]

CASE_BRANCHES = [
    "direct_lhc_safety",
    "production_threshold_branch",
    "astrophysical_black_hole_analogue",
    "stable_growth_or_capture_branch",
    "evaporation_branch",
]


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def active_routes(node: Dict[str, Any], threshold: float = 0.12) -> List[str]:
    profile = node.get("route_profile") or {}
    out: List[str] = []
    for route in ROUTES:
        try:
            if float(profile.get(route, 0.0)) >= threshold:
                out.append(route)
        except Exception:
            continue
    return out


def load_graph(out_dir: Path) -> Dict[str, Any]:
    graph_path = out_dir / "equation_mechanism_graph.json"
    if not graph_path.exists():
        raise FileNotFoundError(f"Missing {graph_path}. Build the equation mechanism graph first.")
    return read_json(graph_path)


def normalized(counter: Counter[str]) -> Dict[str, float]:
    total = sum(counter.values())
    if total <= 0:
        return {}
    return {key: value / total for key, value in counter.most_common()}


def top_pairs(counter: Counter[Tuple[str, str]], limit: int = 24) -> List[Dict[str, Any]]:
    return [
        {"left": left, "right": right, "count": count}
        for (left, right), count in counter.most_common(limit)
    ]


def build_sparse_attention(graph: Dict[str, Any]) -> Dict[str, Any]:
    nodes = graph.get("nodes") or []
    evidence_ids = set(graph.get("evidence_grade_case_node_ids") or [])
    usable_ids = set(graph.get("usable_node_ids") or [])

    evidence_nodes = [node for node in nodes if node.get("id") in evidence_ids]
    usable_nodes = [node for node in nodes if node.get("id") in usable_ids]

    branch_route: Dict[str, Counter[str]] = defaultdict(Counter)
    category_route: Dict[str, Counter[str]] = defaultdict(Counter)
    route_route: Counter[Tuple[str, str]] = Counter()
    branch_counts: Counter[str] = Counter()
    category_counts: Counter[str] = Counter()

    for node in evidence_nodes:
        routes = active_routes(node)
        case = node.get("case_evidence") or {}
        branches = list(case.get("branch_labels") or [])
        categories = list(case.get("local_categories") or [])
        if not branches:
            branches = ["unassigned_case_branch"]
        for branch in branches:
            branch_counts[branch] += 1
            for route in routes:
                branch_route[branch][route] += 1
        for category in categories:
            category_counts[category] += 1
            for route in routes:
                category_route[category][route] += 1
        for i, left in enumerate(routes):
            for right in routes[i + 1 :]:
                route_route[tuple(sorted((left, right)))] += 1

    usable_route_counts = Counter(route for node in usable_nodes for route in active_routes(node))
    evidence_route_counts = Counter(route for node in evidence_nodes for route in active_routes(node))

    direct_count = int(graph.get("direct_lhc_safety_mechanism_node_count") or 0)
    analogue_count = int(graph.get("astrophysical_analogue_mechanism_node_count") or 0)
    threshold_count = int(graph.get("production_threshold_mechanism_node_count") or 0)

    findings: List[str] = []
    if direct_count == 0 and analogue_count > 0:
        findings.append(
            "Sparse attention supports the main audit finding: direct collider-safety mechanisms are absent under the strict gate, while adjacent astrophysical black-hole mechanisms are present."
        )
    if threshold_count > 0:
        findings.append(
            "Collider-threshold evidence appears as a separate branch from accretion, evaporation and capture mechanisms."
        )
    if evidence_route_counts:
        top_routes = ", ".join(f"{route} ({count})" for route, count in evidence_route_counts.most_common(3))
        findings.append(f"Evidence-grade case nodes concentrate on {top_routes}, consistent with mechanism translation rather than claim provenance.")
    if branch_route.get("astrophysical_black_hole_analogue"):
        branch_top = ", ".join(
            f"{route} ({count})"
            for route, count in branch_route["astrophysical_black_hole_analogue"].most_common(4)
        )
        findings.append(f"Astrophysical analogues are routed mainly through {branch_top}.")

    return {
        "report_type": "lhc_sparse_attention_audit",
        "readiness": "usable",
        "node_scope": "static equation_mechanism_graph.json",
        "usable_node_count": len(usable_nodes),
        "evidence_grade_case_node_count": len(evidence_nodes),
        "usable_route_counts": dict(usable_route_counts.most_common()),
        "evidence_route_counts": dict(evidence_route_counts.most_common()),
        "case_branch_counts": dict(branch_counts.most_common()),
        "case_category_counts": dict(category_counts.most_common()),
        "branch_route_attention": {branch: normalized(counts) for branch, counts in branch_route.items()},
        "category_route_attention": {category: normalized(counts) for category, counts in category_route.items()},
        "route_route_coattention": top_pairs(route_route),
        "findings": findings,
        "claim_scope": (
            "This is a sparse co-activation audit over static public graph artifacts. "
            "It supports report interpretation; it does not create new Hyperion fingerprints or claim physical equivalence."
        ),
    }


def render_markdown(audit: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append("# Sparse Attention Audit")
    lines.append("")
    lines.append("This audit reads the static equation mechanism graph and measures which mechanism routes co-activate in the LHC black-hole case layer.")
    lines.append("")
    lines.append("## Scale")
    lines.append("")
    lines.append(f"- usable mechanism nodes: `{audit.get('usable_node_count')}`")
    lines.append(f"- evidence-grade case nodes: `{audit.get('evidence_grade_case_node_count')}`")
    lines.append("")
    lines.append("## Findings")
    lines.append("")
    for finding in audit.get("findings") or []:
        lines.append(f"- {finding}")
    if not audit.get("findings"):
        lines.append("- No sparse-attention finding passed the current gate.")
    lines.append("")
    lines.append("## Evidence-Grade Route Counts")
    lines.append("")
    for route, count in (audit.get("evidence_route_counts") or {}).items():
        lines.append(f"- `{route}`: `{count}`")
    lines.append("")
    lines.append("## Branch To Route Attention")
    lines.append("")
    for branch, routes in (audit.get("branch_route_attention") or {}).items():
        if not routes:
            continue
        route_text = ", ".join(f"{route}={score:.2f}" for route, score in routes.items())
        lines.append(f"- `{branch}`: {route_text}")
    lines.append("")
    lines.append("## Route Co-Attention")
    lines.append("")
    for pair in audit.get("route_route_coattention") or []:
        lines.append(f"- `{pair['left']}` + `{pair['right']}`: `{pair['count']}`")
    lines.append("")
    lines.append("## Boundary")
    lines.append("")
    lines.append(str(audit.get("claim_scope") or "Static sparse-attention audit."))
    return "\n".join(lines).rstrip() + "\n"


def build(args: argparse.Namespace) -> Dict[str, Any]:
    out_dir = Path(args.out_dir)
    graph = load_graph(out_dir)
    audit = build_sparse_attention(graph)
    json_path = out_dir / "sparse_attention_audit.json"
    md_path = out_dir / "sparse_attention_audit.md"
    json_path.write_text(json.dumps(audit, indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(render_markdown(audit), encoding="utf-8")
    return {"json": str(json_path), "markdown": str(md_path), "readiness": audit["readiness"]}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a static sparse-attention audit from an equation mechanism graph.")
    parser.add_argument("--out-dir", required=True, help="Audit output directory containing equation_mechanism_graph.json")
    return parser


def main() -> None:
    print(json.dumps(build(build_parser().parse_args()), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
