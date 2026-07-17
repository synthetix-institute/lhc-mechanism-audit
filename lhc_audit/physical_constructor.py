from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

from .evidence_contract import (
    SLOT_CONTRACTS,
    SLOT_ORDER,
    classify_receipt,
    contracts_compose,
    source_local_reachable,
)


# Public compatibility name used by report builders.
SLOT_DEFINITIONS = SLOT_CONTRACTS


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def slot_match(node: Dict[str, Any], slot: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    """Match a slot from the equation itself; prose supplies regime only."""
    grade, details = classify_receipt(node, slot)
    return grade is not None, details


def evidence_grade(node: Dict[str, Any], slot: Dict[str, Any]) -> Tuple[str | None, Dict[str, Any]]:
    return classify_receipt(node, slot)


def slot_status(direct: List[Dict[str, Any]], candidates: List[Dict[str, Any]]) -> str:
    if direct:
        return "direct_mechanism_receipt"
    if candidates:
        return "candidate_transfer_only"
    return "missing"


def node_summary(node: Dict[str, Any], match: Dict[str, Any] | None = None) -> Dict[str, Any]:
    case = node.get("case_evidence") or {}
    out = {
        "node_id": node.get("id"),
        "source_id": node.get("source_id"),
        "source_equation_ordinal": node.get("source_equation_ordinal"),
        "formula": str(node.get("formula") or ""),
        "context": str(node.get("context") or ""),
        "text_role": node.get("text_role"),
        "route_signature": node.get("route_signature") or [],
        "constructor_roles": node.get("constructor_roles") or [],
        "pair_status": node.get("pair_status"),
        "formula_detail_score": node.get("formula_detail_score"),
        "local_categories": case.get("local_categories") or [],
        "branch_labels": case.get("branch_labels") or [],
    }
    if match:
        out["slot_match"] = match
    return out


def _rank(node: Dict[str, Any]) -> Tuple[int, int, int]:
    return (
        int(node.get("formula_detail_score") or 0),
        len(node.get("constructor_roles") or []),
        len(str(node.get("formula") or "")),
    )


def _slot_receipts(nodes: List[Dict[str, Any]], slot: Dict[str, Any]) -> Dict[str, Any]:
    direct: List[Tuple[Dict[str, Any], Dict[str, Any]]] = []
    candidates: List[Tuple[Dict[str, Any], Dict[str, Any]]] = []
    rejected_formula_matches = 0

    for node in nodes:
        grade, details = evidence_grade(node, slot)
        if grade == "direct_collider_receipt":
            direct.append((node, details))
        elif grade == "candidate_transfer_receipt":
            candidates.append((node, details))
        elif details.get("formula_contract_valid"):
            rejected_formula_matches += 1

    direct.sort(key=lambda pair: _rank(pair[0]), reverse=True)
    candidates.sort(key=lambda pair: _rank(pair[0]), reverse=True)
    return {
        "direct": direct,
        "candidates": candidates,
        "rejected_formula_matches": rejected_formula_matches,
    }


def _composition_audit(
    slots: List[Dict[str, Any]],
    raw_receipts: Dict[str, Dict[str, Any]],
    graph_edges: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    supported: List[Dict[str, Any]] = []
    broken: List[Dict[str, Any]] = []
    slot_by_id = {slot["slot_id"]: slot for slot in slots}

    for left_id, right_id in zip(SLOT_ORDER, SLOT_ORDER[1:]):
        left_slot = slot_by_id[left_id]
        right_slot = slot_by_id[right_id]
        contract_compatible = contracts_compose(left_slot, right_slot)
        witnesses: List[Dict[str, Any]] = []
        typed_cross_source_candidates = 0

        for left_node, _ in raw_receipts[left_id]["direct"]:
            for right_node, _ in raw_receipts[right_id]["direct"]:
                left_source = str(left_node.get("source_id") or "")
                right_source = str(right_node.get("source_id") or "")
                if left_source != right_source:
                    typed_cross_source_candidates += 1
                    continue
                if source_local_reachable(
                    left_source,
                    left_node.get("id"),
                    right_node.get("id"),
                    graph_edges,
                ):
                    witnesses.append({
                        "source_id": left_source,
                        "source_node": left_node.get("id"),
                        "target_node": right_node.get("id"),
                        "edge_type": "source_local_equation_path",
                    })

        record = {
            "source_slot": left_id,
            "target_slot": right_id,
            "contract_compatible": contract_compatible,
            "source_local_witnesses": witnesses,
            "typed_cross_source_candidates": typed_cross_source_candidates,
            "supports_branch_closure": bool(contract_compatible and witnesses),
        }
        if record["supports_branch_closure"]:
            supported.append(record)
        else:
            broken.append(record)
    return supported, broken


def build_physical_constructor(run_dir: Path) -> Dict[str, Any]:
    graph = read_json(run_dir / "equation_mechanism_graph.json")
    usable_ids = set(graph.get("usable_node_ids") or [])
    nodes = [
        node for node in graph.get("nodes") or []
        if str(node.get("id")) in usable_ids
    ]

    slots: List[Dict[str, Any]] = []
    raw_receipts: Dict[str, Dict[str, Any]] = {}
    for slot_def in SLOT_DEFINITIONS:
        receipts = _slot_receipts(nodes, slot_def)
        raw_receipts[slot_def["slot_id"]] = receipts
        direct = receipts["direct"]
        candidates = receipts["candidates"]
        slots.append({
            "slot_id": slot_def["slot_id"],
            "label": slot_def["label"],
            "required_condition": slot_def["required_condition"],
            "equation_template": slot_def["equation_template"],
            "route_need": slot_def["route_need"],
            "formula_quantities": slot_def["formula_quantities"],
            "inputs": slot_def["inputs"],
            "outputs": slot_def["outputs"],
            "status": slot_status([item[0] for item in direct], [item[0] for item in candidates]),
            "direct_receipt_count": len(direct),
            "candidate_transfer_count": len(candidates),
            # Compatibility aliases for existing figure/report code.
            "transfer_receipt_count": len(candidates),
            "direct_receipts": [node_summary(node, match) for node, match in direct],
            "candidate_transfer_receipts": [node_summary(node, match) for node, match in candidates],
            "transfer_receipts": [node_summary(node, match) for node, match in candidates],
            "rejected_formula_matches_without_case_regime": receipts["rejected_formula_matches"],
        })

    supported_transitions, broken_transitions = _composition_audit(
        SLOT_DEFINITIONS,
        raw_receipts,
        list(graph.get("edges") or []),
    )
    missing_direct_slots = [
        slot["slot_id"] for slot in slots
        if slot["status"] != "direct_mechanism_receipt"
    ]
    branch_closed = not missing_direct_slots and not broken_transitions

    return {
        "report_type": "lhc_physical_constructor",
        "schema": "typed equation-contract constructor v2",
        "readiness": "usable",
        "source_run": str(run_dir),
        "evidence_rule": (
            "Equation quantities fill mechanism slots; surrounding text identifies the physical regime. "
            "Branch closure additionally requires a source-local equation path between every adjacent slot."
        ),
        "input_counts": {
            "source_witness_count": graph.get("source_witness_count"),
            "usable_mechanism_node_count": graph.get("usable_mechanism_node_count"),
            "case_relevant_mechanism_node_count": graph.get("case_relevant_mechanism_node_count"),
        },
        "branch_closed": branch_closed,
        "branch_verdict": (
            "closed_composable_danger_branch"
            if branch_closed
            else "incomplete_direct_mechanism_branch"
        ),
        "missing_direct_slots": missing_direct_slots,
        "broken_required_slots": missing_direct_slots,
        "supported_transitions": supported_transitions,
        "broken_transitions": broken_transitions,
        "candidate_transfer_only_slots": [
            slot["slot_id"] for slot in slots
            if slot["status"] == "candidate_transfer_only"
        ],
        "transfer_only_slots": [
            slot["slot_id"] for slot in slots
            if slot["status"] == "candidate_transfer_only"
        ],
        "slots": slots,
    }


def render_markdown(constructor: Dict[str, Any]) -> str:
    lines: List[str] = [
        "# LHC Physical Constructor",
        "",
        f"Verdict: `{constructor['branch_verdict']}`",
        "",
        constructor["evidence_rule"],
        "",
        "| Mechanism condition | Status | Direct collider equations | Transfer candidates |",
        "|---|---:|---:|---:|",
    ]
    for slot in constructor["slots"]:
        lines.append(
            f"| {slot['label']} | `{slot['status']}` | {slot['direct_receipt_count']} | "
            f"{slot['candidate_transfer_count']} |"
        )

    lines += ["", "## Equation Receipts", ""]
    for slot in constructor["slots"]:
        lines += [
            f"### {slot['label']}",
            "",
            f"Required relation: ${slot['equation_template']}$",
            "",
        ]
        if slot["direct_receipts"]:
            lines.append("Direct collider equations:")
            lines.append("")
            for item in slot["direct_receipts"]:
                lines.append(f"- `{item['source_id']}` / `{item['node_id']}`: `${item['formula']}$`")
            lines.append("")
        if slot["candidate_transfer_receipts"]:
            lines.append("Cross-regime equation candidates:")
            lines.append("")
            for item in slot["candidate_transfer_receipts"]:
                lines.append(f"- `{item['source_id']}` / `{item['node_id']}`: `${item['formula']}$`")
            lines.append("")
        if not slot["direct_receipts"] and not slot["candidate_transfer_receipts"]:
            lines += ["No equation satisfies this contract in the retained run.", ""]

    lines += ["## Composition", ""]
    for transition in constructor["supported_transitions"]:
        lines.append(
            f"- `{transition['source_slot']} -> {transition['target_slot']}`: "
            f"{len(transition['source_local_witnesses'])} source-local equation path(s)."
        )
    for transition in constructor["broken_transitions"]:
        lines.append(
            f"- `{transition['source_slot']} -> {transition['target_slot']}`: no source-local equation path."
        )
    return "\n".join(lines).rstrip() + "\n"


def write_constructor(run_dir: Path) -> Dict[str, str]:
    constructor = build_physical_constructor(run_dir)
    json_path = run_dir / "physical_constructor.json"
    md_path = run_dir / "physical_constructor.md"
    json_path.write_text(json.dumps(constructor, indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(render_markdown(constructor), encoding="utf-8")
    return {"json": str(json_path), "markdown": str(md_path), "readiness": constructor["readiness"]}
