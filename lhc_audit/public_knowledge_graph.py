from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Tuple


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
    "unknown": "unclassified claims",
}


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def node(node_id: str, kind: str, label: str, **attrs: Any) -> Dict[str, Any]:
    return {"id": node_id, "kind": kind, "label": label, **attrs}


def edge(source: str, target: str, relation: str, **attrs: Any) -> Dict[str, Any]:
    return {"source": source, "target": target, "relation": relation, **attrs}


def _constructor_receipt_index(
    constructor: Dict[str, Any],
) -> Dict[str, List[Tuple[str, str, str]]]:
    out: Dict[str, List[Tuple[str, str, str]]] = defaultdict(list)
    for slot in constructor.get("slots") or []:
        slot_id = str(slot.get("slot_id"))
        for item in slot.get("direct_receipts") or []:
            out[str(item.get("node_id"))].append(
                (slot_id, "direct_receipt_for_slot", "direct_collider_receipt")
            )
        candidates = slot.get("candidate_transfer_receipts")
        if candidates is None:
            candidates = slot.get("transfer_receipts") or []
        for item in candidates:
            out[str(item.get("node_id"))].append(
                (slot_id, "candidate_transfer_for_slot", "candidate_transfer_receipt")
            )
    return out


def _strict_receipt_nodes(
    equation_graph: Dict[str, Any],
    receipt_index: Dict[str, List[Tuple[str, str, str]]],
) -> List[Dict[str, Any]]:
    ids = set(receipt_index)
    return [
        item
        for item in equation_graph.get("nodes") or []
        if str(item.get("id")) in ids
    ]


def _provenance_id(kind: str, raw_id: Any) -> str:
    return f"{kind}:{raw_id}"


def build_public_knowledge_graph(run_dir: Path) -> Dict[str, Any]:
    provenance = read_json(run_dir / "provenance_graph.json")
    equation_graph = read_json(run_dir / "equation_mechanism_graph.json")
    constructor = read_json(run_dir / "physical_constructor.json")

    provenance_nodes = {
        str(item.get("id")): item for item in provenance.get("nodes") or []
    }
    papers = [
        item for item in provenance_nodes.values()
        if str(item.get("node_type") or "paper") == "paper"
    ]
    authors = [
        item for item in provenance_nodes.values()
        if str(item.get("node_type")) == "author"
    ]
    references = [
        item for item in provenance_nodes.values()
        if str(item.get("node_type")) == "external_reference"
    ]
    claims = [
        item for item in provenance_nodes.values()
        if str(item.get("node_type")) == "claim"
    ]

    receipt_index = _constructor_receipt_index(constructor)
    receipts = _strict_receipt_nodes(equation_graph, receipt_index)
    receipt_ids = {str(item.get("id")) for item in receipts}

    kg_nodes: Dict[str, Dict[str, Any]] = {}
    kg_edges: List[Dict[str, Any]] = []

    kg_nodes["case:lhc_black_hole"] = node(
        "case:lhc_black_hole",
        "case",
        "Could an LHC-produced microscopic black hole grow dangerously?",
    )
    verdict_id = "verdict:constructor"
    verdict_label = (
        "complete danger mechanism connected by source equations"
        if constructor.get("branch_closed")
        else "required danger mechanism remains incomplete"
    )
    kg_nodes[verdict_id] = node(
        verdict_id,
        "verdict",
        verdict_label,
        branch_closed=bool(constructor.get("branch_closed")),
        branch_verdict=constructor.get("branch_verdict"),
        missing_direct_slots=constructor.get("missing_direct_slots") or [],
        broken_transitions=constructor.get("broken_transitions") or [],
    )
    kg_edges.append(edge(verdict_id, "case:lhc_black_hole", "answers_case"))

    for paper in papers:
        paper_id = str(paper.get("id"))
        kg_id = _provenance_id("paper", paper_id)
        kg_nodes[kg_id] = node(
            kg_id,
            "paper",
            str(paper.get("title") or paper_id),
            source_id=paper_id,
            authors=paper.get("authors") or [],
            year=paper.get("year"),
            url=paper.get("url") or f"https://arxiv.org/abs/{paper_id}",
        )
        kg_edges.append(edge(kg_id, "case:lhc_black_hole", "selected_for_case"))

    for author in authors:
        raw_id = str(author.get("id"))
        kg_id = _provenance_id("author", raw_id)
        kg_nodes[kg_id] = node(
            kg_id,
            "author",
            str(author.get("name") or raw_id),
        )

    for reference in references:
        raw_id = str(reference.get("id"))
        kg_id = _provenance_id("reference", raw_id)
        kg_nodes[kg_id] = node(
            kg_id,
            "reference",
            str(reference.get("title") or raw_id),
            url=reference.get("url") or f"https://arxiv.org/abs/{raw_id}",
        )

    for claim_type, label in CLAIM_LABELS.items():
        family_id = f"claim_family:{claim_type}"
        kg_nodes[family_id] = node(family_id, "claim_family", label)

    for claim in claims:
        claim_id = str(claim.get("id"))
        claim_type = str(claim.get("claim_type") or "unknown")
        source_id = str(claim.get("source_id") or "")
        kg_id = _provenance_id("claim", claim_id)
        kg_nodes[kg_id] = node(
            kg_id,
            "claim",
            claim_id,
            claim_type=claim_type,
            text=str(claim.get("text") or ""),
            source_id=source_id,
        )
        kg_edges.append(edge(kg_id, f"claim_family:{claim_type}", "classified_as"))

    # Preserve the source graph rather than rebuilding it from naming conventions.
    for item in provenance.get("edges") or []:
        relation = str(item.get("edge_type") or "provenance_relation")
        source_raw = str(item.get("source"))
        target_raw = str(item.get("target"))
        source_node = provenance_nodes.get(source_raw) or {}
        target_node = provenance_nodes.get(target_raw) or {}
        source_kind = str(source_node.get("node_type") or "paper")
        target_kind = str(target_node.get("node_type") or "paper")
        source_prefix = {
            "paper": "paper",
            "author": "author",
            "external_reference": "reference",
            "claim": "claim",
        }.get(source_kind, "paper")
        target_prefix = {
            "paper": "paper",
            "author": "author",
            "external_reference": "reference",
            "claim": "claim",
        }.get(target_kind, "paper")
        source_id = _provenance_id(source_prefix, source_raw)
        target_id = _provenance_id(target_prefix, target_raw)
        if source_id in kg_nodes and target_id in kg_nodes:
            kg_edges.append(edge(source_id, target_id, relation))

    for route, route_count in (equation_graph.get("route_counts") or {}).items():
        route_id = f"route:{route}"
        kg_nodes[route_id] = node(
            route_id,
            "route",
            str(route).replace("_", " "),
            count=int(route_count),
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
        kg_id = f"slot:{slot_id}"
        kg_nodes[kg_id] = node(
            kg_id,
            "constructor_slot",
            str(slot.get("label") or slot_id),
            status=slot.get("status"),
            direct_receipt_count=slot.get("direct_receipt_count"),
            candidate_transfer_count=slot.get("candidate_transfer_count"),
            required_condition=slot.get("required_condition"),
        )
        kg_edges.append(
            edge(kg_id, verdict_id, "contributes_to_verdict", status=slot.get("status"))
        )

    for item in receipts:
        equation_id = str(item.get("id"))
        source_id = str(item.get("source_id") or "")
        case = item.get("case_evidence") or {}
        grades = sorted({entry[2] for entry in receipt_index[equation_id]})
        kg_id = f"equation:{equation_id}"
        kg_nodes[kg_id] = node(
            kg_id,
            "equation_receipt",
            equation_id,
            source_id=source_id,
            source_equation_ordinal=item.get("source_equation_ordinal"),
            formula=str(item.get("formula") or ""),
            context=str(item.get("context") or ""),
            receipt_grades=grades,
            route_signature=item.get("route_signature") or [],
            constructor_roles=item.get("constructor_roles") or [],
            branch_labels=case.get("branch_labels") or [],
        )
        paper_id = f"paper:{source_id}"
        if paper_id in kg_nodes:
            kg_edges.append(edge(paper_id, kg_id, "contains_equation_receipt"))
        for route in item.get("route_signature") or []:
            route_id = f"route:{route}"
            if route_id in kg_nodes:
                kg_edges.append(edge(kg_id, route_id, "has_route"))
        for branch in case.get("branch_labels") or []:
            branch_id = f"branch:{branch}"
            if branch_id in kg_nodes:
                kg_edges.append(edge(kg_id, branch_id, "instantiates_branch"))
        for slot_id, relation, grade in receipt_index[equation_id]:
            kg_edges.append(edge(kg_id, f"slot:{slot_id}", relation, grade=grade))

    for item in equation_graph.get("edges") or []:
        left = str(item.get("source"))
        right = str(item.get("target"))
        if left in receipt_ids and right in receipt_ids:
            kg_edges.append(
                edge(
                    f"equation:{left}",
                    f"equation:{right}",
                    "source_local_equation_transition",
                    route_signature=item.get("route_signature") or [],
                )
            )
    for item in equation_graph.get("analog_edges") or []:
        left = str(item.get("source"))
        right = str(item.get("target"))
        if left in receipt_ids and right in receipt_ids:
            kg_edges.append(
                edge(
                    f"equation:{left}",
                    f"equation:{right}",
                    "cross_source_structural_analogue",
                    route_overlap=item.get("route_overlap") or [],
                    route_cosine=item.get("route_cosine"),
                )
            )

    claim_family_counts = Counter(str(item.get("claim_type") or "unknown") for item in claims)
    paper_claim_counts = Counter(
        str(item.get("source"))
        for item in provenance.get("edges") or []
        if item.get("edge_type") == "source_makes_claim"
    )
    receipt_grade_counts = Counter()
    receipt_slot_counts = Counter()
    paper_receipt_counts = Counter()
    for equation_id, entries in receipt_index.items():
        graph_node = next(
            (item for item in receipts if str(item.get("id")) == equation_id),
            None,
        )
        if graph_node:
            paper_receipt_counts[str(graph_node.get("source_id"))] += 1
        for slot_id, _, grade in entries:
            receipt_grade_counts[grade] += 1
            receipt_slot_counts[slot_id] += 1

    return {
        "report_type": "lhc_public_knowledge_graph",
        "readiness": "usable",
        "node_count": len(kg_nodes),
        "edge_count": len(kg_edges),
        "nodes": list(kg_nodes.values()),
        "edges": kg_edges,
        "summary": {
            "papers": len(papers),
            "authors": len(authors),
            "external_references": len(references),
            "claims": len(claims),
            "provenance_edge_type_counts": provenance.get("edge_type_counts") or {},
            "equation_receipts": len(receipts),
            "constructor_slots": len(constructor.get("slots") or []),
            "branch_closed": bool(constructor.get("branch_closed")),
            "claim_family_counts": dict(claim_family_counts),
            "receipt_grade_counts": dict(receipt_grade_counts),
            "receipt_slot_counts": dict(receipt_slot_counts),
            "top_papers_by_claims": paper_claim_counts.most_common(12),
            "top_papers_by_equation_receipts": paper_receipt_counts.most_common(12),
        },
        "interpretation": (
            "One typed graph joins authorship, citation, claims, source equations, "
            "operational routes and the six physical conditions required by the LHC case."
        ),
    }


def render_markdown(kg: Dict[str, Any]) -> str:
    summary = kg.get("summary") or {}
    lines = [
        "# LHC Public Knowledge Graph",
        "",
        str(kg.get("interpretation") or ""),
        "",
        f"- nodes: `{kg.get('node_count')}`",
        f"- edges: `{kg.get('edge_count')}`",
        f"- papers: `{summary.get('papers')}`",
        f"- authors: `{summary.get('authors')}`",
        f"- cited external papers: `{summary.get('external_references')}`",
        f"- claims: `{summary.get('claims')}`",
        f"- typed equation receipts: `{summary.get('equation_receipts')}`",
        f"- complete equation-connected branch: `{summary.get('branch_closed')}`",
        "",
        "## Provenance Relations",
        "",
    ]
    for key, value in sorted((summary.get("provenance_edge_type_counts") or {}).items()):
        lines.append(f"- `{key}`: `{value}`")
    lines += ["", "## Equation Receipts By Contract", ""]
    for key, value in sorted((summary.get("receipt_slot_counts") or {}).items()):
        lines.append(f"- `{key}`: `{value}`")
    lines += ["", "## Top Papers By Claims", ""]
    for key, value in summary.get("top_papers_by_claims") or []:
        lines.append(f"- `{key}`: `{value}`")
    lines += ["", "## Top Papers By Typed Equations", ""]
    for key, value in summary.get("top_papers_by_equation_receipts") or []:
        lines.append(f"- `{key}`: `{value}`")
    return "\n".join(lines).rstrip() + "\n"


def write_public_knowledge_graph(run_dir: Path) -> Dict[str, str]:
    kg = build_public_knowledge_graph(run_dir)
    json_path = run_dir / "public_knowledge_graph.json"
    md_path = run_dir / "public_knowledge_graph.md"
    json_path.write_text(json.dumps(kg, indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(render_markdown(kg), encoding="utf-8")
    return {"json": str(json_path), "markdown": str(md_path), "readiness": "usable"}
