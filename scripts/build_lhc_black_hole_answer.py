#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Tuple

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lhc_audit.constructor_layer_export import build_constructor_layer_export
from lhc_audit.discourse_mechanism_attention import write_discourse_mechanism_attention
from lhc_audit.physical_constructor import build_physical_constructor, write_constructor
from lhc_audit.public_knowledge_graph import build_public_knowledge_graph, write_public_knowledge_graph


DEFAULT_RUN = ROOT / "runs" / "lhc_black_hole_audit_revised"
SLOT_ORDER = [
    "production_selector",
    "survival_lifetime",
    "stopping_capture",
    "net_positive_growth",
    "growth_timescale",
    "astronomical_bound_evasion",
]
SLOT_SHORT = {
    "production_selector": "production",
    "survival_lifetime": "survival",
    "stopping_capture": "stopping",
    "net_positive_growth": "net growth",
    "growth_timescale": "growth time",
    "astronomical_bound_evasion": "astronomical test",
}
ROUTE_SHORT = {
    "transport_flow": "transport",
    "constraint_closure": "constraint",
    "spectral_operator": "operator",
    "boundary_weak_form": "boundary",
    "commutator_incompatibility": "incompatibility",
    "discrete_protocol": "protocol",
}
COLORS = {
    "paper": "#35677d",
    "author": "#7f6a9a",
    "external_reference": "#a4adb3",
    "reference": "#a4adb3",
    "claim": "#d2994f",
    "equation_receipt": "#3f826d",
    "constructor_slot": "#b45f4d",
    "route": "#6d8e3f",
    "verdict": "#202c39",
    "case": "#202c39",
    "direct": "#2f7d5d",
    "candidate": "#d18b31",
    "missing": "#b8bec2",
}


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def portable_path(path: Path | str) -> str:
    resolved = Path(path).resolve()
    try:
        return str(resolved.relative_to(ROOT))
    except ValueError:
        return str(resolved)


def count(value: Any) -> str:
    return f"{int(value or 0):,}"


def latex_escape(value: Any) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(char, char) for char in str(value))


def stable_fraction(key: Any, salt: str = "") -> float:
    digest = hashlib.sha1(f"{salt}:{key}".encode("utf-8", errors="replace")).digest()
    return int.from_bytes(digest[:8], "big") / float(2**64 - 1)


def ensure_matplotlib():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "font.size": 9,
        "axes.titlesize": 12,
        "axes.labelsize": 9,
        "figure.dpi": 140,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    })
    return plt


def save_figure(fig: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, bbox_inches="tight", facecolor="white")


def draw_box(
    ax: Any,
    x: float,
    y: float,
    width: float,
    height: float,
    title: str,
    body: str,
    color: str,
    *,
    title_size: float = 9.2,
    body_size: float = 7.8,
) -> None:
    from matplotlib.patches import FancyBboxPatch

    patch = FancyBboxPatch(
        (x - width / 2, y - height / 2),
        width,
        height,
        boxstyle="round,pad=0.02,rounding_size=0.04",
        facecolor=color,
        edgecolor="#2b3136",
        linewidth=0.9,
    )
    ax.add_patch(patch)
    ax.text(x, y + height * 0.19, title, ha="center", va="center", fontsize=title_size, weight="bold")
    ax.text(x, y - height * 0.13, body, ha="center", va="center", fontsize=body_size, linespacing=1.15)


def arrow(ax: Any, start: Tuple[float, float], end: Tuple[float, float], *, color: str = "#39434a", style: str = "-", width: float = 1.3) -> None:
    ax.annotate(
        "",
        xy=end,
        xytext=start,
        arrowprops={
            "arrowstyle": "-|>",
            "color": color,
            "lw": width,
            "linestyle": style,
            "shrinkA": 2,
            "shrinkB": 2,
        },
    )


def strict_receipt_index(constructor: Dict[str, Any]) -> Dict[str, List[Dict[str, str]]]:
    index: Dict[str, List[Dict[str, str]]] = defaultdict(list)
    for slot in constructor.get("slots") or []:
        slot_id = str(slot.get("slot_id"))
        for item in slot.get("direct_receipts") or []:
            index[str(item.get("node_id"))].append({"slot_id": slot_id, "grade": "direct"})
        candidates = slot.get("candidate_transfer_receipts")
        if candidates is None:
            candidates = slot.get("transfer_receipts") or []
        for item in candidates:
            index[str(item.get("node_id"))].append({"slot_id": slot_id, "grade": "candidate"})
    return index


def plot_evidence_funnel(
    manifest: Dict[str, Any],
    graph: Dict[str, Any],
    constructor: Dict[str, Any],
    gold: Dict[str, Any],
    path: Path,
) -> None:
    plt = ensure_matplotlib()
    fig, ax = plt.subplots(figsize=(10.8, 5.4))
    stages = [
        ("selected papers", int(manifest.get("source_count") or 0), "broad literature search plus complete primary sources"),
        ("equation windows", int(manifest.get("equation_witness_count") or 0), "complete formulas retained with source position and nearby text"),
        ("typed equation nodes", int(graph.get("usable_mechanism_node_count") or len(graph.get("nodes") or [])), "physical quantities and mathematical operation identified"),
        ("case equations", len(strict_receipt_index(constructor)), "equations answer at least one of the six safety questions"),
        ("benchmark equations", int(gold.get("recovered_receipts") or 0), "equations named in advance and recovered from primary sources"),
    ]
    max_value = max(value for _, value, _ in stages) or 1
    y_values = list(reversed(range(len(stages))))
    for idx, ((label, value, detail), y) in enumerate(zip(stages, y_values)):
        width = 8.7 * math.sqrt(max(value, 1) / max_value)
        color = ["#dfe8ec", "#c8dce2", "#a8c9cf", "#79a9a4", "#3f826d"][idx]
        left = -width / 2
        right = width / 2
        next_width = width if idx == len(stages) - 1 else 8.7 * math.sqrt(max(stages[idx + 1][1], 1) / max_value)
        polygon = plt.Polygon(
            [(left, y + 0.42), (right, y + 0.42), (next_width / 2, y - 0.42), (-next_width / 2, y - 0.42)],
            closed=True,
            facecolor=color,
            edgecolor="white",
            linewidth=1.2,
        )
        ax.add_patch(polygon)
        ax.text(0, y, f"{value:,}", ha="center", va="center", weight="bold", fontsize=10)
        ax.text(4.85, y + 0.11, label, ha="left", va="center", weight="bold", fontsize=9.4)
        ax.text(4.85, y - 0.17, detail, ha="left", va="center", fontsize=7.5, color="#2e3a40")
    ax.text(-4.95, 4.45, f"Primary sources present: {gold.get('present_required_sources', 0)}/{gold.get('required_source_count', 0)}", ha="left", fontsize=8.7, weight="bold")
    ax.text(-4.95, 4.15, f"Named equations recovered: {gold.get('recovered_receipts', 0)}/{gold.get('total_receipts', 0)}", ha="left", fontsize=8.7, weight="bold")
    ax.set_title("From a broad literature search to a testable physical chain", loc="left", weight="bold")
    ax.set_xlim(-5.1, 10.2)
    ax.set_ylim(-0.7, 4.7)
    ax.axis("off")
    save_figure(fig, path)
    plt.close(fig)


def _provenance_positions(provenance: Dict[str, Any]) -> Dict[str, Tuple[float, float]]:
    bands = {"author": 0.0, "paper": 1.6, "external_reference": 3.2, "claim": 4.8}
    positions: Dict[str, Tuple[float, float]] = {}
    by_kind: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for item in provenance.get("nodes") or []:
        by_kind[str(item.get("node_type") or "paper")].append(item)
    for kind, items in by_kind.items():
        ordered = sorted(items, key=lambda item: str(item.get("id")))
        n = max(len(ordered), 1)
        for index, item in enumerate(ordered):
            y = 0.03 + 0.94 * ((index + 0.5) / n)
            x = bands.get(kind, 1.6) + (stable_fraction(item.get("id"), "x") - 0.5) * 0.38
            y += (stable_fraction(item.get("id"), "y") - 0.5) * min(0.012, 0.35 / n)
            positions[str(item.get("id"))] = (x, y)
    return positions


def plot_provenance_graph(provenance: Dict[str, Any], path: Path) -> None:
    plt = ensure_matplotlib()
    fig, ax = plt.subplots(figsize=(12.6, 7.0))
    positions = _provenance_positions(provenance)
    relation_style = {
        "author_wrote_paper": ("#7f6a9a", 0.22, 0.45),
        "paper_cites_paper": ("#84939c", 0.11, 0.35),
        "source_makes_claim": ("#c17d35", 0.14, 0.40),
    }
    for item in provenance.get("edges") or []:
        source = positions.get(str(item.get("source")))
        target = positions.get(str(item.get("target")))
        if not source or not target:
            continue
        color, alpha, width = relation_style.get(str(item.get("edge_type")), ("#9aa1a5", 0.10, 0.3))
        ax.plot([source[0], target[0]], [source[1], target[1]], color=color, alpha=alpha, linewidth=width, zorder=1)
    node_size = {"author": 12, "paper": 13, "external_reference": 8, "claim": 7}
    for kind in ("author", "paper", "external_reference", "claim"):
        points = [positions[str(item.get("id"))] for item in provenance.get("nodes") or [] if str(item.get("node_type") or "paper") == kind]
        if not points:
            continue
        ax.scatter(
            [point[0] for point in points],
            [point[1] for point in points],
            s=node_size[kind],
            c=COLORS[kind],
            alpha=0.86 if kind != "claim" else 0.64,
            linewidths=0,
            label=kind.replace("_", " "),
            zorder=3,
        )
    primary_ids = {"0806.3381", "0806.3414", "0807.3349", "0808.1415", "0808.4087", "0901.2948"}
    for source_id in primary_ids:
        if source_id in positions:
            x, y = positions[source_id]
            ax.scatter([x], [y], s=46, facecolors="white", edgecolors="#15232b", linewidths=1.0, zorder=5)
    for x, label in ((0.0, "named authors"), (1.6, "selected papers"), (3.2, "cited papers"), (4.8, "source claims")):
        ax.text(x, 1.035, label, ha="center", va="bottom", fontsize=9.2, weight="bold")
    ax.set_title("Provenance graph: who wrote, cited and claimed what", loc="left", weight="bold")
    ax.text(0.0, -0.050, "Outlined nodes are the six primary LHC-safety papers used by the equation benchmark:", fontsize=8.2)
    ax.text(0.0, -0.085, "0806.3381, 0806.3414, 0807.3349, 0808.1415, 0808.4087 and 0901.2948", fontsize=8.2, weight="bold")
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, -0.15), ncol=4, frameon=False, fontsize=8)
    ax.set_xlim(-0.5, 5.3)
    ax.set_ylim(-0.14, 1.09)
    ax.axis("off")
    save_figure(fig, path)
    plt.close(fig)


def plot_provenance_summary(provenance: Dict[str, Any], path: Path) -> None:
    plt = ensure_matplotlib()
    fig, ax = plt.subplots(figsize=(11.8, 5.8))
    node_counts = Counter(str(item.get("node_type") or "paper") for item in provenance.get("nodes") or [])
    edge_counts = Counter(str(item.get("edge_type") or "unknown") for item in provenance.get("edges") or [])
    claim_counts = Counter(
        str(item.get("claim_type") or "unknown")
        for item in provenance.get("nodes") or []
        if str(item.get("node_type")) == "claim"
    )
    draw_box(ax, 1.2, 3.8, 1.8, 0.95, "papers", f"{node_counts['paper']:,}", "#dce9ee")
    draw_box(ax, 1.2, 2.1, 1.8, 0.95, "named authors", f"{node_counts['author']:,}", "#e7dfee")
    draw_box(ax, 4.0, 3.8, 2.2, 0.95, "source claims", f"{node_counts['claim']:,}", "#f2dfc4")
    draw_box(ax, 4.0, 2.1, 2.2, 0.95, "cited papers", f"{node_counts['external_reference']:,}", "#e4e7e9")
    draw_box(ax, 7.4, 4.3, 2.5, 0.82, "risk claims", f"{claim_counts['risk_claim']:,}", "#f2c7b8")
    draw_box(ax, 7.4, 3.1, 2.5, 0.82, "safety claims", f"{claim_counts['safety_claim']:,}", "#c7dfd4")
    draw_box(ax, 7.4, 1.9, 2.5, 0.82, "astrophysical claims", f"{claim_counts['astrophysical_claim']:,}", "#d6dfec")
    arrow(ax, (2.15, 3.8), (2.85, 3.8), color="#c17d35", width=1.8)
    arrow(ax, (2.15, 3.45), (2.9, 2.45), color="#84939c", width=1.2)
    arrow(ax, (2.15, 2.1), (2.9, 3.35), color="#7f6a9a", width=1.2)
    arrow(ax, (5.15, 3.8), (6.1, 4.2), color="#c17d35")
    arrow(ax, (5.15, 3.8), (6.1, 3.15), color="#c17d35")
    arrow(ax, (5.15, 3.8), (6.1, 2.05), color="#c17d35")
    ax.text(2.55, 4.05, f"{edge_counts['source_makes_claim']:,} claim links", fontsize=7.6, color="#8a5725")
    ax.text(2.3, 2.75, f"{edge_counts['paper_cites_paper']:,} citations", fontsize=7.6, color="#5f6c73")
    ax.text(2.05, 2.95, f"{edge_counts['author_wrote_paper']:,} authorship links", fontsize=7.6, color="#655477", rotation=35)
    ax.text(9.25, 3.1, "Claim prevalence records the debate.\nPhysical compatibility is tested\nin the equation graph.", fontsize=9.0, va="center", linespacing=1.3)
    ax.set_title("Collapsed provenance structure", loc="left", weight="bold")
    ax.set_xlim(0, 11.5)
    ax.set_ylim(1.0, 5.1)
    ax.axis("off")
    save_figure(fig, path)
    plt.close(fig)


def plot_public_knowledge_graph(kg: Dict[str, Any], path: Path) -> None:
    plt = ensure_matplotlib()
    fig, ax = plt.subplots(figsize=(12.8, 7.2))
    x_by_kind = {
        "author": 0.2,
        "paper": 1.4,
        "reference": 2.6,
        "claim": 3.8,
        "claim_family": 5.0,
        "equation_receipt": 6.2,
        "route": 7.4,
        "branch": 8.6,
        "constructor_slot": 9.8,
        "verdict": 11.0,
        "case": 12.0,
    }
    public_kind = {
        "author": "authors",
        "paper": "selected\npapers",
        "reference": "cited\nstudies",
        "claim": "written\nclaims",
        "claim_family": "claim\ntypes",
        "equation_receipt": "equations\nused",
        "route": "calculation\ntypes",
        "branch": "physical\nbranches",
        "constructor_slot": "six\nconditions",
        "verdict": "physical\nresult",
        "case": "public\nanswer",
    }
    by_kind: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for item in kg.get("nodes") or []:
        by_kind[str(item.get("kind") or "paper")].append(item)
    positions: Dict[str, Tuple[float, float]] = {}
    for kind, items in by_kind.items():
        ordered = sorted(items, key=lambda item: str(item.get("id")))
        for idx, item in enumerate(ordered):
            n = max(len(ordered), 1)
            positions[str(item.get("id"))] = (
                x_by_kind.get(kind, 6.0) + (stable_fraction(item.get("id"), "kgx") - 0.5) * 0.18,
                0.04 + 0.92 * ((idx + 0.5) / n),
            )
    important_relations = {
        "author_wrote_paper",
        "paper_cites_paper",
        "source_makes_claim",
        "contains_equation_receipt",
        "direct_receipt_for_slot",
        "candidate_transfer_for_slot",
        "source_local_equation_transition",
        "cross_source_structural_analogue",
        "contributes_to_verdict",
        "answers_case",
    }
    for item in kg.get("edges") or []:
        relation = str(item.get("relation") or "")
        if relation not in important_relations:
            continue
        source = positions.get(str(item.get("source")))
        target = positions.get(str(item.get("target")))
        if not source or not target:
            continue
        is_mechanism = relation in {"contains_equation_receipt", "direct_receipt_for_slot", "candidate_transfer_for_slot", "source_local_equation_transition", "cross_source_structural_analogue", "contributes_to_verdict", "answers_case"}
        ax.plot(
            [source[0], target[0]],
            [source[1], target[1]],
            color="#2f6f62" if is_mechanism else "#9a7a57",
            alpha=0.20 if is_mechanism else 0.055,
            linewidth=0.52 if is_mechanism else 0.25,
            zorder=1,
        )
    for kind, items in by_kind.items():
        points = [positions[str(item.get("id"))] for item in items]
        size = 7 if len(items) > 100 else 18
        if kind in {"constructor_slot", "verdict", "case"}:
            size = 55
        ax.scatter(
            [point[0] for point in points],
            [point[1] for point in points],
            s=size,
            c=COLORS.get(kind, "#82939c"),
            alpha=0.78,
            linewidths=0,
            zorder=3,
        )
    for kind, x in sorted(x_by_kind.items(), key=lambda item: item[1]):
        if by_kind.get(kind):
            ax.text(x, 1.035, f"{public_kind.get(kind, kind.replace('_', ' '))}\n{len(by_kind[kind]):,}", ha="center", va="bottom", fontsize=7.4, weight="bold")
    ax.set_title("How the literature becomes a physical answer", loc="left", weight="bold")
    ax.text(0.15, -0.035, "Brown links trace people, papers, citations and claims. Green links follow calculations into the six physical conditions and the final answer.", fontsize=8.2)
    ax.set_xlim(-0.2, 12.45)
    ax.set_ylim(-0.01, 1.1)
    ax.axis("off")
    save_figure(fig, path)
    plt.close(fig)


def plot_equation_graph(graph: Dict[str, Any], constructor: Dict[str, Any], path: Path) -> None:
    plt = ensure_matplotlib()
    fig, ax = plt.subplots(figsize=(12.8, 7.1))
    receipt_index = strict_receipt_index(constructor)
    node_by_id = {str(item.get("id")): item for item in graph.get("nodes") or []}
    positions: Dict[Tuple[str, str], Tuple[float, float]] = {}
    slot_x = {slot_id: idx for idx, slot_id in enumerate(SLOT_ORDER)}
    slot_examples = {
        "production_selector": r"$\sigma_{\rm BH}$ and threshold",
        "survival_lifetime": r"$\mathrm{d}M/\mathrm{d}t<0$",
        "stopping_capture": r"$\mathrm{d}p/\mathrm{d}\ell$",
        "net_positive_growth": r"$\mathrm{d}M/\mathrm{d}t$",
        "growth_timescale": r"$\int \mathrm{d}M/\dot M$",
        "astronomical_bound_evasion": r"predicted time vs star age",
    }
    slot_rows: Dict[str, List[Tuple[str, Dict[str, str]]]] = defaultdict(list)
    for node_id, assignments in receipt_index.items():
        for assignment in assignments:
            slot_rows[assignment["slot_id"]].append((node_id, assignment))
    for slot_id, rows in slot_rows.items():
        rows.sort(key=lambda pair: (str(node_by_id.get(pair[0], {}).get("source_id")), pair[0], pair[1]["grade"]))
        n = max(len(rows), 1)
        for index, (node_id, assignment) in enumerate(rows):
            y = 0.10 + 0.78 * ((index + 0.5) / n)
            positions[(node_id, slot_id)] = (slot_x[slot_id], y)

    def copies(node_id: str) -> List[Tuple[float, float]]:
        return [point for (candidate, _), point in positions.items() if candidate == node_id]

    for item in graph.get("analog_edges") or []:
        for source in copies(str(item.get("source"))):
            for target in copies(str(item.get("target"))):
                ax.plot([source[0], target[0]], [source[1], target[1]], color="#6b88a1", alpha=0.13, linewidth=0.45, linestyle="--", zorder=1)
    for item in graph.get("edges") or []:
        for source in copies(str(item.get("source"))):
            for target in copies(str(item.get("target"))):
                ax.plot([source[0], target[0]], [source[1], target[1]], color="#32434a", alpha=0.30, linewidth=0.65, zorder=2)
    for (node_id, slot_id), (x, y) in positions.items():
        assignment = next(item for item in receipt_index[node_id] if item["slot_id"] == slot_id)
        node = node_by_id.get(node_id) or {}
        marker = "o" if assignment["grade"] == "direct" else "D"
        color = COLORS[assignment["grade"]]
        ax.scatter([x], [y], s=42 if marker == "o" else 34, marker=marker, c=color, edgecolors="white", linewidths=0.5, zorder=4)
    for slot_id, x in slot_x.items():
        ax.axvline(x, color="#dfe3e5", linewidth=0.7, zorder=0)
        ax.text(x, 0.965, SLOT_SHORT[slot_id], ha="center", va="bottom", fontsize=8.8, weight="bold")
        ax.text(x, 0.925, f"{len(slot_rows.get(slot_id, []))} equations", ha="center", va="bottom", fontsize=7.1, color="#4c5960")
        ax.text(x, 0.885, slot_examples[slot_id], ha="center", va="bottom", fontsize=6.7, color="#44535a")
    ax.scatter([], [], s=42, c=COLORS["direct"], marker="o", label="collider-regime equation")
    ax.scatter([], [], s=34, c=COLORS["candidate"], marker="D", label="equation transferred from another setting")
    ax.plot([], [], color="#32434a", linewidth=0.8, label="next calculation in the same paper")
    ax.plot([], [], color="#6b88a1", linewidth=0.8, linestyle="--", label="same calculation pattern in another paper")
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, -0.11), ncol=4, frameon=False, fontsize=7.5)
    ax.set_title("How the retained equations assemble into the six-condition argument", loc="left", weight="bold")
    ax.set_xlim(-0.35, 5.5)
    ax.set_ylim(0.02, 1.06)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    save_figure(fig, path)
    plt.close(fig)


def plot_constructor(constructor: Dict[str, Any], path: Path) -> None:
    plt = ensure_matplotlib()
    fig, ax = plt.subplots(figsize=(13.4, 6.2))
    titles = {
        "production_selector": "1  FORM",
        "survival_lifetime": "2  SURVIVE",
        "stopping_capture": "3  STOP",
        "net_positive_growth": "4  GAIN MASS",
        "growth_timescale": "5  GROW FAST",
        "astronomical_bound_evasion": "6  PASS THE SKY TEST",
    }
    questions = {
        "production_selector": "Can a collision\nmake it?",
        "survival_lifetime": "Does it outlive\nHawking loss?",
        "stopping_capture": "Can matter\nretain it?",
        "net_positive_growth": "Is accretion larger\nthan every loss?",
        "growth_timescale": "Does growth\nfinish in time?",
        "astronomical_bound_evasion": "Do compact stars\nsurvive the prediction?",
    }
    exits = {
        "production_selector": "below threshold\nno black hole",
        "survival_lifetime": "ordinary branch\nevaporates",
        "stopping_capture": "too much momentum\nescapes matter",
        "net_positive_growth": "net rate $\\leq 0$\nshrinks or stalls",
        "growth_timescale": "growth is too slow\nfor a catastrophe",
        "astronomical_bound_evasion": "old white dwarfs and\nneutron stars survive",
    }
    xs = {slot_id: 1.05 + idx * 2.16 for idx, slot_id in enumerate(SLOT_ORDER)}
    for left, right in zip(SLOT_ORDER, SLOT_ORDER[1:]):
        arrow(ax, (xs[left] + 0.86, 3.65), (xs[right] - 0.86, 3.65), color="#2f6f62", width=1.8)
    for slot_id in SLOT_ORDER:
        x = xs[slot_id]
        draw_box(
            ax,
            x,
            3.65,
            1.78,
            1.32,
            titles[slot_id],
            questions[slot_id],
            "#d8e9e2" if slot_id != "astronomical_bound_evasion" else "#f1dfbd",
            title_size=8.2,
            body_size=7.5,
        )
        arrow(ax, (x, 2.98), (x, 2.20), color="#a65545", width=1.2)
        ax.text(x + 0.13, 2.62, "if no", ha="left", va="center", fontsize=7.2, color="#8e4437", weight="bold")
        draw_box(
            ax,
            x,
            1.68,
            1.78,
            0.78,
            "branch ends",
            exits[slot_id],
            "#f3e7e2" if slot_id != "astronomical_bound_evasion" else "#e6edf3",
            title_size=7.4,
            body_size=6.8,
        )
    ax.text(
        0.15,
        0.47,
        "The dangerous scenario needs six consecutive yes answers.  The standard branch ends at evaporation; the stable branch conflicts with the observed survival of compact stars.",
        fontsize=10.0,
        weight="bold",
        color="#202c39",
    )
    ax.set_title("What would have to happen before a microscopic black hole became dangerous?", loc="left", weight="bold", fontsize=13)
    ax.set_xlim(0, 13.0)
    ax.set_ylim(0.15, 4.65)
    ax.axis("off")
    save_figure(fig, path)
    plt.close(fig)


def plot_transfer_map(constructor: Dict[str, Any], path: Path) -> None:
    plt = ensure_matplotlib()
    fig, ax = plt.subplots(figsize=(12.4, 6.4))
    slots = [item for item in constructor.get("slots") or [] if item.get("candidate_transfer_receipts")]
    measured_equations = {
        "stopping_capture": r"$\mathrm{d}p/\mathrm{d}\ell=-F_{\rm stop}$",
        "net_positive_growth": r"$\dot M_{\rm acc}=\pi\rho vR_{\rm eff}^{2}$",
        "growth_timescale": r"$t_{\rm grow}=\int \mathrm{d}M/\dot M$",
        "astronomical_bound_evasion": r"$t_{\rm NS}\sim20\,{\rm yr}$",
    }
    collider_tests = {
        "stopping_capture": r"$L_{\rm stop}<L_{\rm Earth}$",
        "net_positive_growth": r"$\dot M_{\rm acc}+\dot M_{\rm evap}>0$",
        "growth_timescale": r"$t_{\rm grow}<t_{\rm exposure}$",
        "astronomical_bound_evasion": r"$N_{\rm CR}P_{\rm cap}P_{\rm grow}\ll1$",
    }
    transfer_conditions = {
        "stopping_capture": "how quickly momentum is lost",
        "net_positive_growth": "mass gained minus mass lost",
        "growth_timescale": "time obtained by integrating the growth rate",
        "astronomical_bound_evasion": "predicted effect during a star's lifetime",
    }
    source_titles = {
        "stopping_capture": "stopping law in dense matter",
        "net_positive_growth": "accretion law in dense matter",
        "growth_timescale": "growth law integrated over mass",
        "astronomical_bound_evasion": "compact-star growth prediction",
    }
    test_titles = {
        "stopping_capture": "Does it stop inside Earth?",
        "net_positive_growth": "Does mass increase overall?",
        "growth_timescale": "Does growth finish in time?",
        "astronomical_bound_evasion": "Should old compact stars survive?",
    }
    rows = min(len(slots), 6)
    for idx, slot in enumerate(slots[:rows]):
        y = rows - idx - 0.5
        candidate = (slot.get("candidate_transfer_receipts") or [])[0]
        slot_id = str(slot.get("slot_id"))
        formula = measured_equations.get(slot_id, r"$\mathrm{typed\ source\ equation}$")
        source = str(candidate.get("source_id") or "source")
        draw_box(ax, 1.55, y, 2.65, 0.78, source_titles.get(slot_id, "source equation"), f"{formula}  [{source}]", "#dce8ef", title_size=7.8, body_size=6.5)
        draw_box(ax, 5.55, y, 2.65, 0.78, SLOT_SHORT.get(slot_id, slot_id), transfer_conditions.get(slot_id, "evaluate the same physical quantity"), "#e6edda", title_size=7.8, body_size=6.4)
        draw_box(ax, 9.65, y, 2.65, 0.78, test_titles.get(slot_id, "Collider test"), collider_tests.get(slot_id, "evaluate with LHC parameters"), "#f1dfc4", title_size=7.8, body_size=6.8)
        arrow(ax, (2.9, y), (4.15, y), color="#527c8c")
        arrow(ax, (6.9, y), (8.25, y), color="#6f8a45")
    ax.text(3.55, rows + 0.12, "keep the same physical quantity", ha="center", fontsize=8.0, color="#365865")
    ax.text(7.6, rows + 0.12, "insert Earth or collider conditions and recalculate", ha="center", fontsize=8.0, color="#566c31")
    ax.set_title("Equation transfer from compact stars and matter to the collider case", loc="left", weight="bold")
    ax.set_xlim(0, 11.2)
    ax.set_ylim(0, rows + 0.6)
    ax.axis("off")
    save_figure(fig, path)
    plt.close(fig)


def public_transition_label(item: Dict[str, Any], graph: Dict[str, Any]) -> str:
    nodes = {str(node.get("id")): node for node in graph.get("nodes") or []}
    source = str((nodes.get(str(item.get("source"))) or {}).get("formula") or "")
    target = str((nodes.get(str(item.get("target"))) or {}).get("formula") or "")
    if "sigma_{BH}" in source and "hat\\sigma" in target:
        return "total production -> geometric production area"
    if "acc" in source and "{\\ud p}" in target:
        return "mass intake -> momentum evolution"
    if "4\\pi" in source and "dv}{dr}" in target:
        return "steady mass flow -> force balance"
    if "acc" in source and "\\rem" in target:
        return "mass intake -> capture radius"
    if "evap" in source and "acc" in target:
        return "evaporation -> accretion"
    if "t(R_B" in source and "t_w" in target:
        return "growth stages -> total growth time"
    if "t_{NS" in source and "dM}{dt}" in target:
        return "neutron-star time -> steady mass flow"
    if "dM}{dt}" in source and "v_{EM}" in target:
        return "growth law -> Earth-speed condition"
    source_grades = item.get("source_receipt_grades") or []
    target_grades = item.get("target_receipt_grades") or []

    def grade_slot(grades: Sequence[Any]) -> str:
        if not grades:
            return "supporting equation"
        slot = str(grades[0]).split(":", 1)[0]
        return SLOT_SHORT.get(slot, slot.replace("_", " "))

    return f"{grade_slot(source_grades)} -> {grade_slot(target_grades)}"


def plot_sparse_attention(sparse: Dict[str, Any], graph: Dict[str, Any], path: Path) -> None:
    plt = ensure_matplotlib()
    public_route = {
        "transport_flow": "change / flow",
        "constraint_closure": "constraint",
        "spectral_operator": "transformation",
        "boundary_weak_form": "environment",
        "commutator_incompatibility": "competing laws",
        "discrete_protocol": "sequence",
    }
    transitions = sparse.get("route_transition_attention") or []
    routes = [route for route in ROUTE_SHORT if any(item.get("source_route") == route or item.get("target_route") == route for item in transitions)]
    matrix = [[0.0 for _ in routes] for _ in routes]
    index = {route: idx for idx, route in enumerate(routes)}
    for item in transitions:
        source = str(item.get("source_route"))
        target = str(item.get("target_route"))
        if source in index and target in index:
            matrix[index[source]][index[target]] = float(item.get("attention") or 0.0)
    fig, axes = plt.subplots(1, 2, figsize=(12.4, 5.4), gridspec_kw={"width_ratios": [1.05, 1.25]})
    im = axes[0].imshow(matrix, cmap="YlGnBu", aspect="equal")
    axes[0].set_xticks(range(len(routes)), [public_route[route] for route in routes], rotation=38, ha="right", fontsize=7.5)
    axes[0].set_yticks(range(len(routes)), [public_route[route] for route in routes], fontsize=7.5)
    axes[0].set_xlabel("role of the next equation")
    axes[0].set_ylabel("role of the current equation")
    axes[0].set_title("Information score by equation role", loc="left", fontsize=10.3, weight="bold")
    fig.colorbar(im, ax=axes[0], fraction=0.046, pad=0.04, label="share of information score")
    top = (sparse.get("top_edges") or [])[:8]
    y = list(reversed(range(len(top))))
    values = [float(item.get("attention") or 0.0) for item in top]
    labels = [f"{item.get('source_paper')}  {public_transition_label(item, graph)}" for item in top]
    axes[1].barh(y, values, color="#4d8191")
    axes[1].set_yticks(y, labels, fontsize=7.4)
    axes[1].set_xlabel("normalized information score")
    axes[1].set_title("Eight equation steps carrying the most information", loc="left", fontsize=10.3, weight="bold")
    axes[1].spines[["top", "right"]].set_visible(False)
    fig.suptitle("Which equation-to-equation links carry the safety argument?", x=0.01, ha="left", fontsize=12, weight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    save_figure(fig, path)
    plt.close(fig)


def slot_rows_tex(constructor: Dict[str, Any]) -> str:
    contribution = {
        "production_selector": "formation threshold and production rate",
        "survival_lifetime": "evaporation rate or lifetime",
        "stopping_capture": "momentum loss and capture",
        "net_positive_growth": "mass gained minus mass lost",
        "growth_timescale": "time required to reach a larger scale",
        "astronomical_bound_evasion": "predicted consequence for compact stars",
    }
    rows = []
    for slot in constructor.get("slots") or []:
        slot_id = str(slot.get("slot_id"))
        rows.append(
            f"{latex_escape(SLOT_SHORT.get(slot_id, slot_id))} & "
            f"{int(slot.get('direct_receipt_count') or 0)} & {int(slot.get('candidate_transfer_count') or 0)} & "
            f"{latex_escape(contribution.get(slot_id, 'physical relation'))} \\\\"
        )
    return "\n".join(rows)


def primary_source_rows(gold: Dict[str, Any]) -> str:
    rows = []
    for paper in gold.get("papers") or []:
        recovered = sum(bool(item.get("recovered")) for item in paper.get("receipt_results") or [])
        required = len(paper.get("receipt_results") or [])
        rows.append(
            f"\href{{https://arxiv.org/abs/{paper.get('arxiv_id')}}}{{{latex_escape(paper.get('arxiv_id'))}}} & "
            f"{int(paper.get('equation_count') or 0)} & {recovered}/{required} \\\\"
        )
    return "\n".join(rows)


def source_counts(provenance: Dict[str, Any]) -> Tuple[Counter, Counter]:
    return (
        Counter(str(item.get("node_type") or "paper") for item in provenance.get("nodes") or []),
        Counter(str(item.get("edge_type") or "unknown") for item in provenance.get("edges") or []),
    )


def write_tex(
    paper_dir: Path,
    manifest: Dict[str, Any],
    provenance: Dict[str, Any],
    graph: Dict[str, Any],
    sparse: Dict[str, Any],
    constructor: Dict[str, Any],
    kg: Dict[str, Any],
    gold: Dict[str, Any],
) -> Path:
    paper_dir.mkdir(parents=True, exist_ok=True)
    tex_path = paper_dir / "lhc_black_hole_answer.tex"
    node_counts, edge_counts = source_counts(provenance)
    receipt_index = strict_receipt_index(constructor)
    direct_assignments = sum(
        int(slot.get("direct_receipt_count") or 0) for slot in constructor.get("slots") or []
    )
    candidate_assignments = sum(
        int(slot.get("candidate_transfer_count") or 0) for slot in constructor.get("slots") or []
    )
    missing_slots = [SLOT_SHORT.get(item, item) for item in constructor.get("missing_direct_slots") or []]
    broken_pairs = [
        f"{SLOT_SHORT.get(str(item.get('source_slot')), item.get('source_slot'))} $\\rightarrow$ {SLOT_SHORT.get(str(item.get('target_slot')), item.get('target_slot'))}"
        for item in constructor.get("broken_transitions") or []
    ]
    top_edge = (sparse.get("top_edges") or [{}])[0]
    top_transition_text = public_transition_label(top_edge, graph)
    if top_edge.get("source_paper"):
        top_transition_text += f" in arXiv {top_edge.get('source_paper')}"
    slot_table = slot_rows_tex(constructor)
    source_table = primary_source_rows(gold)
    selection_path = ROOT / "data" / "hf_lhc_selection_500k" / "selection_manifest.json"
    selection = read_json(selection_path) if selection_path.exists() else {}
    template_path = ROOT / "paper" / "lhc_black_hole_article_template.tex"
    if not template_path.exists():
        raise FileNotFoundError(f"Missing public article template: {template_path}")
    replacements = {
        "@@SCANNED_COUNT@@": count(selection.get("scanned") or 0),
        "@@SELECTED_COUNT@@": count(selection.get("selected") or manifest.get("source_count") or 0),
        "@@SOURCE_COUNT@@": count(manifest.get("source_count")),
        "@@CLAIM_COUNT@@": count(node_counts.get("claim")),
        "@@REFERENCE_COUNT@@": count(node_counts.get("external_reference")),
        "@@CITATION_LINKS@@": count(edge_counts.get("paper_cites_paper")),
        "@@CLAIM_LINKS@@": count(edge_counts.get("source_makes_claim")),
        "@@EQUATION_WINDOW_COUNT@@": count(manifest.get("equation_witness_count")),
        "@@GRAPH_NODE_COUNT@@": count(len(graph.get("nodes") or [])),
        "@@USABLE_NODE_COUNT@@": count(graph.get("usable_mechanism_node_count") or 0),
        "@@GRAPH_EDGE_COUNT@@": count(len(graph.get("edges") or [])),
        "@@ANALOG_EDGE_COUNT@@": count(len(graph.get("analog_edges") or [])),
        "@@STRICT_RECEIPT_COUNT@@": count(len(receipt_index)),
        "@@DIRECT_ASSIGNMENTS@@": count(direct_assignments),
        "@@CANDIDATE_ASSIGNMENTS@@": count(candidate_assignments),
        "@@TOTAL_RECEIPTS@@": count(gold.get("total_receipts")),
        "@@RECOVERED_RECEIPTS@@": count(gold.get("recovered_receipts")),
        "@@TOP_TRANSITION@@": latex_escape(top_transition_text),
        "@@SLOT_TABLE@@": slot_table,
        "@@SOURCE_TABLE@@": source_table,
    }
    tex = template_path.read_text(encoding="utf-8")
    for placeholder, value in replacements.items():
        tex = tex.replace(placeholder, value)
    unresolved = sorted({token for token in tex.split() if token.startswith("@@")})
    if unresolved:
        raise ValueError(f"Unresolved public-article placeholders: {unresolved}")
    tex_path.write_text(tex, encoding="utf-8")
    return tex_path

    # Retained temporarily as a fallback record of the earlier technical report.
    tex = rf"""\documentclass[10pt]{{article}}
\usepackage[margin=0.78in]{{geometry}}
\usepackage{{amsmath,amssymb,booktabs,array,tabularx,graphicx,microtype,xcolor}}
\usepackage[hidelinks]{{hyperref}}
\usepackage{{caption,placeins}}
\captionsetup{{font=small,labelfont=bf}}
\setlength{{\parindent}}{{0pt}}
\setlength{{\parskip}}{{0.55em}}
\newcolumntype{{Y}}{{>{{\raggedright\arraybackslash}}X}}
\newcommand{{\ud}}{{\mathrm{{d}}}}
\newcommand{{\yr}}{{\mathrm{{yr}}}}

\title{{Can the Large Hadron Collider produce a dangerous black hole?\\
\large A mechanism-level reconstruction from the scientific literature}}
\author{{Synthetix Institute}}
\date{{}}

\begin{{document}}
\maketitle

\begin{{abstract}}
Microscopic black holes were discussed before the Large Hadron Collider (LHC) began operation because models with a low fundamental gravity scale permit their production in high-energy parton collisions. Catastrophe requires a conjunction of physical conditions: production, survival, retention in matter, positive mass growth, growth within an available time, and consistency with the continued existence of compact stars exposed to higher-energy cosmic rays. We reconstructed these conditions from {count(manifest.get('source_count'))} selected papers and six complete primary sources. A provenance graph records authorship, citations and claims. A second graph links equations by their physical role and source order. The extraction recovered all {count(gold.get('total_receipts'))} prespecified primary-source equations. Production, stopping and accretion equations occur in the collider literature; survival, growth time and astronomical exclusion supply the decisive constraints. No recovered derivation connects all six conditions under one consistent set of assumptions. Hawking loss removes the ordinary short-lived branch, while the stable or metastable branch is constrained by stopping, accretion times and the survival of white dwarfs and neutron stars. Agreement with the independent CERN Safety Study Group report validates the reconstructed mechanism and its conclusion.
\end{{abstract}}

\section{{The physical question}}

The LHC question concerns a sequence of events, rather than the existence of a single exotic object. A microscopic black hole would become dangerous only if it were produced, remained intact, lost enough momentum to stay inside matter, gained mass faster than it lost mass, reached a macroscopic scale within the available time, and escaped the astronomical tests imposed by cosmic rays. Failure of any condition ends the catastrophe branch.

This formulation separates two kinds of evidence. A provenance graph identifies the papers, authors, citations and explicit claims. It establishes responsibility and intellectual dependence. The equation graph identifies which mathematical relation supplies each condition and whether adjacent relations are connected inside a source derivation. The first graph answers who argued for a proposition. The second tests whether the proposition has a complete physical mechanism.

\begin{{figure}}[t]
\centering
\includegraphics[width=0.94\linewidth]{{figures/lhc_evidence_funnel.pdf}}
\caption{{Evidence funnel. The analysis begins with the selected literature and retains equation windows that pass formula and mechanism gates. The primary-source regression recovers {count(gold.get('recovered_receipts'))} of {count(gold.get('total_receipts'))} named equations.}}
\label{{fig:funnel}}
\end{{figure}}

\section{{Evidence base and two linked graphs}}

The static case corpus contains {count(node_counts.get('paper'))} paper nodes, {count(node_counts.get('claim'))} extracted claims and {count(node_counts.get('external_reference'))} cited papers outside the selected set. Its provenance graph has {count(edge_counts.get('paper_cites_paper'))} citation links, {count(edge_counts.get('source_makes_claim'))} paper-to-claim links and {count(edge_counts.get('author_wrote_paper'))} authorship links. The limited author count reflects the metadata retained in this static export; the six primary safety papers carry complete author records.

Figure~\ref{{fig:provenance}} shows the complete graph. It reveals the distribution of positions across the literature and the citation paths by which they are inherited. The collapsed view in Fig.~\ref{{fig:provenance-summary}} shows why claim prevalence alone cannot settle the case: risk, safety and astrophysical statements all coexist, while the physical answer depends on whether their equations compose.

\begin{{figure}}[t]
\centering
\includegraphics[width=\linewidth]{{figures/lhc_provenance_full.pdf}}
\caption{{Full provenance graph. Outlined nodes are the six primary papers used for equation-level regression.}}
\label{{fig:provenance}}
\end{{figure}}

\begin{{figure}}[t]
\centering
\includegraphics[width=0.94\linewidth]{{figures/lhc_provenance_summary.pdf}}
\caption{{Collapsed provenance structure. Claim families summarize the stated positions; citations and authorship record how those positions entered the literature.}}
\label{{fig:provenance-summary}}
\end{{figure}}

The joined graph contains {count(kg.get('node_count'))} typed nodes and {count(kg.get('edge_count'))} edges (Fig.~\ref{{fig:joined}}). Papers connect to equations, equations connect to operational routes, and strict equation contracts connect them to six safety conditions. This arrangement keeps a claim attached to its source while exposing the calculation that can support or contradict it.

\begin{{figure}}[t]
\centering
\includegraphics[width=\linewidth]{{figures/lhc_public_knowledge_graph.pdf}}
\caption{{Joined knowledge graph. Brown edges carry provenance; green edges carry equation evidence into the physical constructor.}}
\label{{fig:joined}}
\end{{figure}}
\FloatBarrier

\section{{The six-condition mechanism}}

\subsection{{Production is conditional on low-scale gravity}}

In the extra-dimensional models studied in the safety literature, the inclusive production cross-section is written as \cite{{GiddingsMangano2008}}
\begin{{equation}}
\sigma_{{\rm BH}}(M>M_{{\min}})=
\sum_{{ij}}\int_{{\tau_{{\min}}}}^1 \ud\tau
\int_\tau^1\frac{{\ud x}}{{x}},f_i(x)f_j(\tau/x)\,
\hat\sigma(\sqrt{{\hat s}}).
\label{{eq:production}}
\end{{equation}}
Here $s$ is the proton--proton centre-of-mass energy squared, $x_1$ and $x_2$ are parton momentum fractions, $\hat s=x_1x_2s$ is the parton-level energy squared, $f_i$ and $f_j$ are parton distribution functions, $M_{{\min}}$ is the assumed minimum black-hole mass, and $\hat\sigma$ is the partonic formation cross-section. The integration begins at
\begin{{equation}}
\tau=x_1x_2>\tau_{{\min}}=\frac{{M_{{\min}}^2}}{{y^2s}},
\label{{eq:threshold}}
\end{{equation}}
where $y$ is the fraction of collision energy trapped behind the horizon. Equations~\eqref{{eq:production}} and \eqref{{eq:threshold}} calculate production after a low fundamental gravity scale and a semiclassical formation law have been assumed. They define the entrance to the safety problem.

\subsection{{Evaporation tests survival}}

For a semiclassical microscopic black hole, Hawking emission gives a negative mass rate. One retained source writes \cite{{Koch2008}}
\begin{{equation}}
\frac{{\ud M}}{{\ud t}}\simeq
-c_{{\rm H}}\frac{{d+1}}{{4R_{{\rm H}}^2}}<0,
\label{{eq:evaporation}}
\end{{equation}}
where $M$ is black-hole mass, $t$ is time, $R_{{\rm H}}$ is horizon radius, $d$ denotes the model's extra spatial dimensions, and $c_{{\rm H}}>0$ collects the emission channels and greybody factors. Equation~\eqref{{eq:evaporation}} removes the ordinary short-lived branch before capture or growth can begin. Stable and metastable models therefore enter as separate hypotheses and must pass the remaining conditions.

\subsection{{A survivor must stop inside matter}}

A fast microscopic object leaves the Earth unless interactions remove sufficient momentum. Giddings and Mangano derive an accretion contribution to momentum loss of the form \cite{{GiddingsMangano2008}}
\begin{{equation}}
\left(\frac{{\ud p}}{{\ud\ell}}\right)_{{\rm ac}}
=-(c_{{p}}-c_{{M}})\,\hat b_{{\min}}^2\pi\rho
\frac{{E^2}}{{M^2}}R^2(\sqrt{{s}}),
\label{{eq:stopping}}
\end{{equation}}
where $p$ and $E$ are momentum and energy, $\ell$ is path length, $\rho$ is the medium density, $R$ is the capture radius, $\hat b_{{\min}}$ is a dimensionless capture impact parameter, and $c_p$ and $c_M$ describe momentum and mass transfer in an encounter. Integrating Eq.~\eqref{{eq:stopping}} over a column density decides whether the object is retained. Cosmic-ray black holes are produced with much larger boosts than LHC products, so compact bodies provide a stringent stopping test.

\subsection{{Accretion must exceed mass loss}}

Once retained, the object must gain mass. The leading capture law is \cite{{Casadio2009,GiddingsMangano2008}}
\begin{{equation}}
\left.\frac{{\ud M}}{{\ud t}}\right|_{{\rm acc}}
=\pi v\rho R_{{\rm eff}}^2,
\label{{eq:accretion}}
\end{{equation}}
where $v$ is speed through matter and $R_{{\rm eff}}$ is the effective capture radius. The relevant balance is
\begin{{equation}}
\frac{{\ud M}}{{\ud t}}=
\left.\frac{{\ud M}}{{\ud t}}\right|_{{\rm evap}}+
\left.\frac{{\ud M}}{{\ud t}}\right|_{{\rm acc}}.
\label{{eq:balance}}
\end{{equation}}
Positive growth requires the right-hand side of Eq.~\eqref{{eq:balance}} to remain positive as $R_{{\rm eff}}$, $v$ and the surrounding material change. A positive rate at one mass supplies a local condition; catastrophe requires the integrated trajectory.

\subsection{{The rate must integrate to a short growth time}}

The general growth time from an initial mass $M_0$ to a macroscopic mass $M_*$ is
\begin{{equation}}
t_{{\rm grow}}(M_0\!\rightarrow\!M_*)=
\int_{{M_0}}^{{M_*}}\frac{{\ud M}}{{\dot M_{{\rm net}}(M)}}.
\label{{eq:growth-time}}
\end{{equation}}
The primary sources evaluate Eq.~\eqref{{eq:growth-time}} through several radius regimes. For a representative six-dimensional white-dwarf calculation, the retained equations give year-to-century stages proportional to $(M_D/M_0)^2/\lambda_D$ \cite{{GiddingsMangano2008}}, where $M_D$ is the fundamental gravity scale and $\lambda_D$ is the dimension-dependent accretion coefficient. These times apply after capture in compact stellar matter. Their transfer to Earth requires new values of density, sound speed, capture radius and exposure time.

\subsection{{Compact stars test the complete stable branch}}

Cosmic rays have collided with dense astronomical bodies at energies at least comparable to those reached at the LHC. A stable species that is produced, stopped and grows should therefore affect old white dwarfs or neutron stars. One retained warped-model calculation gives
\begin{{equation}}
t_{{\rm NS,w}}\sim20\,\yr,
\label{{eq:neutron-star}}
\end{{equation}}
where $t_{{\rm NS,w}}$ is the growth time inside a neutron star in that model \cite{{GiddingsMangano2008}}. The observed survival of neutron stars far beyond this interval excludes the corresponding conjunction of production, capture and rapid growth. The astronomical argument tests the mechanism under a more demanding exposure history than a laboratory run.

\section{{What the constructor finds}}

The strict constructor accepts an equation only when its symbols instantiate a required physical quantity. Text identifies the regime in which the equation is applied. A collider receipt therefore combines a valid equation contract with LHC or collider context. A transfer candidate combines the same contract with an astrophysical or material context. Adjacent conditions compose when the output quantity of one condition is an input to the next and the source graph contains an equation path between their receipts.

\begin{{table}}[t]
\centering
\caption{{Equation evidence assigned to the six necessary conditions.}}
\label{{tab:constructor}}
\begin{{tabularx}}{{\linewidth}}{{YrrY}}
\toprule
Condition & Collider equations & Transfer equations & Interpretation \\
\midrule
{slot_table}
\bottomrule
\end{{tabularx}}
\end{{table}}

The revised graph retains {count(len(graph.get('nodes') or []))} fingerprinted equation nodes, {count(len(graph.get('edges') or []))} source-local transitions and {count(len(graph.get('analog_edges') or []))} cross-paper structural analogues. The constructor identifies {count(len(receipt_index))} distinct strict equation receipts, with {count(direct_assignments)} direct slot assignments and {count(candidate_assignments)} transfer assignments. Collider-regime equations remain absent for {latex_escape(', '.join(missing_slots) if missing_slots else 'no condition')}. The recovered derivations lack links between {', '.join(broken_pairs) if broken_pairs else 'none'}.

The literature contains calculations for each neighboring process, yet no recovered derivation supplies one parameter-consistent path from an LHC collision through survival, capture and rapid macroscopic growth while also satisfying compact-star observations. The dangerous conjunction is therefore unsupported by the processed literature.

\begin{{figure}}[t]
\centering
\includegraphics[width=\linewidth]{{figures/lhc_equation_graph.pdf}}
\caption{{Strict equation receipts organized by physical condition. Solid links are source-local equation paths; dashed links are cross-paper structural analogues.}}
\label{{fig:equation-graph}}
\end{{figure}}

\begin{{figure}}[t]
\centering
\includegraphics[width=\linewidth]{{figures/lhc_physical_constructor.pdf}}
\caption{{Six-condition constructor. Every box and arrow is necessary for the dangerous branch.}}
\label{{fig:constructor}}
\end{{figure}}

\section{{Equation transfer and sparse attention}}

Astrophysical equations enter the collider question through explicit variable substitution. Density, exposure time, velocity and capture radius change; the equation role remains fixed. Figure~\ref{{fig:transfer}} shows this transfer. A compact-star mass rate becomes an LHC test only after $\rho$, $v$, $R_{{\rm eff}}$ and the initial conditions are replaced by collider and terrestrial values. Structural similarity alone supplies a candidate. The transferred equation becomes evidence after dimensional consistency, parameter range and boundary conditions have been checked.

\begin{{figure}}[t]
\centering
\includegraphics[width=\linewidth]{{figures/lhc_transfer_map.pdf}}
\caption{{Transfer map. Each row preserves a physical quantity while changing the substrate and parameter regime.}}
\label{{fig:transfer}}
\end{{figure}}

Sparse attention ranks measured graph transitions by route rarity, transition information and endpoint degree. The highest aggregate transition in this run is {latex_escape(top_transition_text)}. The concentration on operator, transport and closure transitions reflects the structure of the safety argument: a production threshold matters only after it is connected to time evolution, material transport and a growth constraint. Claim frequency does not enter this score.

\begin{{figure}}[t]
\centering
\includegraphics[width=0.96\linewidth]{{figures/lhc_sparse_attention.pdf}}
\caption{{Sparse attention over real equation-graph edges. The matrix shows route-to-route traffic; the bars identify individual high-information transitions.}}
\label{{fig:sparse}}
\end{{figure}}
\FloatBarrier

\section{{Primary-source regression}}

The extraction was tested against twelve named equations chosen before the final graph was built. They cover production, threshold selection, Hawking loss, stopping, accretion, competing mass rates, compact-star growth times and astronomical bounds. All twelve were recovered and passed their typed formula contracts (Table~\ref{{tab:gold}}). This regression catches the failure that affected the earlier export: abstract-scale records preserved topic words while dropping the complete equations needed by the constructor.

\begin{{table}}[t]
\centering
\caption{{Primary-source regression. The review and response papers supply source coverage; the calculation papers supply the named equation receipts.}}
\label{{tab:gold}}
\begin{{tabular}}{{lrr}}
\toprule
arXiv source & Extracted equations & Named receipts \\
\midrule
{source_table}
\bottomrule
\end{{tabular}}
\end{{table}}

\section{{Independent comparison with CERN-2003-001}}

The CERN Safety Study Group report was written independently and was withheld from the equation benchmark. Its human analysis follows the same branch recovered here \cite{{CERN2003}}. It first treats production as conditional on speculative low-scale gravity, then separates rapidly evaporating objects from stable objects. The stable branch is tested through energy loss, capture, accretion and astronomical exposure. The report concludes that LHC collisions present no conceivable danger.

The automated reconstruction reaches the same structure from the arXiv sources. Equations~\eqref{{eq:production}} and \eqref{{eq:threshold}} define conditional production. Equation~\eqref{{eq:evaporation}} removes the standard Hawking branch. Equations~\eqref{{eq:stopping}}--\eqref{{eq:growth-time}} test retention and growth under the stable hypothesis. Equation~\eqref{{eq:neutron-star}} connects that hypothesis to compact-star survival. Agreement in branch order, decisive conditions and final conclusion provides independent validation of the machine-built mechanism graph.

\section{{Conclusion}}

The processed literature gives no support to an LHC black-hole catastrophe. Microscopic production is conditional on speculative gravity models. Standard semiclassical objects evaporate. Stable or metastable alternatives must satisfy a coupled stopping-and-growth calculation and are constrained by the continued survival of compact stars exposed to cosmic-ray collisions. No parameter-consistent derivation satisfies all six requirements.

The two-graph representation explains why this conclusion is inspectable. Provenance locates each claim and citation. The mechanism graph exposes the equations, variables, physical regimes and transitions on which the claim depends. New evidence can update a specific condition without rebuilding the debate as prose.

\FloatBarrier

\begin{{thebibliography}}{{10}}
\bibitem{{CERN2003}} J.-P. Blaizot et al., ``Study of potentially dangerous events during heavy-ion collisions at the LHC: Report of the LHC Safety Study Group,'' CERN-2003-001 (2003), \url{{https://cds.cern.ch/record/613175/files/CERN-2003-001.pdf}}.
\bibitem{{GiddingsMangano2008}} S. B. Giddings and M. L. Mangano, ``Astrophysical implications of hypothetical stable TeV-scale black holes,'' Phys. Rev. D 78, 035009 (2008), \url{{https://arxiv.org/abs/0806.3381}}.
\bibitem{{Ellis2008}} J. Ellis et al., ``Review of the Safety of LHC Collisions,'' J. Phys. G 35, 115004 (2008), \url{{https://arxiv.org/abs/0806.3414}}.
\bibitem{{Koch2008}} B. Koch, M. Bleicher and H. Stoecker, ``Exclusion of black hole disaster scenarios at the LHC,'' Phys. Lett. B 672, 71--76 (2009), \url{{https://arxiv.org/abs/0807.3349}}.
\bibitem{{Plaga2008}} R. Plaga, ``On the potential catastrophic risk from metastable quantum-black holes produced at particle colliders,'' \url{{https://arxiv.org/abs/0808.1415}}.
\bibitem{{Casadio2009}} R. Casadio, S. Fabi and B. Harms, ``Possibility of catastrophic black hole growth in the warped brane-world scenario at the LHC,'' \url{{https://arxiv.org/abs/0901.2948}}.
\bibitem{{Hawking1975}} S. W. Hawking, ``Particle creation by black holes,'' Commun. Math. Phys. 43, 199--220 (1975).
\end{{thebibliography}}

\end{{document}}
"""
    tex_path.write_text(tex, encoding="utf-8")
    return tex_path


def find_gold(run_dir: Path) -> Dict[str, Any]:
    candidates = [
        run_dir / "lhc_gold_benchmark.json",
        ROOT / "outputs" / "lhc_gold_benchmark.json",
    ]
    for path in candidates:
        if path.exists():
            return read_json(path)
    raise FileNotFoundError(
        "Missing lhc_gold_benchmark.json. Run scripts/audit_lhc_gold_benchmark.py first."
    )


def build(args: argparse.Namespace) -> Dict[str, Any]:
    run_dir = Path(args.run_dir)
    paper_dir = Path(args.paper_dir)
    figure_dir = paper_dir / "figures"
    figure_dir.mkdir(parents=True, exist_ok=True)

    manifest = read_json(run_dir / "manifest.json")
    provenance = read_json(run_dir / "provenance_graph.json")
    graph = read_json(run_dir / "equation_mechanism_graph.json")
    sparse = read_json(run_dir / "sparse_attention_audit.json")
    gold = find_gold(run_dir)
    constructor = build_physical_constructor(run_dir)
    write_constructor(run_dir)
    write_discourse_mechanism_attention(run_dir)
    kg = build_public_knowledge_graph(run_dir)
    write_public_knowledge_graph(run_dir)
    constructor_layer = build_constructor_layer_export(
        run_dir=run_dir,
        source_dir=None,
        out_dir=run_dir,
        fingerprint_only=True,
    )

    plot_evidence_funnel(manifest, graph, constructor, gold, figure_dir / "lhc_evidence_funnel.pdf")
    plot_provenance_graph(provenance, figure_dir / "lhc_provenance_full.pdf")
    plot_provenance_summary(provenance, figure_dir / "lhc_provenance_summary.pdf")
    plot_public_knowledge_graph(kg, figure_dir / "lhc_public_knowledge_graph.pdf")
    plot_equation_graph(graph, constructor, figure_dir / "lhc_equation_graph.pdf")
    plot_constructor(constructor, figure_dir / "lhc_physical_constructor.pdf")
    plot_transfer_map(constructor, figure_dir / "lhc_transfer_map.pdf")
    plot_sparse_attention(sparse, graph, figure_dir / "lhc_sparse_attention.pdf")
    tex_path = write_tex(paper_dir, manifest, provenance, graph, sparse, constructor, kg, gold)
    generated_figures = [
        figure_dir / "lhc_evidence_funnel.pdf",
        figure_dir / "lhc_provenance_full.pdf",
        figure_dir / "lhc_provenance_summary.pdf",
        figure_dir / "lhc_public_knowledge_graph.pdf",
        figure_dir / "lhc_equation_graph.pdf",
        figure_dir / "lhc_physical_constructor.pdf",
        figure_dir / "lhc_transfer_map.pdf",
        figure_dir / "lhc_sparse_attention.pdf",
    ]
    portable_constructor_layer = dict(constructor_layer)
    for key in ("json", "markdown"):
        if portable_constructor_layer.get(key):
            portable_constructor_layer[key] = portable_path(portable_constructor_layer[key])
    report = {
        "report_type": "lhc_black_hole_answer",
        "readiness": "usable",
        "tex": portable_path(tex_path),
        "pdf": portable_path(tex_path.with_suffix(".pdf")),
        "figures": [portable_path(path) for path in generated_figures],
        "constructor_layer": portable_constructor_layer,
        "source_run": portable_path(run_dir),
        "source_coverage": gold.get("source_coverage"),
        "receipt_coverage": gold.get("receipt_coverage"),
        "branch_closed": constructor.get("branch_closed"),
    }
    (paper_dir / "lhc_black_hole_answer_manifest.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build the public LHC black-hole mechanism paper.")
    parser.add_argument("--run-dir", default=str(DEFAULT_RUN))
    parser.add_argument("--paper-dir", default=str(ROOT / "paper"))
    return parser


def main() -> None:
    print(json.dumps(build(build_parser().parse_args()), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
