from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List

from .physical_constructor import build_physical_constructor
from .sparse_attention import build_graph_sparse_attention


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def normalized(counter: Counter[str]) -> Dict[str, float]:
    total = sum(counter.values())
    return {key: value / total for key, value in counter.most_common()} if total else {}


def claim_type_counts(provenance: Dict[str, Any]) -> Counter[str]:
    return Counter(
        str(node.get("claim_type") or "unknown")
        for node in provenance.get("nodes") or []
        if node.get("node_type") == "claim" or str(node.get("id", "")).startswith("C")
    )


def build_discourse_mechanism_attention(run_dir: Path) -> Dict[str, Any]:
    provenance = read_json(run_dir / "provenance_graph.json")
    graph = read_json(run_dir / "equation_mechanism_graph.json")
    constructor = build_physical_constructor(run_dir)
    graph_attention = build_graph_sparse_attention(graph)

    provenance_nodes = provenance.get("nodes") or []
    provenance_edges = provenance.get("edges") or []
    node_type_counts = Counter(str(node.get("node_type") or "legacy") for node in provenance_nodes)
    edge_type_counts = Counter(str(edge.get("edge_type") or "unknown") for edge in provenance_edges)
    if not node_type_counts.get("paper"):
        node_type_counts["paper"] = sum(1 for node in provenance_nodes if not str(node.get("id", "")).startswith("C"))
    if not node_type_counts.get("claim"):
        node_type_counts["claim"] = sum(1 for node in provenance_nodes if str(node.get("id", "")).startswith("C"))
    claim_counts = claim_type_counts(provenance)

    slot_rows: List[Dict[str, Any]] = []
    for slot in constructor.get("slots") or []:
        slot_rows.append({
            "slot_id": slot.get("slot_id"),
            "label": slot.get("label"),
            "status": slot.get("status"),
            "direct_receipts": int(slot.get("direct_receipt_count") or 0),
            "candidate_transfers": int(slot.get("candidate_transfer_count") or 0),
            "required_condition": slot.get("required_condition"),
        })

    direct_slots = [slot for slot in slot_rows if slot["direct_receipts"] > 0]
    candidate_only_slots = [slot for slot in slot_rows if slot["status"] == "candidate_transfer_only"]
    missing_slots = [slot for slot in slot_rows if slot["status"] == "missing"]
    proof_checks = {
        "source_claim_provenance_present": edge_type_counts.get("source_makes_claim", 0) > 0,
        "citation_provenance_present": edge_type_counts.get("paper_cites_paper", 0) > 0,
        "authorship_provenance_present": edge_type_counts.get("author_wrote_paper", 0) > 0,
        "typed_equation_receipts_present": graph_attention["strict_receipt_node_count"] > 0,
        "equation_graph_attention_present": graph_attention["attended_edge_count"] > 0,
        "constructor_transitions_complete": not constructor.get("broken_transitions"),
        "constructor_branch_closed": bool(constructor.get("branch_closed")),
    }

    findings = [
        (
            f"The provenance layer contains {node_type_counts.get('paper', 0)} papers, "
            f"{node_type_counts.get('claim', 0)} claims and "
            f"{edge_type_counts.get('paper_cites_paper', 0)} citation links."
        ),
        (
            f"Strict formula contracts recover {graph_attention['strict_receipt_node_count']} equation nodes; "
            f"{graph_attention['attended_edge_count']} graph edges connect at least one such receipt."
        ),
        (
            f"The physical constructor fills {len(direct_slots)} of {len(slot_rows)} conditions with "
            f"direct collider equations and leaves {len(constructor.get('broken_transitions') or [])} "
            "adjacent mechanism transitions without a source-local derivation path."
        ),
    ]

    return {
        "report_type": "lhc_provenance_mechanism_comparison",
        "readiness": "usable",
        "source_run": str(run_dir),
        "provenance_graph": {
            "node_type_counts": dict(node_type_counts),
            "edge_type_counts": dict(edge_type_counts),
            "claim_type_counts": dict(claim_counts.most_common()),
            "claim_prevalence": normalized(claim_counts),
        },
        "mechanism_graph": graph_attention,
        "constructor": {
            "branch_verdict": constructor.get("branch_verdict"),
            "branch_closed": constructor.get("branch_closed"),
            "slot_rows": slot_rows,
            "direct_slots": len(direct_slots),
            "candidate_only_slots": len(candidate_only_slots),
            "missing_slots": len(missing_slots),
            "supported_transitions": constructor.get("supported_transitions") or [],
            "broken_transitions": constructor.get("broken_transitions") or [],
        },
        "proof_checks": proof_checks,
        "findings": findings,
        "comparison": (
            "Provenance resolves responsibility and documentary dependence. The mechanism graph resolves "
            "which equations instantiate each physical condition and whether those equations compose in source order."
        ),
    }


def render_markdown(result: Dict[str, Any]) -> str:
    provenance = result["provenance_graph"]
    mechanism = result["mechanism_graph"]
    constructor = result["constructor"]
    lines: List[str] = [
        "# Provenance and Equation Mechanisms",
        "",
        result["comparison"],
        "",
        "## Provenance graph",
        "",
    ]
    for node_type, count in provenance["node_type_counts"].items():
        lines.append(f"- `{node_type}` nodes: `{count}`")
    for edge_type, count in provenance["edge_type_counts"].items():
        lines.append(f"- `{edge_type}` edges: `{count}`")
    lines += [
        "",
        "## Equation graph",
        "",
        f"- strict equation receipts: `{mechanism['strict_receipt_node_count']}`",
        f"- attended graph edges: `{mechanism['attended_edge_count']}`",
        "",
        "## Physical constructor",
        "",
        f"- branch: `{constructor['branch_verdict']}`",
        f"- direct conditions: `{constructor['direct_slots']}/{len(constructor['slot_rows'])}`",
        f"- missing source-local transitions: `{len(constructor['broken_transitions'])}`",
        "",
        "| Condition | Status | Direct equations | Transfer candidates |",
        "|---|---:|---:|---:|",
    ]
    for slot in constructor["slot_rows"]:
        lines.append(
            f"| {slot['label']} | `{slot['status']}` | {slot['direct_receipts']} | "
            f"{slot['candidate_transfers']} |"
        )
    lines += ["", "## Findings", ""]
    lines.extend(f"- {finding}" for finding in result["findings"])
    return "\n".join(lines).rstrip() + "\n"


def write_discourse_mechanism_attention(run_dir: Path) -> Dict[str, str]:
    result = build_discourse_mechanism_attention(run_dir)
    json_path = run_dir / "discourse_vs_mechanism_attention.json"
    md_path = run_dir / "discourse_vs_mechanism_attention.md"
    json_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(render_markdown(result), encoding="utf-8")
    return {"json": str(json_path), "markdown": str(md_path), "readiness": result["readiness"]}
