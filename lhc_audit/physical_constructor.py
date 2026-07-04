from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple


SLOT_DEFINITIONS: List[Dict[str, Any]] = [
    {
        "slot_id": "production_selector",
        "label": "production threshold",
        "required_condition": "parton collision can enter a low-scale-gravity production channel",
        "equation_template": r"\sqrt{\hat s}=\sqrt{x_1x_2s}>M_{\min},\quad \sigma_{\rm form}\sim \pi r_s^2(M,M_D,n)",
        "direct_categories": {"collider_threshold"},
        "transfer_categories": set(),
        "route_need": ["constraint_closure", "boundary_weak_form"],
        "formula_patterns": [
            r"\\sqrt\{?\\hat\s*s",
            r"M_\{?\\?(?:min|D|P|Planck|BH|f)",
            r"p_?\{?T",
            r"y_\{?\\gamma",
            r"\\sigma",
            r"TeV",
        ],
        "context_patterns": [
            r"LHC|collider|parton|Planck|extra dimension|TeV",
            r"black hole (?:production|formation|evaporation)",
            r"Higgs|diphoton|transverse momentum|rapidity",
        ],
    },
    {
        "slot_id": "survival_lifetime",
        "label": "survival against evaporation",
        "required_condition": "object lifetime exceeds the capture or stopping time",
        "equation_template": r"\tau_{\rm evap}(M,M_D,n)>\tau_{\rm capture}",
        "direct_categories": {"evaporation_branch", "collider_threshold"},
        "transfer_categories": {"evaporation_branch"},
        "route_need": ["transport_flow", "constraint_closure"],
        "formula_patterns": [
            r"\\tau|tau|lifetime",
            r"T_\{?BH|T_\{?\\rm\s*BH|T_\\mathrm\{BH\}",
            r"P_\{?evap|P_\{?\\rm\s*evap|evaporat|Hawking",
            r"dM\s*/\s*dt\s*<\s*0",
            r"evaporat|Hawking",
        ],
        "context_patterns": [
            r"evaporat|Hawking|lifetime|mass[- ]loss",
            r"short[- ]lived|long[- ]lived",
        ],
    },
    {
        "slot_id": "stopping_capture",
        "label": "stopping or capture in matter",
        "required_condition": "object loses enough kinetic energy to remain inside matter",
        "equation_template": r"L_{\rm stop}(M,v,\rho,\sigma)<L_{\rm body}\quad {\rm or}\quad \tau_{\rm capture}<\tau_{\rm escape}",
        "direct_categories": {"capture_stopping", "collider_threshold"},
        "transfer_categories": {"capture_stopping"},
        "route_need": ["transport_flow", "constraint_closure"],
        "formula_patterns": [
            r"R_\{?in\s*/\s*R_?\{?a",
            r"Bondi",
            r"dE\s*/\s*dx|\\Delta\s*E",
            r"\\tau_\{?capture|capture|stopp",
            r"\\Delta\s*t",
        ],
        "context_patterns": [
            r"capture|stopping|energy loss|Bondi|accretion radius|remain inside",
            r"compact object|neutron star|white dwarf",
        ],
    },
    {
        "slot_id": "net_positive_growth",
        "label": "net positive mass growth",
        "required_condition": "matter intake exceeds mass loss",
        "equation_template": r"\dot M_{\rm net}=\rho\,\sigma(M)\,v-P_{\rm evap}(M)/c^2>0",
        "direct_categories": {"accretion_growth", "collider_threshold"},
        "transfer_categories": {"accretion_growth"},
        "route_need": ["transport_flow", "constraint_closure", "spectral_operator"],
        "formula_patterns": [
            r"\\dot\{?M|\\dot\s*M|Mdot|\\langle\s*\\dot\{?M",
            r"\\dot\{?m|\\dot\s*m",
            r"L_\{?Edd|L_X",
            r"\\delta\s*M",
            r"\\rho.*\\sigma.*v",
            r"M_\{?\\odot\s*/\s*(?:yr|year)",
        ],
        "context_patterns": [
            r"accretion|growth|mass[- ]growth|mass intake|time-average accretion",
            r"luminosity|Eddington|Bondi",
        ],
    },
    {
        "slot_id": "growth_timescale",
        "label": "growth on a relevant timescale",
        "required_condition": "integrated growth time is shorter than the physical exposure time",
        "equation_template": r"t_{\rm grow}=\int_{M_0}^{M_*}\frac{dM}{\dot M_{\rm net}(M)}<t_{\rm exposure}",
        "direct_categories": {"accretion_growth", "safety_risk", "collider_threshold"},
        "transfer_categories": {"accretion_growth", "astrophysical_bound"},
        "route_need": ["transport_flow", "constraint_closure"],
        "formula_patterns": [
            r"t_\{?grow|\\Delta\s*t|\\tau",
            r"(?:yr|Myr|Gyr|second|sec)",
            r"\\dot\{?M|\\dot\s*M|M_\{?\\odot\s*/\s*(?:yr|year)",
        ],
        "context_patterns": [
            r"timescale|growth time|time-average|lifetime|duration|delayed collapse",
            r"shorter than|longer than|survival",
        ],
    },
    {
        "slot_id": "astronomical_bound_evasion",
        "label": "evasion of astronomical survival bounds",
        "required_condition": "same mechanism must avoid contradiction with compact-object survival",
        "equation_template": r"N_{\rm CR}\,P_{\rm capture}\,P_{\rm grow}\ll 1\quad {\rm for\ observed\ white\ dwarfs/neutron\ stars}",
        "direct_categories": {"astrophysical_bound", "safety_risk", "collider_threshold"},
        "transfer_categories": {"astrophysical_bound"},
        "route_need": ["constraint_closure", "spectral_operator"],
        "formula_patterns": [
            r"M_\{?(?:WD|NS|BH)",
            r"M_\{?\\odot|M_\\odot|M_\{?\\sun",
            r"L_\{?Edd",
            r"\\chi_\{?BH|a_\{?BH",
            r"white dwarf|neutron star",
        ],
        "context_patterns": [
            r"white dwarf|neutron star|compact object|cosmic ray",
            r"observed survival|survival bounds?|astrophysical bound",
            r"black hole[- ]neutron star|binary neutron stars",
        ],
    },
]


COMPILED_SLOT_PATTERNS: Dict[str, Dict[str, List[re.Pattern[str]]]] = {
    slot["slot_id"]: {
        "formula": [re.compile(pattern, re.IGNORECASE | re.DOTALL) for pattern in slot.get("formula_patterns", [])],
        "context": [re.compile(pattern, re.IGNORECASE | re.DOTALL) for pattern in slot.get("context_patterns", [])],
    }
    for slot in SLOT_DEFINITIONS
}


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def compact(text: Any, limit: int = 420) -> str:
    value = " ".join(str(text or "").split())
    return value if len(value) <= limit else value[: limit - 3] + "..."


def node_categories(node: Dict[str, Any]) -> set[str]:
    case = node.get("case_evidence") or {}
    return set(case.get("local_categories") or []) | set(case.get("categories") or [])


def is_receipt(node: Dict[str, Any], receipt_ids: set[str]) -> bool:
    return str(node.get("id")) in receipt_ids


def slot_match(node: Dict[str, Any], slot: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    patterns = COMPILED_SLOT_PATTERNS.get(slot["slot_id"], {})
    formula = str(node.get("formula") or "")
    context = str(node.get("context") or "")
    formula_hits = [
        pattern.pattern
        for pattern in patterns.get("formula", [])
        if pattern.search(formula)
    ]
    context_hits = [
        pattern.pattern
        for pattern in patterns.get("context", [])
        if pattern.search(context)
    ]
    routes = set(node.get("route_signature") or [])
    needed = set(slot.get("route_need") or [])
    route_hits = sorted(routes & needed)
    has_slot_evidence = bool(formula_hits or context_hits)
    # For required mechanism slots, route agreement alone is not enough. It can
    # only support an already slot-specific formula/context match.
    return has_slot_evidence, {
        "formula_hits": formula_hits[:4],
        "context_hits": context_hits[:4],
        "route_hits": route_hits,
    }


def evidence_grade(node: Dict[str, Any], slot: Dict[str, Any]) -> Tuple[str | None, Dict[str, Any]]:
    categories = node_categories(node)
    matched, match = slot_match(node, slot)
    if "black_hole" not in categories:
        return None, match
    if not matched:
        return None, match
    direct_categories = set(slot["direct_categories"])
    transfer_categories = set(slot["transfer_categories"])
    if direct_categories and direct_categories <= categories:
        return "direct_collider_receipt", match
    if slot["slot_id"] == "production_selector" and "collider_threshold" in categories:
        return "direct_collider_receipt", match
    if transfer_categories and transfer_categories <= categories:
        return "astrophysical_transfer_receipt", match
    return None, match


def slot_status(slot: Dict[str, Any], direct: List[Dict[str, Any]], transfer: List[Dict[str, Any]]) -> str:
    if slot["slot_id"] == "production_selector" and direct:
        return "direct_hook"
    if direct:
        return "direct_mechanism_receipt"
    if transfer:
        return "transfer_only"
    return "missing"


def node_summary(node: Dict[str, Any], match: Dict[str, Any] | None = None) -> Dict[str, Any]:
    case = node.get("case_evidence") or {}
    out = {
        "node_id": node.get("id"),
        "source_id": node.get("source_id"),
        "formula": compact(node.get("formula"), 600),
        "context": compact(node.get("context"), 700),
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


def build_physical_constructor(run_dir: Path) -> Dict[str, Any]:
    graph = read_json(run_dir / "equation_mechanism_graph.json")
    receipt_ids = set(graph.get("evidence_grade_case_node_ids") or [])
    nodes = [node for node in graph.get("nodes") or [] if is_receipt(node, receipt_ids)]

    slots: List[Dict[str, Any]] = []
    for slot_def in SLOT_DEFINITIONS:
        direct: List[Dict[str, Any]] = []
        transfer: List[Dict[str, Any]] = []
        direct_matches: Dict[str, Dict[str, Any]] = {}
        transfer_matches: Dict[str, Dict[str, Any]] = {}
        for node in nodes:
            grade, match = evidence_grade(node, slot_def)
            if grade == "direct_collider_receipt":
                direct.append(node)
                direct_matches[str(node.get("id"))] = match
            elif grade == "astrophysical_transfer_receipt":
                transfer.append(node)
                transfer_matches[str(node.get("id"))] = match
        direct.sort(key=lambda n: int(n.get("formula_detail_score") or 0), reverse=True)
        transfer.sort(key=lambda n: int(n.get("formula_detail_score") or 0), reverse=True)
        status = slot_status(slot_def, direct, transfer)
        slots.append({
            "slot_id": slot_def["slot_id"],
            "label": slot_def["label"],
            "required_condition": slot_def["required_condition"],
            "equation_template": slot_def["equation_template"],
            "route_need": slot_def["route_need"],
            "status": status,
            "direct_receipt_count": len(direct),
            "transfer_receipt_count": len(transfer),
            "direct_receipts": [
                node_summary(node, direct_matches.get(str(node.get("id"))))
                for node in direct[:6]
            ],
            "transfer_receipts": [
                node_summary(node, transfer_matches.get(str(node.get("id"))))
                for node in transfer[:8]
            ],
        })

    direct_required = [
        slot for slot in slots
        if slot["slot_id"] in {
            "survival_lifetime",
            "stopping_capture",
            "net_positive_growth",
            "growth_timescale",
            "astronomical_bound_evasion",
        }
    ]
    broken_slots = [slot for slot in direct_required if slot["status"] != "direct_mechanism_receipt"]
    transfer_slots = [slot for slot in slots if slot["status"] == "transfer_only"]
    hook_slots = [slot for slot in slots if slot["status"] == "direct_hook"]

    return {
        "report_type": "lhc_physical_constructor",
        "schema": "KnowledgeParser operator/substrate constructor adapter",
        "source_run": str(run_dir),
        "input_counts": {
            "source_witness_count": graph.get("source_witness_count"),
            "usable_mechanism_node_count": graph.get("usable_mechanism_node_count"),
            "case_relevant_mechanism_node_count": graph.get("case_relevant_mechanism_node_count"),
            "evidence_grade_case_mechanism_node_count": graph.get("evidence_grade_case_mechanism_node_count"),
            "direct_lhc_safety_mechanism_node_count": graph.get("direct_lhc_safety_mechanism_node_count"),
            "astrophysical_analogue_mechanism_node_count": graph.get("astrophysical_analogue_mechanism_node_count"),
            "production_threshold_mechanism_node_count": graph.get("production_threshold_mechanism_node_count"),
        },
        "branch_closed": not broken_slots,
        "branch_verdict": (
            "closed_danger_branch"
            if not broken_slots
            else "broken_danger_branch"
        ),
        "filled_direct_hooks": [slot["slot_id"] for slot in hook_slots],
        "transfer_only_slots": [slot["slot_id"] for slot in transfer_slots],
        "broken_required_slots": [slot["slot_id"] for slot in broken_slots],
        "slots": slots,
        "claim_scope": (
            "This constructor assembles public static graph receipts into the physical LHC danger branch. "
            "It uses KnowledgeParser operator/substrate constructor frames already embedded in the graph; "
            "it does not recompute private fingerprints."
        ),
    }


def render_markdown(constructor: Dict[str, Any]) -> str:
    lines: List[str] = [
        "# LHC Physical Constructor",
        "",
        f"Verdict: `{constructor['branch_verdict']}`",
        "",
        "A dangerous LHC black-hole mechanism requires every slot below. The table distinguishes direct collider receipts from astrophysical transfer receipts.",
        "",
        "| Slot | Status | Direct receipts | Transfer receipts | Required condition |",
        "|---|---:|---:|---:|---|",
    ]
    for slot in constructor["slots"]:
        lines.append(
            f"| {slot['label']} | `{slot['status']}` | {slot['direct_receipt_count']} | "
            f"{slot['transfer_receipt_count']} | {slot['required_condition']} |"
        )
    lines += ["", "## Slot Receipts", ""]
    for slot in constructor["slots"]:
        lines += [
            f"### {slot['label']}",
            "",
            f"- status: `{slot['status']}`",
            f"- equation template: `{slot['equation_template']}`",
            "",
        ]
        if slot["direct_receipts"]:
            lines.append("Direct collider receipts:")
            lines.append("")
            for item in slot["direct_receipts"]:
                lines.append(f"- `{item['source_id']}` / `{item['node_id']}`: `{item['formula']}`")
            lines.append("")
        if slot["transfer_receipts"]:
            lines.append("Astrophysical transfer receipts:")
            lines.append("")
            for item in slot["transfer_receipts"][:5]:
                lines.append(f"- `{item['source_id']}` / `{item['node_id']}`: `{item['formula']}`")
            lines.append("")
        if not slot["direct_receipts"] and not slot["transfer_receipts"]:
            lines.append("No retained branch receipt fills this slot.")
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def write_constructor(run_dir: Path) -> Dict[str, str]:
    constructor = build_physical_constructor(run_dir)
    json_path = run_dir / "physical_constructor.json"
    md_path = run_dir / "physical_constructor.md"
    json_path.write_text(json.dumps(constructor, indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(render_markdown(constructor), encoding="utf-8")
    return {"json": str(json_path), "markdown": str(md_path), "readiness": "usable"}
