from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


BRANCH_LABELS = {
    "production_threshold_branch": "production threshold",
    "evaporation_branch": "evaporation or lifetime",
    "stable_growth_or_capture_branch": "stable growth or capture",
    "astrophysical_black_hole_analogue": "astronomical analogue",
}

CLAIM_LABELS = {
    "astrophysical_claim": "astrophysical claims",
    "risk_claim": "risk claims",
    "safety_claim": "safety claims",
    "unknown": "unknown claims",
}


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def compact(text: Any, limit: int = 320) -> str:
    value = " ".join(str(text or "").split())
    return value if len(value) <= limit else value[: limit - 3] + "..."


def node(node_id: str, kind: str, label: str, **attrs: Any) -> Dict[str, Any]:
    return {"id": node_id, "kind": kind, "label": label, **attrs}


def edge(source: str, target: str, relation: str, **attrs: Any) -> Dict[str, Any]:
    return {"source": source, "target": target, "relation": relation, **attrs}


def _receipt_nodes(equation_graph: Dict[str, Any]) -> List[Dict[str, Any]]:
    ids = set(equation_graph.get("evidence_grade_case_node_ids") or [])
    return [item for item in equation_graph.get("nodes") or [] if str(item.get("id")) in ids]


def _constructor_receipt_index(constructor: Dict[str, Any]) -> Dict[str, List[Tuple[str, str]]]:
    out: Dict[str, List[Tuple[str, str]]] = defaultdict(list)
    for slot in constructor.get("slots") or []:
        slot_id = str(slot.get("slot_id"))
        for item in slot.get("direct_receipts") or []:
            out[str(item.get("node_id"))].append((slot_id, "direct_receipt_for_slot"))
        for item in slot.get("transfer_receipts") or []:
            out[str(item.get("node_id"))].append((slot_id, "transfer_receipt_for_slot"))
    return out


def build_public_knowledge_graph(run_dir: Path) -> Dict[str, Any]:
    provenance = read_json(run_dir / "provenance_graph.json")
    equation_graph = read_json(run_dir / "equation_mechanism_graph.json")
    constructor = read_json(run_dir / "physical_constructor.json")

    provenance_nodes = {str(item.get("id")): item for item in provenance.get("nodes") or []}
    claim_nodes = [
        item for item in provenance.get("nodes") or []
        if str(item.get("id", "")).startswith("C")
    ]
    source_nodes = [
        item for item in provenance.get("nodes") or []
        if not str(item.get("id", "")).startswith("C")
    ]
    receipts = _receipt_nodes(equation_graph)
    receipt_ids = {str(item.get("id")) for item in receipts}
    receipt_slot_index = _constructor_receipt_index(constructor)

    kg_nodes: Dict[str, Dict[str, Any]] = {}
    kg_edges: List[Dict[str, Any]] = []

    kg_nodes["case:lhc_black_hole"] = node(
        "case:lhc_black_hole",
        "case",
        "LHC black-hole catastrophe claim",
    )
    kg_nodes["verdict:broken_branch"] = node(
        "verdict:broken_branch",
        "verdict",
        "branch breaks before collider growth",
        branch_verdict=constructor.get("branch_verdict"),
    )

    for source in source_nodes:
        source_id = str(source.get("id"))
        kg_nodes[f"source:{source_id}"] = node(
            f"source:{source_id}",
            "source",
            source_id,
            title=source.get("title") or source_id,
            url=source.get("url") or f"https://arxiv.org/abs/{source_id}",
        )
        kg_edges.append(edge(f"source:{source_id}", "case:lhc_black_hole", "selected_for_case"))

    for claim_type, label in CLAIM_LABELS.items():
        kg_nodes[f"claim_family:{claim_type}"] = node(
            f"claim_family:{claim_type}",
            "claim_family",
            label,
        )
    for claim in claim_nodes:
        claim_id = str(claim.get("id"))
        claim_type = str(claim.get("claim_type") or "unknown")
        source_id = str(claim.get("source_id") or "")
        kg_nodes[f"claim:{claim_id}"] = node(
            f"claim:{claim_id}",
            "claim",
            claim_id,
            claim_type=claim_type,
            text=compact(claim.get("text"), 600),
            source_id=source_id,
        )
        if source_id:
            kg_edges.append(edge(f"source:{source_id}", f"claim:{claim_id}", "makes_claim"))
        kg_edges.append(edge(f"claim:{claim_id}", f"claim_family:{claim_type}", "classified_as"))
        kg_edges.append(edge(f"claim:{claim_id}", "case:lhc_black_hole", "mentions_case_context"))

    for route, count in (equation_graph.get("route_counts") or {}).items():
        kg_nodes[f"route:{route}"] = node(
            f"route:{route}",
            "route",
            str(route).replace("_", " "),
            count=int(count),
        )
    for branch_id, label in BRANCH_LABELS.items():
        kg_nodes[f"branch:{branch_id}"] = node(
            f"branch:{branch_id}",
            "branch",
            label,
            count=int((equation_graph.get("case_branch_counts") or {}).get(branch_id, 0)),
        )
    for slot in constructor.get("slots") or []:
        slot_id = str(slot.get("slot_id"))
        kg_nodes[f"slot:{slot_id}"] = node(
            f"slot:{slot_id}",
            "constructor_slot",
            str(slot.get("label") or slot_id),
            status=slot.get("status"),
            direct_receipt_count=slot.get("direct_receipt_count"),
            transfer_receipt_count=slot.get("transfer_receipt_count"),
            required_condition=slot.get("required_condition"),
        )
        kg_edges.append(edge(f"slot:{slot_id}", "verdict:broken_branch", "contributes_to_verdict", status=slot.get("status")))

    for item in receipts:
        equation_id = str(item.get("id"))
        source_id = str(item.get("source_id") or "")
        case = item.get("case_evidence") or {}
        kg_nodes[f"equation:{equation_id}"] = node(
            f"equation:{equation_id}",
            "equation_receipt",
            equation_id,
            source_id=source_id,
            formula=compact(item.get("formula"), 800),
            context=compact(item.get("context"), 800),
            text_role=item.get("text_role"),
            route_signature=item.get("route_signature") or [],
            constructor_roles=item.get("constructor_roles") or [],
            branch_labels=case.get("branch_labels") or [],
            local_categories=case.get("local_categories") or [],
        )
        if source_id:
            kg_edges.append(edge(f"source:{source_id}", f"equation:{equation_id}", "contains_equation_receipt"))
        for route in item.get("route_signature") or []:
            kg_edges.append(edge(f"equation:{equation_id}", f"route:{route}", "has_route"))
        for branch in case.get("branch_labels") or []:
            kg_edges.append(edge(f"equation:{equation_id}", f"branch:{branch}", "fills_branch"))
        for slot_id, relation in receipt_slot_index.get(equation_id, []):
            kg_edges.append(edge(f"equation:{equation_id}", f"slot:{slot_id}", relation))

    for collection_name in (
        "case_source_local_edges",
        "evidence_grade_case_internal_analog_edges",
        "evidence_grade_case_transfer_analog_edges",
    ):
        for item in equation_graph.get(collection_name) or []:
            left = str(item.get("source"))
            right = str(item.get("target"))
            if left not in receipt_ids or right not in receipt_ids:
                continue
            relation = str(item.get("edge_type") or collection_name)
            kg_edges.append(
                edge(
                    f"equation:{left}",
                    f"equation:{right}",
                    relation,
                    route_signature=item.get("route_signature") or item.get("route_overlap") or [],
                    route_cosine=item.get("route_cosine"),
                )
            )

    claim_family_counts = Counter(
        str(item.get("claim_type") or "unknown")
        for item in claim_nodes
    )
    source_claim_counts = Counter(
        str(edge_item.get("source"))
        for edge_item in provenance.get("edges") or []
    )
    receipt_branch_counts = Counter()
    receipt_route_counts = Counter()
    source_receipt_counts = Counter()
    for item in receipts:
        source_receipt_counts[str(item.get("source_id"))] += 1
        for branch in (item.get("case_evidence") or {}).get("branch_labels") or []:
            receipt_branch_counts[branch] += 1
        for route in item.get("route_signature") or []:
            receipt_route_counts[route] += 1

    return {
        "report_type": "lhc_public_knowledge_graph",
        "readiness": "usable",
        "node_count": len(kg_nodes),
        "edge_count": len(kg_edges),
        "nodes": list(kg_nodes.values()),
        "edges": kg_edges,
        "summary": {
            "sources": len(source_nodes),
            "claims": len(claim_nodes),
            "claim_edges": len(provenance.get("edges") or []),
            "equation_receipts": len(receipts),
            "constructor_slots": len(constructor.get("slots") or []),
            "claim_family_counts": dict(claim_family_counts),
            "receipt_branch_counts": dict(receipt_branch_counts),
            "receipt_route_counts": dict(receipt_route_counts),
            "top_sources_by_claims": source_claim_counts.most_common(12),
            "top_sources_by_receipts": source_receipt_counts.most_common(12),
        },
        "claim_scope": (
            "Public typed graph assembled from static LHC run artifacts. It joins provenance, "
            "claims, equation receipts, route signatures, branch placement and constructor slots."
        ),
    }


def render_markdown(kg: Dict[str, Any]) -> str:
    summary = kg.get("summary") or {}
    lines = [
        "# LHC Public Knowledge Graph",
        "",
        f"- nodes: `{kg.get('node_count')}`",
        f"- edges: `{kg.get('edge_count')}`",
        f"- sources: `{summary.get('sources')}`",
        f"- claims: `{summary.get('claims')}`",
        f"- equation receipts: `{summary.get('equation_receipts')}`",
        f"- constructor slots: `{summary.get('constructor_slots')}`",
        "",
        "## Claim Families",
        "",
    ]
    for key, value in sorted((summary.get("claim_family_counts") or {}).items(), key=lambda x: (-x[1], x[0])):
        lines.append(f"- `{key}`: `{value}`")
    lines += ["", "## Receipt Branches", ""]
    for key, value in sorted((summary.get("receipt_branch_counts") or {}).items(), key=lambda x: (-x[1], x[0])):
        lines.append(f"- `{key}`: `{value}`")
    lines += ["", "## Top Sources By Claims", ""]
    for key, value in summary.get("top_sources_by_claims") or []:
        lines.append(f"- `{key}`: `{value}`")
    lines += ["", "## Top Sources By Equation Receipts", ""]
    for key, value in summary.get("top_sources_by_receipts") or []:
        lines.append(f"- `{key}`: `{value}`")
    return "\n".join(lines).rstrip() + "\n"


def write_public_knowledge_graph(run_dir: Path) -> Dict[str, str]:
    kg = build_public_knowledge_graph(run_dir)
    json_path = run_dir / "public_knowledge_graph.json"
    md_path = run_dir / "public_knowledge_graph.md"
    json_path.write_text(json.dumps(kg, indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(render_markdown(kg), encoding="utf-8")
    return {"json": str(json_path), "markdown": str(md_path), "readiness": "usable"}

