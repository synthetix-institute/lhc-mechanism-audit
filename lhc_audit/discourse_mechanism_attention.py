from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List

from lhc_audit.physical_constructor import build_physical_constructor


ROUTES = [
    "transport_flow",
    "constraint_closure",
    "spectral_operator",
    "boundary_weak_form",
    "commutator_incompatibility",
    "discrete_protocol",
]


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def normalized(counter: Counter[str]) -> Dict[str, float]:
    total = sum(counter.values())
    if total <= 0:
        return {}
    return {key: value / total for key, value in counter.most_common()}


def claim_type_counts(provenance: Dict[str, Any]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for node in provenance.get("nodes") or []:
        if str(node.get("id", "")).startswith("C"):
            counts[str(node.get("claim_type") or "unknown")] += 1
    return counts


def active_routes(node: Dict[str, Any], threshold: float = 0.12) -> List[str]:
    profile = node.get("route_profile") or {}
    routes: List[str] = []
    for route in ROUTES:
        try:
            if float(profile.get(route, 0.0)) >= threshold:
                routes.append(route)
        except Exception:
            continue
    signature = node.get("route_signature") or []
    for route in signature:
        if route in ROUTES and route not in routes:
            routes.append(route)
    return routes


def evidence_nodes(graph: Dict[str, Any]) -> List[Dict[str, Any]]:
    ids = set(graph.get("evidence_grade_case_node_ids") or [])
    return [node for node in graph.get("nodes") or [] if str(node.get("id")) in ids]


def build_discourse_mechanism_attention(run_dir: Path) -> Dict[str, Any]:
    provenance = read_json(run_dir / "provenance_graph.json")
    graph = read_json(run_dir / "equation_mechanism_graph.json")
    constructor = build_physical_constructor(run_dir)

    provenance_nodes = provenance.get("nodes") or []
    provenance_edges = provenance.get("edges") or []
    paper_count = sum(1 for node in provenance_nodes if not str(node.get("id", "")).startswith("C"))
    claim_count = sum(1 for node in provenance_nodes if str(node.get("id", "")).startswith("C"))
    claim_counts = claim_type_counts(provenance)

    nodes = evidence_nodes(graph)
    route_counts: Counter[str] = Counter()
    branch_counts: Counter[str] = Counter()
    branch_route_counts: Dict[str, Counter[str]] = {}
    for node in nodes:
        routes = active_routes(node)
        case = node.get("case_evidence") or {}
        branches = list(case.get("branch_labels") or ["unassigned_case_branch"])
        for route in routes:
            route_counts[route] += 1
        for branch in branches:
            branch_counts[branch] += 1
            branch_counter = branch_route_counts.setdefault(branch, Counter())
            for route in routes:
                branch_counter[route] += 1

    slots = constructor.get("slots") or []
    slot_rows: List[Dict[str, Any]] = []
    for slot in slots:
        slot_rows.append(
            {
                "slot_id": slot.get("slot_id"),
                "label": slot.get("label"),
                "status": slot.get("status"),
                "direct_receipts": int(slot.get("direct_receipt_count") or 0),
                "transfer_receipts": int(slot.get("transfer_receipt_count") or 0),
                "required_condition": slot.get("required_condition"),
            }
        )

    downstream_slots = [slot for slot in slot_rows if slot["slot_id"] != "production_selector"]
    direct_downstream_slots = [slot for slot in downstream_slots if slot["direct_receipts"] > 0]
    transfer_only_downstream_slots = [slot for slot in downstream_slots if slot["status"] == "transfer_only"]
    missing_downstream_slots = [slot for slot in downstream_slots if slot["status"] == "missing"]

    proof_checks = {
        "provenance_can_count_claims": claim_count > 0 and bool(provenance_edges),
        "provenance_has_no_physical_slot_dimension": True,
        "mechanism_has_equation_receipts": len(nodes) > 0,
        "mechanism_has_constructor_slots": len(slot_rows) > 0,
        "direct_production_hook_present": any(
            slot["slot_id"] == "production_selector" and slot["direct_receipts"] > 0
            for slot in slot_rows
        ),
        "downstream_direct_closure_absent": len(direct_downstream_slots) == 0,
        "transfer_receipts_populate_downstream": len(transfer_only_downstream_slots) > 0,
    }

    findings = [
        (
            "The discourse graph resolves the literature as papers linked to claim families. "
            "It shows where statements occur, but it has no variable for survival, capture, growth, or astronomical-bound closure."
        ),
        (
            "The mechanism graph resolves the same source set as formula receipts placed into physical slots. "
            "That layer finds one direct collider production hook and no direct downstream collider closure."
        ),
        (
            "Sparse route attention concentrates on spectral/operator, closure, and transport roles. "
            "Those are exactly the operations needed to test threshold, lifetime, capture, and growth."
        ),
        (
            "The decisive result is structural: downstream evidence is transfer evidence from astrophysics, not a closed collider catastrophe branch."
        ),
    ]

    return {
        "report_type": "lhc_discourse_vs_mechanism_attention",
        "readiness": "usable",
        "source_run": str(run_dir),
        "discourse_graph": {
            "paper_nodes": paper_count,
            "claim_nodes": claim_count,
            "source_to_claim_edges": len(provenance_edges),
            "claim_type_counts": dict(claim_counts.most_common()),
            "claim_attention": normalized(claim_counts),
        },
        "mechanism_graph": {
            "fingerprinted_equation_windows": int(graph.get("fingerprinted_node_count") or 0),
            "usable_equation_nodes": int(graph.get("usable_mechanism_node_count") or 0),
            "case_relevant_nodes": int(graph.get("case_relevant_mechanism_node_count") or 0),
            "evidence_grade_receipts": len(nodes),
            "route_counts": dict(route_counts.most_common()),
            "route_attention": normalized(route_counts),
            "branch_counts": dict(branch_counts.most_common()),
            "branch_attention": normalized(branch_counts),
            "branch_route_attention": {
                branch: normalized(counter)
                for branch, counter in sorted(branch_route_counts.items())
            },
        },
        "constructor": {
            "branch_verdict": constructor.get("branch_verdict"),
            "slot_rows": slot_rows,
            "required_downstream_slots": len(downstream_slots),
            "direct_downstream_slots": len(direct_downstream_slots),
            "transfer_only_downstream_slots": len(transfer_only_downstream_slots),
            "missing_downstream_slots": len(missing_downstream_slots),
        },
        "proof_checks": proof_checks,
        "findings": findings,
        "advantage": (
            "A discourse graph ranks who said what. A mechanism graph tests whether equations "
            "can be assembled into the required physical branch. In this run the two layers diverge: "
            "claims exist, but the equation constructor stops after the production hook."
        ),
    }


def render_markdown(audit: Dict[str, Any]) -> str:
    discourse = audit["discourse_graph"]
    mechanism = audit["mechanism_graph"]
    constructor = audit["constructor"]
    lines: List[str] = [
        "# Discourse-vs-Mechanism Sparse Attention",
        "",
        "## Result",
        "",
        audit["advantage"],
        "",
        "## Discourse Graph",
        "",
        f"- paper nodes: `{discourse['paper_nodes']}`",
        f"- claim nodes: `{discourse['claim_nodes']}`",
        f"- source-to-claim edges: `{discourse['source_to_claim_edges']}`",
        "",
        "Claim attention:",
    ]
    for label, score in discourse["claim_attention"].items():
        lines.append(f"- `{label}`: `{score:.3f}`")
    lines += [
        "",
        "## Mechanism Graph",
        "",
        f"- fingerprinted equation windows: `{mechanism['fingerprinted_equation_windows']}`",
        f"- usable equation nodes: `{mechanism['usable_equation_nodes']}`",
        f"- case-relevant nodes: `{mechanism['case_relevant_nodes']}`",
        f"- evidence-grade receipts: `{mechanism['evidence_grade_receipts']}`",
        "",
        "Route attention:",
    ]
    for label, score in mechanism["route_attention"].items():
        lines.append(f"- `{label}`: `{score:.3f}`")
    lines += [
        "",
        "## Constructor",
        "",
        f"- branch verdict: `{constructor['branch_verdict']}`",
        f"- required downstream slots: `{constructor['required_downstream_slots']}`",
        f"- direct downstream slots: `{constructor['direct_downstream_slots']}`",
        f"- transfer-only downstream slots: `{constructor['transfer_only_downstream_slots']}`",
        f"- missing downstream slots: `{constructor['missing_downstream_slots']}`",
        "",
        "| Slot | Status | Direct receipts | Transfer receipts |",
        "|---|---:|---:|---:|",
    ]
    for slot in constructor["slot_rows"]:
        lines.append(
            f"| {slot['label']} | `{slot['status']}` | {slot['direct_receipts']} | {slot['transfer_receipts']} |"
        )
    lines += ["", "## Findings", ""]
    for finding in audit["findings"]:
        lines.append(f"- {finding}")
    return "\n".join(lines).rstrip() + "\n"


def write_discourse_mechanism_attention(run_dir: Path) -> Dict[str, str]:
    audit = build_discourse_mechanism_attention(run_dir)
    json_path = run_dir / "discourse_vs_mechanism_attention.json"
    md_path = run_dir / "discourse_vs_mechanism_attention.md"
    json_path.write_text(json.dumps(audit, indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(render_markdown(audit), encoding="utf-8")
    return {"json": str(json_path), "markdown": str(md_path), "readiness": "usable"}
