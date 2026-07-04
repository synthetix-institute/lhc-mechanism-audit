#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import random
import sys
import textwrap
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lhc_audit.discourse_mechanism_attention import build_discourse_mechanism_attention, write_discourse_mechanism_attention
from lhc_audit.physical_constructor import build_physical_constructor, write_constructor
from lhc_audit.public_knowledge_graph import build_public_knowledge_graph, write_public_knowledge_graph

DEFAULT_RUN = ROOT / "runs" / "lhc_black_hole_audit_500k_strict"


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def latex_escape(value: Any) -> str:
    text = str(value)
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
    return "".join(replacements.get(ch, ch) for ch in text)


def count(value: Any) -> str:
    return f"{int(value or 0):,}"


def compact(label: str) -> str:
    return str(label).replace("_", " ")


def sorted_counts(mapping: Dict[str, Any]) -> List[Tuple[str, int]]:
    return sorted(((str(k), int(v)) for k, v in (mapping or {}).items()), key=lambda item: (-item[1], item[0]))


def claim_type_counts(provenance: Dict[str, Any]) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for node in provenance.get("nodes") or []:
        if str(node.get("id", "")).startswith("C"):
            key = str(node.get("claim_type") or "unknown")
            out[key] = out.get(key, 0) + 1
    return out


def receipt_nodes(graph: Dict[str, Any]) -> List[Dict[str, Any]]:
    ids = set(graph.get("evidence_grade_case_node_ids") or [])
    return [node for node in graph.get("nodes") or [] if node.get("id") in ids]


def arxiv_url(source: Any) -> str:
    value = str(source or "")
    old_style = ("astro-ph", "cond-mat", "hep-", "math-ph", "quant-ph", "gr-qc")
    if value.startswith(old_style) and "/" not in value:
        prefix = "".join(ch for ch in value if not ch.isdigit())
        suffix = value[len(prefix) :]
        return f"https://arxiv.org/abs/{prefix}/{suffix}"
    return f"https://arxiv.org/abs/{value}"


def math_fragment(text: Any, limit: int = 190) -> str:
    value = " ".join(str(text or "").split())
    if len(value) > limit:
        value = value[: limit - 7].rstrip() + r"\ldots"
    value = value.replace("$", "")
    value = value.replace(r"\,", " ")
    value = value.replace(r"\left", "")
    value = value.replace(r"\right", "")
    return value


def formula_cell(text: Any, limit: int = 190) -> str:
    value = math_fragment(text, limit=limit)
    if len(value) > 68:
        value = value.replace(r" \lesssim ", r"\\ \lesssim ")
        value = value.replace(r" \leq ", r"\\ \leq ")
        value = value.replace(") (", r")\\ (")
        value = value.replace(")^2(", r")^2\\ (")
        value = value.replace(r"M_\odot~", r"M_\odot\\ ")
    if r"\\" in value:
        value = r"\begin{gathered}" + value + r"\end{gathered}"
    return (
        r"\begin{minipage}[t]{\linewidth}\raggedright\scriptsize "
        r"\(\displaystyle " + value + r"\)"
        r"\end{minipage}"
    )


def ensure_matplotlib():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    return plt


def draw_box(ax: Any, x: float, y: float, label: str, value: str = "", color: str = "#eef3f7", w: float = 2.0, h: float = 0.8, fs: float = 9.0) -> None:
    import matplotlib.pyplot as plt

    rect = plt.Rectangle((x - w / 2, y - h / 2), w, h, facecolor=color, edgecolor="#222222", linewidth=1.0)
    ax.add_patch(rect)
    ax.text(x, y + 0.12, label, ha="center", va="center", fontsize=fs, fontweight="bold")
    if value:
        ax.text(x, y - 0.20, value, ha="center", va="center", fontsize=max(7.5, fs - 0.6))


def arrow(ax: Any, a: Tuple[float, float], b: Tuple[float, float], lw: float = 1.4, color: str = "#333333", rad: float = 0.0) -> None:
    ax.annotate(
        "",
        xy=b,
        xytext=a,
        arrowprops={
            "arrowstyle": "->",
            "lw": lw,
            "color": color,
            "connectionstyle": f"arc3,rad={rad}",
        },
    )


def plot_provenance_graph(provenance: Dict[str, Any], path: Path) -> None:
    plt = ensure_matplotlib()
    random.seed(7)
    nodes = provenance.get("nodes") or []
    edges = provenance.get("edges") or []
    node_by_id = {node.get("id"): node for node in nodes}
    claim_nodes = [node for node in nodes if str(node.get("id", "")).startswith("C")]
    source_nodes = [node for node in nodes if not str(node.get("id", "")).startswith("C")]

    family_y = {"astrophysical_claim": 0.72, "risk_claim": 0.43, "safety_claim": 0.18, "unknown": 0.08}
    claim_groups: Dict[str, List[Dict[str, Any]]] = {}
    for claim in claim_nodes:
        claim_groups.setdefault(str(claim.get("claim_type") or "unknown"), []).append(claim)

    pos: Dict[str, Tuple[float, float]] = {}
    for claim_type, group in claim_groups.items():
        base = family_y.get(claim_type, 0.08)
        for i, claim in enumerate(sorted(group, key=lambda x: str(x.get("id")))):
            spread = 0.18 if claim_type == "astrophysical_claim" else 0.08
            y = base + (random.random() - 0.5) * spread
            x = 0.63 + (random.random() - 0.5) * 0.06
            pos[str(claim.get("id"))] = (x, min(0.95, max(0.05, y)))

    source_targets: Dict[str, List[float]] = {}
    for edge in edges:
        target = str(edge.get("target"))
        source = str(edge.get("source"))
        if target in pos:
            source_targets.setdefault(source, []).append(pos[target][1])
    for source in source_nodes:
        sid = str(source.get("id"))
        if sid in source_targets:
            y = sum(source_targets[sid]) / len(source_targets[sid]) + (random.random() - 0.5) * 0.10
        else:
            y = random.random()
        pos[sid] = (0.18 + (random.random() - 0.5) * 0.06, min(0.95, max(0.05, y)))

    colors = {"astrophysical_claim": "#5f8f62", "risk_claim": "#bc6b4c", "safety_claim": "#4f7fa6", "unknown": "#777777"}
    fig, ax = plt.subplots(figsize=(10.6, 5.8))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    for edge in edges:
        source = str(edge.get("source"))
        target = str(edge.get("target"))
        if source not in pos or target not in pos:
            continue
        x0, y0 = pos[source]
        x1, y1 = pos[target]
        ax.plot([x0, x1], [y0, y1], color="#777777", alpha=0.12, lw=0.45, zorder=1)

    sx = [pos[str(node.get("id"))][0] for node in source_nodes if str(node.get("id")) in pos]
    sy = [pos[str(node.get("id"))][1] for node in source_nodes if str(node.get("id")) in pos]
    ax.scatter(sx, sy, s=10, color="#2f5d7c", alpha=0.75, linewidths=0, label="papers", zorder=2)
    for claim_type, group in claim_groups.items():
        xs = [pos[str(node.get("id"))][0] for node in group if str(node.get("id")) in pos]
        ys = [pos[str(node.get("id"))][1] for node in group if str(node.get("id")) in pos]
        ax.scatter(xs, ys, s=16, color=colors.get(claim_type, "#777777"), alpha=0.86, linewidths=0, label=compact(claim_type), zorder=3)

    ax.text(0.18, 0.985, f"{len(source_nodes)} paper nodes", ha="center", va="top", fontsize=10, fontweight="bold")
    ax.text(0.63, 0.985, f"{len(claim_nodes)} claim nodes", ha="center", va="top", fontsize=10, fontweight="bold")
    ax.text(0.40, 0.03, f"{len(edges)} source-to-claim links", ha="center", va="bottom", fontsize=10)
    for label, y in [("astrophysical claims", 0.72), ("risk claims", 0.43), ("safety claims", 0.18)]:
        ax.text(0.88, y, label, ha="left", va="center", fontsize=9)
        ax.plot([0.78, 0.86], [y, y], color="#222222", lw=0.7)
    ax.set_title("Provenance graph: papers linked to extracted claim labels", fontsize=12, fontweight="bold", pad=12)
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def plot_provenance_summary(provenance: Dict[str, Any], path: Path) -> None:
    plt = ensure_matplotlib()
    counts = claim_type_counts(provenance)
    nodes = provenance.get("nodes") or []
    source_count = len([node for node in nodes if not str(node.get("id", "")).startswith("C")])
    claim_count = len([node for node in nodes if str(node.get("id", "")).startswith("C")])
    edge_count = len(provenance.get("edges") or [])
    fig, ax = plt.subplots(figsize=(9.4, 4.5))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5)
    ax.axis("off")
    draw_box(ax, 1.4, 2.55, "papers", count(source_count), "#e7edf6", w=1.7)
    draw_box(ax, 4.0, 2.55, "claim nodes", count(claim_count), "#edf2fa", w=1.9)
    arrow(ax, (2.28, 2.55), (3.03, 2.55), lw=1.5)
    ax.text(2.68, 2.86, f"{edge_count} links", ha="center", fontsize=8.5)
    families = [
        ("astrophysical\nclaims", counts.get("astrophysical_claim", 0), "#e4f0e3", 7.2, 3.7),
        ("risk\nclaims", counts.get("risk_claim", 0), "#f4e2d8", 7.2, 2.55),
        ("safety\nclaims", counts.get("safety_claim", 0), "#e1ecf4", 7.2, 1.4),
    ]
    for label, value, color, x, y in families:
        draw_box(ax, x, y, label, count(value), color, w=2.0)
        arrow(ax, (4.98, 2.55), (6.18, y), lw=1.1, color="#555555", rad=0.10 if y > 2.55 else -0.10)
    ax.text(5.0, 0.38, "Provenance answers: which source contains which kind of statement?", ha="center", fontsize=10)
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def plot_provenance_matrix(provenance: Dict[str, Any], path: Path) -> None:
    plt = ensure_matplotlib()
    import numpy as np

    nodes = {str(node.get("id")): node for node in provenance.get("nodes") or []}
    claim_types = ["astrophysical_claim", "risk_claim", "safety_claim"]
    source_counts: Dict[str, Dict[str, int]] = {}
    for item in provenance.get("edges") or []:
        source = str(item.get("source"))
        claim = nodes.get(str(item.get("target"))) or {}
        claim_type = str(claim.get("claim_type") or "unknown")
        source_counts.setdefault(source, {key: 0 for key in claim_types})
        if claim_type in source_counts[source]:
            source_counts[source][claim_type] += 1
    top_sources = sorted(
        source_counts,
        key=lambda source: (-sum(source_counts[source].values()), source),
    )[:24]
    matrix = np.array([[source_counts[source].get(key, 0) for key in claim_types] for source in top_sources], dtype=float)
    fig, ax = plt.subplots(figsize=(8.8, 7.2))
    ax.set_facecolor("#FFFFFF")
    image = ax.imshow(matrix, cmap="YlOrBr", aspect="auto", vmin=0, vmax=max(1, matrix.max()))
    ax.set_xticks(range(len(claim_types)), [compact(key) for key in claim_types], fontsize=9)
    ax.set_yticks(range(len(top_sources)), top_sources, fontsize=7)
    ax.tick_params(length=0)
    for y in range(matrix.shape[0]):
        for x in range(matrix.shape[1]):
            if matrix[y, x] > 0:
                ax.text(x, y, str(int(matrix[y, x])), ha="center", va="center", fontsize=7.5, color="#1F2430")
    ax.set_title("Claim provenance matrix: which sources carry which claim type", fontsize=12, fontweight="bold", pad=12)
    ax.text(
        0.5,
        -0.10,
        "Rows show the highest-claim sources. Numbers are extracted source-to-claim links, not aggregated topic labels.",
        transform=ax.transAxes,
        ha="center",
        va="top",
        fontsize=8.8,
        color="#4f5561",
    )
    cbar = fig.colorbar(image, ax=ax, shrink=0.72, pad=0.02)
    cbar.ax.set_ylabel("claims from source", fontsize=8)
    cbar.ax.tick_params(labelsize=7)
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def plot_public_knowledge_graph(kg: Dict[str, Any], path: Path) -> None:
    plt = ensure_matplotlib()
    summary = kg.get("summary") or {}
    claim_counts = summary.get("claim_family_counts") or {}
    branch_counts = summary.get("receipt_branch_counts") or {}
    route_counts = summary.get("receipt_route_counts") or {}

    slot_nodes = [
        node for node in kg.get("nodes") or []
        if node.get("kind") == "constructor_slot"
    ]
    slot_nodes.sort(key=lambda item: [
        "production_selector",
        "survival_lifetime",
        "stopping_capture",
        "net_positive_growth",
        "growth_timescale",
        "astronomical_bound_evasion",
    ].index(str(item.get("id")).replace("slot:", "")) if str(item.get("id")).replace("slot:", "") in [
        "production_selector",
        "survival_lifetime",
        "stopping_capture",
        "net_positive_growth",
        "growth_timescale",
        "astronomical_bound_evasion",
    ] else 99)

    fig, ax = plt.subplots(figsize=(12.6, 7.2))
    ax.set_xlim(0, 13.5)
    ax.set_ylim(0, 9)
    ax.axis("off")

    def box(x: float, y: float, label: str, value: str, color: str, w: float = 1.75, h: float = 0.72) -> None:
        draw_box(ax, x, y, label, value, color=color, w=w, h=h, fs=7.8)

    box(0.95, 4.55, "sources", count(summary.get("sources")), "#e7edf6", w=1.55, h=0.85)
    claim_y = {
        "astrophysical_claim": 6.65,
        "risk_claim": 4.55,
        "safety_claim": 2.35,
    }
    claim_color = {
        "astrophysical_claim": "#e2f0df",
        "risk_claim": "#f4dfd4",
        "safety_claim": "#dfeaf3",
    }
    for key, y in claim_y.items():
        box(2.75, y, compact(key), count(claim_counts.get(key)), claim_color[key], w=1.9)
        arrow(ax, (1.72, 4.55), (1.80, y), lw=0.7 + 2.4 * (claim_counts.get(key, 0) / max(1, sum(claim_counts.values()))), color="#5e6570", rad=0.10 if y > 4.55 else -0.10)

    box(4.75, 4.55, "equation\nreceipts", count(summary.get("equation_receipts")), "#f2e6bf", w=1.8, h=0.90)
    for y in claim_y.values():
        arrow(ax, (3.70, y), (3.85, 4.55), lw=0.85, color="#a0a5ad", rad=-0.14 if y > 4.55 else 0.14)

    branch_order = [
        ("production_threshold_branch", "production", "#f2ead7", 6.55),
        ("evaporation_branch", "evaporation", "#e6f0f6", 5.2),
        ("stable_growth_or_capture_branch", "growth/capture", "#f7e7df", 3.85),
        ("astrophysical_black_hole_analogue", "astronomical", "#e9f2e5", 2.5),
    ]
    max_branch = max(1, max(int(v) for v in branch_counts.values() or [1]))
    for key, label, color, y in branch_order:
        value = int(branch_counts.get(key, 0))
        box(6.75, y, label, count(value), color, w=1.75)
        arrow(ax, (5.66, 4.55), (5.82, y), lw=0.7 + 2.0 * value / max_branch, color="#6b717b", rad=0.10 if y > 4.55 else -0.10)

    route_order = [
        ("spectral_operator", "spectral"),
        ("constraint_closure", "closure"),
        ("transport_flow", "transport"),
        ("boundary_weak_form", "boundary"),
    ]
    for i, (key, label) in enumerate(route_order):
        x = 2.9 + i * 1.65
        box(x, 1.05, label, count(route_counts.get(key, 0)), "#eef1f5", w=1.25, h=0.55)
    ax.text(5.35, 1.62, "route signatures in retained equations", ha="center", fontsize=8.7, color="#4f5561")

    slot_y = [7.35, 6.15, 4.95, 3.75, 2.55, 1.35]
    status_color = {"direct_hook": "#f0d98b", "direct_mechanism_receipt": "#8cc084", "transfer_only": "#9ebbd2", "missing": "#d8d8d8"}
    for i, item in enumerate(slot_nodes[:6]):
        status = str(item.get("status") or "")
        label = str(item.get("label") or "").replace("survival against evaporation", "survival").replace("evasion of astronomical survival bounds", "astronomical bound")
        value = f"D {item.get('direct_receipt_count', 0)} / T {item.get('transfer_receipt_count', 0)}"
        box(9.75, slot_y[i], label, value, status_color.get(status, "#e8e8e8"), w=2.25, h=0.64)

    branch_to_slot = [
        (6.75, 6.55, 8.62, 7.35, 1.2),
        (6.75, 5.20, 8.62, 6.15, 1.0),
        (6.75, 3.85, 8.62, 4.95, 1.0),
        (6.75, 3.85, 8.62, 3.75, 1.3),
        (6.75, 3.85, 8.62, 2.55, 1.1),
        (6.75, 2.50, 8.62, 1.35, 1.1),
    ]
    for x0, y0, x1, y1, lw in branch_to_slot:
        arrow(ax, (x0 + 0.88, y0), (x1, y1), lw=lw, color="#6b717b", rad=0.08 if y1 > y0 else -0.08)

    box(12.45, 4.35, "verdict", "broken\nbranch", "#f4dfd4", w=1.35, h=0.90)
    for y in slot_y:
        arrow(ax, (10.90, y), (11.75, 4.35), lw=0.48, color="#6b717b", rad=-0.06)

    ax.text(6.75, 8.65, "Typed knowledge graph: provenance, equations, mechanisms and constructor slots", ha="center", fontsize=12, fontweight="bold")
    ax.text(6.75, 0.28, f"{kg.get('node_count')} typed nodes and {kg.get('edge_count')} typed edges assembled from the static run", ha="center", fontsize=9, color="#4f5561")
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def plot_public_knowledge_graph_full(kg: Dict[str, Any], path: Path) -> None:
    plt = ensure_matplotlib()
    random.seed(23)
    nodes = kg.get("nodes") or []
    edges = kg.get("edges") or []

    by_kind: Dict[str, List[Dict[str, Any]]] = {}
    for node in nodes:
        by_kind.setdefault(str(node.get("kind") or "unknown"), []).append(node)

    pos: Dict[str, Tuple[float, float]] = {}

    def place_group(items: List[Dict[str, Any]], x: float, center: float, span: float, jitter_x: float = 0.08) -> None:
        ordered = sorted(items, key=lambda item: str(item.get("id")))
        n = max(1, len(ordered))
        for i, item in enumerate(ordered):
            if n == 1:
                y = center
            else:
                y = center - span / 2 + span * (i + 0.5) / n
            y += (random.random() - 0.5) * min(0.035, span / max(n, 1))
            pos[str(item.get("id"))] = (x + (random.random() - 0.5) * jitter_x, min(8.35, max(0.65, y)))

    claim_centers = {
        "astrophysical_claim": (6.85, 2.25),
        "risk_claim": (4.55, 1.10),
        "safety_claim": (2.55, 0.70),
        "unknown": (1.40, 0.40),
    }
    claim_groups: Dict[str, List[Dict[str, Any]]] = {}
    for claim in by_kind.get("claim", []):
        claim_groups.setdefault(str(claim.get("claim_type") or "unknown"), []).append(claim)
    for claim_type, group in claim_groups.items():
        center, span = claim_centers.get(claim_type, claim_centers["unknown"])
        place_group(group, 2.35, center, span, jitter_x=0.18)

    claim_target_y: Dict[str, List[float]] = {}
    for edge in edges:
        if edge.get("relation") != "makes_claim":
            continue
        target = str(edge.get("target"))
        source = str(edge.get("source"))
        if target in pos:
            claim_target_y.setdefault(source, []).append(pos[target][1])

    sources = sorted(by_kind.get("source", []), key=lambda item: str(item.get("id")))
    for source in sources:
        sid = str(source.get("id"))
        ys = claim_target_y.get(sid)
        if ys:
            y = sum(ys) / len(ys) + (random.random() - 0.5) * 0.28
        else:
            y = 0.85 + 7.2 * (sources.index(source) + 0.5) / max(1, len(sources))
        pos[sid] = (0.95 + (random.random() - 0.5) * 0.16, min(8.35, max(0.65, y)))

    place_group(by_kind.get("case", []), 0.32, 8.35, 0.10, jitter_x=0.02)

    family_y = {
        "claim_family:astrophysical_claim": 6.85,
        "claim_family:risk_claim": 4.55,
        "claim_family:safety_claim": 2.55,
        "claim_family:unknown": 1.40,
    }
    for family in by_kind.get("claim_family", []):
        fid = str(family.get("id"))
        pos[fid] = (3.55, family_y.get(fid, 1.40))

    branch_centers = {
        "production_threshold_branch": 7.10,
        "evaporation_branch": 5.70,
        "stable_growth_or_capture_branch": 4.20,
        "astrophysical_black_hole_analogue": 2.70,
        "unknown": 1.35,
    }
    receipt_groups: Dict[str, List[Dict[str, Any]]] = {}
    for receipt in by_kind.get("equation_receipt", []):
        labels = receipt.get("branch_labels") or []
        key = str(labels[0]) if labels else "unknown"
        receipt_groups.setdefault(key, []).append(receipt)
    for key, group in receipt_groups.items():
        center = branch_centers.get(key, branch_centers["unknown"])
        place_group(group, 5.15, center, 1.15 if len(group) > 2 else 0.35, jitter_x=0.18)

    route_order = [
        "transport_flow",
        "constraint_closure",
        "spectral_operator",
        "boundary_weak_form",
        "commutator_incompatibility",
        "discrete_protocol",
    ]
    route_y = {name: 7.55 - i * 0.95 for i, name in enumerate(route_order)}
    for route in by_kind.get("route", []):
        key = str(route.get("id")).replace("route:", "")
        pos[str(route.get("id"))] = (6.55, route_y.get(key, 2.0))

    for branch in by_kind.get("branch", []):
        key = str(branch.get("id")).replace("branch:", "")
        pos[str(branch.get("id"))] = (7.80, branch_centers.get(key, 1.35))

    slot_order = [
        "production_selector",
        "survival_lifetime",
        "stopping_capture",
        "net_positive_growth",
        "growth_timescale",
        "astronomical_bound_evasion",
    ]
    slot_y = {name: 7.60 - i * 1.12 for i, name in enumerate(slot_order)}
    for slot in by_kind.get("constructor_slot", []):
        key = str(slot.get("id")).replace("slot:", "")
        pos[str(slot.get("id"))] = (9.65, slot_y.get(key, 1.40))

    place_group(by_kind.get("verdict", []), 11.65, 4.55, 0.15, jitter_x=0.02)

    kind_color = {
        "case": "#1f2430",
        "source": "#2f5d7c",
        "claim": "#5f8f62",
        "claim_family": "#7a8c58",
        "equation_receipt": "#b5792d",
        "route": "#6d7480",
        "branch": "#8a6f3d",
        "constructor_slot": "#4d7a9c",
        "verdict": "#b55242",
    }
    claim_color = {
        "astrophysical_claim": "#5f8f62",
        "risk_claim": "#bc6b4c",
        "safety_claim": "#4f7fa6",
        "unknown": "#777777",
    }
    kind_size = {
        "case": 42,
        "source": 8,
        "claim": 10,
        "claim_family": 68,
        "equation_receipt": 24,
        "route": 58,
        "branch": 62,
        "constructor_slot": 74,
        "verdict": 80,
    }
    rel_style = {
        "selected_for_case": ("#777777", 0.012, 0.22),
        "mentions_case_context": ("#777777", 0.010, 0.22),
        "makes_claim": ("#6c737d", 0.055, 0.32),
        "classified_as": ("#56636b", 0.085, 0.40),
        "contains_equation_receipt": ("#b5792d", 0.40, 0.75),
        "has_route": ("#6d7480", 0.18, 0.48),
        "fills_branch": ("#8a6f3d", 0.34, 0.70),
        "direct_receipt_for_slot": ("#1d5f3f", 0.82, 1.45),
        "transfer_receipt_for_slot": ("#4d7a9c", 0.48, 0.82),
        "source_local_route_transition": ("#343a40", 0.40, 0.72),
        "cross_source_route_analogue": ("#7a4f31", 0.42, 0.72),
        "contributes_to_verdict": ("#b55242", 0.52, 0.95),
    }

    fig, ax = plt.subplots(figsize=(15.2, 8.7))
    ax.set_xlim(-0.15, 12.35)
    ax.set_ylim(0.30, 8.75)
    ax.axis("off")

    lane_specs = [
        (0.95, "papers", len(by_kind.get("source", []))),
        (2.35, "claims", len(by_kind.get("claim", []))),
        (3.55, "claim\nfamilies", len(by_kind.get("claim_family", []))),
        (5.15, "equation\nreceipts", len(by_kind.get("equation_receipt", []))),
        (6.55, "routes", len(by_kind.get("route", []))),
        (7.80, "branches", len(by_kind.get("branch", []))),
        (9.65, "constructor\nslots", len(by_kind.get("constructor_slot", []))),
        (11.65, "verdict", len(by_kind.get("verdict", []))),
    ]
    for x, label, value in lane_specs:
        ax.axvspan(x - 0.42, x + 0.42, color="#f4f6f8", alpha=0.55, zorder=0)
        ax.text(x, 8.55, f"{label}\n{value}", ha="center", va="top", fontsize=8.4, fontweight="bold")

    for edge in edges:
        source = str(edge.get("source"))
        target = str(edge.get("target"))
        if source not in pos or target not in pos:
            continue
        color, alpha, lw = rel_style.get(str(edge.get("relation")), ("#999999", 0.055, 0.32))
        x0, y0 = pos[source]
        x1, y1 = pos[target]
        ax.plot([x0, x1], [y0, y1], color=color, alpha=alpha, lw=lw, zorder=1, solid_capstyle="round")

    for kind, group in by_kind.items():
        xs: List[float] = []
        ys: List[float] = []
        cs: List[str] = []
        for node in group:
            nid = str(node.get("id"))
            if nid not in pos:
                continue
            xs.append(pos[nid][0])
            ys.append(pos[nid][1])
            if kind == "claim":
                cs.append(claim_color.get(str(node.get("claim_type") or "unknown"), "#777777"))
            else:
                cs.append(kind_color.get(kind, "#777777"))
        if xs:
            marker = "D" if kind in {"claim_family", "branch", "constructor_slot"} else "o"
            ax.scatter(xs, ys, s=kind_size.get(kind, 12), c=cs, marker=marker, alpha=0.88, linewidths=0.25, edgecolors="#ffffff", zorder=3)

    for label, y, color in [
        ("astrophysical claim lane", 6.85, "#5f8f62"),
        ("risk claim lane", 4.55, "#bc6b4c"),
        ("safety claim lane", 2.55, "#4f7fa6"),
    ]:
        ax.text(3.02, y, label, ha="left", va="center", fontsize=7.6, color=color)
        ax.plot([2.78, 2.98], [y, y], color=color, lw=1.0, alpha=0.8)

    ax.text(
        6.10,
        0.48,
        f"Full public knowledge graph: {kg.get('node_count')} nodes and {kg.get('edge_count')} typed edges. "
        "Labels are suppressed in the overview; lanes show how provenance narrows into equation receipts and constructor slots.",
        ha="center",
        va="bottom",
        fontsize=9.2,
        color="#3b4048",
    )
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def plot_mechanism_retention(graph: Dict[str, Any], path: Path) -> None:
    plt = ensure_matplotlib()
    fig, ax = plt.subplots(figsize=(10.2, 5.6))
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 6)
    ax.axis("off")
    draw_box(ax, 1.35, 3.1, "equation\nwindows", count(graph.get("source_witness_count")), "#f0e7d7", w=1.95, h=0.90)
    draw_box(ax, 3.65, 3.1, "usable\nequation nodes", count(graph.get("usable_mechanism_node_count")), "#e7efe7", w=2.05, h=0.90)
    draw_box(ax, 6.0, 3.1, "LHC-relevant\nequation nodes", count(graph.get("case_relevant_mechanism_node_count")), "#e4eef4", w=2.15, h=0.90)
    draw_box(ax, 8.35, 3.1, "branch\nreceipts", count(graph.get("evidence_grade_case_mechanism_node_count")), "#f2e6bf", w=1.95, h=0.90)
    for a, b in [((2.34, 3.1), (2.62, 3.1)), ((4.70, 3.1), (4.90, 3.1)), ((7.10, 3.1), (7.38, 3.1))]:
        arrow(ax, a, b, lw=1.8)
    branch_counts = graph.get("case_branch_counts") or {}
    branches = [
        ("production\nthreshold", graph.get("production_threshold_mechanism_node_count", 0), "#f2ead7", 10.0, 5.0),
        ("evaporation", branch_counts.get("evaporation_branch", 0), "#e6f0f6", 10.0, 3.7),
        ("stable growth\nor capture", branch_counts.get("stable_growth_or_capture_branch", 0), "#f7e7df", 10.0, 2.35),
        ("astronomical\nanalogue", graph.get("astrophysical_analogue_mechanism_node_count", 0), "#e9f2e5", 10.0, 1.0),
    ]
    for label, value, color, x, y in branches:
        draw_box(ax, x, y, label, count(value), color, w=1.85, h=0.78, fs=8.5)
        arrow(ax, (9.33, 3.1), (9.05, y), lw=1.1, color="#555555", rad=0.12 if y > 3.1 else -0.12)
    ax.text(5.0, 0.35, "Result: equations accumulate around adjacent astrophysical constraints; no direct survival-capture-growth chain is retained for the collider case.", ha="center", fontsize=10)
    ax.set_title("From processed equations to the retained physical branch receipts", fontsize=12, fontweight="bold", pad=10)
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def plot_mechanism_actual_graph(graph: Dict[str, Any], path: Path) -> None:
    plt = ensure_matplotlib()
    random.seed(11)
    import matplotlib.gridspec as gridspec

    nodes = graph.get("nodes") or []
    receipt_ids = set(graph.get("evidence_grade_case_node_ids") or [])
    case_ids = set(graph.get("case_relevant_node_ids") or [])
    receipt_nodes_local = [node for node in nodes if str(node.get("id")) in case_ids]
    edges = (
        (graph.get("case_source_local_edges") or [])
        + (graph.get("evidence_grade_case_internal_analog_edges") or [])
        + (graph.get("evidence_grade_case_transfer_analog_edges") or [])
    )
    branch_order = [
        ("production_threshold_branch", "production\nthreshold", 0.12, "#d9c58c"),
        ("evaporation_branch", "evaporation /\nlifetime", 0.36, "#8bb6d6"),
        ("stable_growth_or_capture_branch", "growth /\ncapture", 0.62, "#c4745d"),
        ("astrophysical_black_hole_analogue", "astronomical\nbound", 0.86, "#6fa06b"),
    ]
    route_color = {
        "transport_flow": "#277da1",
        "constraint_closure": "#577590",
        "spectral_operator": "#f8961e",
        "boundary_weak_form": "#43aa8b",
        "commutator_incompatibility": "#9d4edd",
        "discrete_protocol": "#f94144",
        "none": "#8d99ae",
    }
    route_label = {
        "transport_flow": "transport",
        "constraint_closure": "closure",
        "spectral_operator": "spectral",
        "boundary_weak_form": "boundary",
        "commutator_incompatibility": "commutator",
        "discrete_protocol": "protocol",
    }
    positions: Dict[str, Tuple[float, float]] = {}
    branch_members: Dict[str, List[Dict[str, Any]]] = {key: [] for key, *_ in branch_order}
    for node in receipt_nodes_local:
        nid = str(node.get("id"))
        labels = (node.get("case_evidence") or {}).get("branch_labels") or []
        placed = False
        for key, *_ in branch_order:
            if key in labels:
                branch_members[key].append(node)
                placed = True
                break
        if not placed:
            branch_members["stable_growth_or_capture_branch"].append(node)
    for key, _label, x, _color in branch_order:
        group = sorted(branch_members.get(key) or [], key=lambda n: str(n.get("source_id") or n.get("id")))
        n = max(1, len(group))
        for i, node in enumerate(group):
            y = 0.12 + 0.76 * (i + 0.5) / n
            positions[str(node.get("id"))] = (x + (random.random() - 0.5) * 0.025, y)

    fig = plt.figure(figsize=(13.4, 6.6))
    spec = gridspec.GridSpec(1, 2, width_ratios=[2.35, 1.0], wspace=0.18)
    ax = fig.add_subplot(spec[0, 0])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    for key, label, x, color in branch_order:
        ax.axvspan(x - 0.07, x + 0.07, color=color, alpha=0.10, zorder=0)
    for edge in edges:
        source, target = str(edge.get("source")), str(edge.get("target"))
        if source not in positions or target not in positions:
            continue
        x0, y0 = positions[source]
        x1, y1 = positions[target]
        color = "#3b3b3b" if edge.get("edge_type") == "source_local_route_transition" else "#9a6538"
        alpha = 0.22 if edge.get("edge_type") == "source_local_route_transition" else 0.30
        lw = 0.75 if edge.get("edge_type") == "source_local_route_transition" else 0.95
        rad = 0.10 if x0 <= x1 else -0.10
        ax.annotate("", xy=(x1, y1), xytext=(x0, y0), arrowprops={"arrowstyle": "-", "lw": lw, "color": color, "alpha": alpha, "connectionstyle": f"arc3,rad={rad}"}, zorder=1)
    for key, label, x, color in branch_order:
        ax.text(x, 0.98, label, ha="center", va="top", fontsize=9.5, fontweight="bold")
        group = branch_members.get(key) or []
        for node in group:
            nid = str(node.get("id"))
            if nid not in positions:
                continue
            routes = node.get("route_signature") or []
            primary = str(routes[0]) if routes else "none"
            sx, sy = positions[nid]
            is_receipt = nid in receipt_ids
            ax.scatter(
                [sx],
                [sy],
                s=58 if is_receipt else 24,
                color=route_color.get(primary, route_color["none"]),
                alpha=0.92 if is_receipt else 0.34,
                edgecolors="#1f2430" if is_receipt else "none",
                linewidths=0.45 if is_receipt else 0,
                zorder=4 if is_receipt else 2,
            )
        for node in [n for n in group if str(n.get("id")) in receipt_ids][:6]:
            nid = str(node.get("id"))
            if nid not in positions:
                continue
            sx, sy = positions[nid]
            ax.text(sx + 0.012, sy, str(node.get("source_id") or nid), ha="left", va="center", fontsize=5.8, alpha=0.82)
        evidence_count = sum(1 for n in group if str(n.get("id")) in receipt_ids)
        ax.text(x, 0.07, f"{len(group)} nodes; {evidence_count} receipts", ha="center", fontsize=8.2, color="#3b4048")
    visible_edges = [edge for edge in edges if str(edge.get("source")) in positions and str(edge.get("target")) in positions]
    visible_source_local = sum(1 for edge in visible_edges if edge.get("edge_type") == "source_local_route_transition")
    visible_analog = len(visible_edges) - visible_source_local
    ax.text(0.50, 0.025, f"{len(receipt_nodes_local)} case-relevant equation nodes; {len(receipt_ids)} evidence-grade receipts; {visible_source_local} source-local transitions; {visible_analog} analogue links visible.", ha="center", fontsize=8.5)
    ax.set_title("A. Equation mechanism graph: case-relevant nodes and retained receipts", fontsize=11.5, fontweight="bold", pad=10)

    ax2 = fig.add_subplot(spec[0, 1])
    route_counts_by_branch: Dict[str, Counter] = {key: Counter() for key, *_ in branch_order}
    for key, *_ in branch_order:
        for node in branch_members.get(key) or []:
            for route in node.get("route_signature") or ["none"]:
                route_counts_by_branch[key][str(route)] += 1
    y = 0
    route_order = ["spectral_operator", "constraint_closure", "transport_flow", "boundary_weak_form", "discrete_protocol", "commutator_incompatibility"]
    branch_names = [label.replace("\n", " ") for _key, label, _x, _color in branch_order]
    max_total = max(1, max(sum(route_counts_by_branch[key].values()) for key, *_ in branch_order))
    for idx, (key, label, _x, _color) in enumerate(branch_order):
        left = 0
        for route in route_order:
            value = route_counts_by_branch[key].get(route, 0)
            if value:
                ax2.barh(idx, value, left=left, color=route_color[route], edgecolor="white", linewidth=0.5)
                left += value
        ax2.text(left + 0.35, idx, f"{len(branch_members.get(key) or [])}", va="center", fontsize=8)
    ax2.set_yticks(range(len(branch_order)))
    ax2.set_yticklabels(branch_names, fontsize=8)
    ax2.invert_yaxis()
    ax2.set_xlim(0, max_total + 4)
    ax2.set_xlabel("route labels attached to plotted equation nodes", fontsize=8)
    ax2.tick_params(axis="x", labelsize=7)
    ax2.set_title("B. Route composition", fontsize=11.5, fontweight="bold", pad=10)
    handles = [plt.Rectangle((0, 0), 1, 1, color=route_color[r]) for r in route_order]
    labels = [route_label[r] for r in route_order]
    ax2.legend(handles, labels, loc="lower right", fontsize=6.8, frameon=False)
    ax2.text(
        0.0,
        -0.22,
        "Interpretation: the graph is dense in spectral/closure/transport roles, but the collider side has only a production hook; survival, capture and growth are supplied as transfer constraints, not as a direct collider derivation.",
        transform=ax2.transAxes,
        ha="left",
        va="top",
        fontsize=8.0,
        wrap=True,
    )
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def plot_physical_tree(graph: Dict[str, Any], path: Path) -> None:
    plt = ensure_matplotlib()
    branch_counts = graph.get("case_branch_counts") or {}
    fig, ax = plt.subplots(figsize=(10.4, 5.7))
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 6)
    ax.axis("off")
    draw_box(ax, 1.0, 3.0, "LHC collision", r"$\sqrt{\hat{s}}$ available", "#edf1f7", w=1.8, h=0.86)
    draw_box(ax, 3.1, 3.0, "production?", r"$\sqrt{\hat{s}}>M_{\min}$", "#f2ead7", w=1.8, h=0.86)
    draw_box(ax, 5.15, 4.65, "evaporates?", r"$dM/dt<0$", "#e6f0f6", w=1.85, h=0.86)
    draw_box(ax, 7.35, 4.65, "short lifetime", r"$\tau_{\rm evap}\ll\tau_{\rm capture}$", "#e6f0f6", w=2.15, h=0.86)
    draw_box(ax, 5.15, 1.55, "stable remnant?", r"$dM/dt\geq 0$", "#f7e7df", w=1.95, h=0.86)
    draw_box(ax, 7.35, 1.55, "capture/growth?", r"$dM/dt=\rho\sigma_{\rm cap}v$", "#f7e7df", w=2.15, h=0.86)
    draw_box(ax, 9.65, 1.55, "astronomical bound", r"$t_{\rm grow}>t_{\rm WD,NS}$", "#e9f2e5", w=2.15, h=0.86)
    arrow(ax, (1.9, 3.0), (2.2, 3.0))
    arrow(ax, (4.0, 3.0), (4.25, 4.45), rad=0.16)
    arrow(ax, (6.1, 4.65), (6.27, 4.65))
    arrow(ax, (4.0, 3.0), (4.23, 1.75), rad=-0.16)
    arrow(ax, (6.15, 1.55), (6.27, 1.55))
    arrow(ax, (8.45, 1.55), (8.57, 1.55))
    ax.text(5.15, 5.35, f"receipts: {branch_counts.get('evaporation_branch', 0)}", ha="center", fontsize=8.5)
    ax.text(7.35, 2.18, f"receipts: {branch_counts.get('stable_growth_or_capture_branch', 0)}", ha="center", fontsize=8.5)
    ax.text(9.65, 2.18, f"receipts: {graph.get('astrophysical_analogue_mechanism_node_count', 0)}", ha="center", fontsize=8.5)
    ax.text(5.55, 0.45, "The catastrophe branch requires production, survival, capture, rapid growth, and failure of the astronomical bound.", ha="center", fontsize=10)
    ax.set_title("Branched physical tree for the LHC black-hole catastrophe claim", fontsize=12, fontweight="bold", pad=10)
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def plot_physical_constructor(constructor: Dict[str, Any], path: Path) -> None:
    plt = ensure_matplotlib()
    status_color = {
        "direct_hook": "#f0d98b",
        "direct_mechanism_receipt": "#8cc084",
        "transfer_only": "#9ebbd2",
        "missing": "#d8d8d8",
    }
    slots = constructor.get("slots") or []
    fig, ax = plt.subplots(figsize=(8.8, 7.2))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis("off")
    y_positions = [8.4, 7.1, 5.8, 4.5, 3.2, 1.9]
    for i, slot in enumerate(slots):
        color = status_color.get(str(slot.get("status")), "#eeeeee")
        label = str(slot.get("label") or "")
        value = (
            f"{str(slot.get('status') or '').replace('_', ' ')}  |  "
            f"direct {slot.get('direct_receipt_count', 0)}  |  "
            f"transfer {slot.get('transfer_receipt_count', 0)}"
        )
        draw_box(ax, 4.2, y_positions[i], label, value, color, w=6.9, h=0.82, fs=9.0)
        ax.text(
            8.05,
            y_positions[i],
            str(slot.get("required_condition") or ""),
            ha="left",
            va="center",
            fontsize=7.5,
            wrap=True,
        )
        if i < len(slots) - 1:
            arrow(ax, (4.2, y_positions[i] - 0.42), (4.2, y_positions[i + 1] + 0.42), lw=1.2)
    ax.text(
        4.2,
        9.55,
        "Required physical branch: every slot must be filled by collider-relevant equations",
        ha="center",
        fontsize=12,
        fontweight="bold",
    )
    ax.text(
        4.2,
        0.55,
        "Result: the corpus contains a production hook and astrophysical transfer equations, but no direct collider chain for lifetime, capture and growth.",
        ha="center",
        fontsize=9.7,
    )
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def plot_constructor_demonstration(constructor: Dict[str, Any], path: Path) -> None:
    plt = ensure_matplotlib()
    slots = constructor.get("slots") or []
    slot_labels = [
        "production\nthreshold",
        "survival\nlifetime",
        "stopping /\ncapture",
        "net mass\ngrowth",
        "growth\ntimescale",
        "astronomical\nbound",
    ]
    slot_templates = [
        r"\sqrt{\hat{s}}>M_{\min}",
        r"\tau_{\rm evap}>\tau_{\rm capture}",
        r"L_{\rm stop}<L_{\rm body}",
        r"\dot{M}_{\rm net}>0",
        r"t_{\rm grow}<t_{\rm exposure}",
        r"N_{\rm CR}P_{\rm cap}P_{\rm grow}\ll 1",
    ]
    status_color = {
        "direct_hook": "#f0d98b",
        "direct_mechanism_receipt": "#8cc084",
        "transfer_only": "#9ebbd2",
        "missing": "#d8d8d8",
    }
    fig, axes = plt.subplots(
        2,
        1,
        figsize=(13.2, 8.0),
        gridspec_kw={"height_ratios": [1.05, 2.2], "hspace": 0.34},
    )
    ax = axes[0]
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 3)
    ax.axis("off")
    steps = [
        (1.2, "1. slots", "production, lifetime\ncapture, growth, bound", "#f2ead7"),
        (4.05, "2. receipts", "formula +\nphysical role", "#edf1f7"),
        (6.95, "3. evidence", "direct collider\nor transfer", "#e6f0f6"),
        (9.95, "4. closure", "all downstream\nslots must close", "#f7e7df"),
        (12.6, "5. verdict", "break after\nproduction", "#f4e2d8"),
    ]
    for x, label, value, color in steps:
        ax.add_patch(plt.Rectangle((x - 1.08, 0.96), 2.16, 1.14, facecolor=color, edgecolor="#222222", linewidth=1.0))
        ax.text(x, 1.75, label, ha="center", va="center", fontsize=8.6, fontweight="bold")
        ax.text(x, 1.27, value, ha="center", va="center", fontsize=7.6, linespacing=1.05)
    for x0, x1 in [(2.35, 2.92), (5.18, 5.82), (8.08, 8.78), (11.08, 11.65)]:
        arrow(ax, (x0, 1.55), (x1, 1.55), lw=1.2, color="#4f5561")
    ax.text(
        7.0,
        2.78,
        "Constructor operation: a danger branch is a sequence of required physical slots, not a count of papers.",
        ha="center",
        fontsize=12,
        fontweight="bold",
    )

    ax2 = axes[1]
    ax2.set_xlim(-0.65, 15.8)
    ax2.set_ylim(-0.8, len(slots) + 0.9)
    ax2.axis("off")
    x_slot, x_template, x_direct, x_transfer, x_status = 0.55, 3.35, 7.15, 9.25, 12.05
    ax2.text(x_slot, len(slots) + 0.45, "physical slot", ha="center", fontsize=9, fontweight="bold")
    ax2.text(x_template, len(slots) + 0.45, "slot equation template", ha="center", fontsize=9, fontweight="bold")
    ax2.text(x_direct, len(slots) + 0.45, "direct\ncollider", ha="center", fontsize=9, fontweight="bold")
    ax2.text(x_transfer, len(slots) + 0.45, "transfer\nanalogue", ha="center", fontsize=9, fontweight="bold")
    ax2.text(x_status, len(slots) + 0.45, "slot status", ha="center", fontsize=9, fontweight="bold")
    max_transfer = max(1, max(int(slot.get("transfer_receipt_count") or 0) for slot in slots))
    for idx, slot in enumerate(slots):
        y = len(slots) - 1 - idx
        label = slot_labels[idx] if idx < len(slot_labels) else str(slot.get("label") or "")
        template = slot_templates[idx] if idx < len(slot_templates) else math_fragment(slot.get("equation_template"), limit=48)
        direct = int(slot.get("direct_receipt_count") or 0)
        transfer = int(slot.get("transfer_receipt_count") or 0)
        status = str(slot.get("status") or "missing")
        row_color = "#f7f8fa" if idx % 2 == 0 else "#ffffff"
        ax2.add_patch(plt.Rectangle((-0.20, y - 0.42), 13.45, 0.84, facecolor=row_color, edgecolor="none", zorder=0))
        ax2.text(x_slot, y, label, ha="center", va="center", fontsize=8.6, fontweight="bold")
        ax2.text(x_template, y, rf"${template}$", ha="center", va="center", fontsize=8.0)
        ax2.barh(y, min(1.0, direct), left=x_direct - 0.42, height=0.30, color="#2d7f5e" if direct else "#d6dbe1")
        ax2.text(x_direct + 0.72, y, str(direct), ha="left", va="center", fontsize=8.5)
        transfer_width = 1.85 * transfer / max_transfer
        ax2.barh(y, transfer_width, left=x_transfer - 0.42, height=0.30, color="#4d7a9c" if transfer else "#d6dbe1")
        ax2.text(x_transfer + 1.65, y, str(transfer), ha="left", va="center", fontsize=8.5)
        status_text = status.replace("_", " ")
        draw_box(ax2, x_status, y, status_text, "", status_color.get(status, "#eeeeee"), w=2.0, h=0.48, fs=7.8)
    ax2.plot([13.55, 13.55], [-0.45, len(slots) - 1.55], color="#b55242", lw=1.1, alpha=0.75)
    ax2.text(
        14.75,
        2.2,
        "no downstream\ndirect collider\nclosure",
        ha="center",
        va="center",
        fontsize=8.4,
        color="#6b2f2a",
    )
    ax2.text(
        6.6,
        -0.64,
        "Direct evidence closes a collider slot. Transfer evidence marks a relevant physical role that still has to be rewritten and tested in collider variables.",
        ha="center",
        fontsize=8.8,
    )
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def plot_discourse_mechanism_proof(attention: Dict[str, Any], path: Path) -> None:
    plt = ensure_matplotlib()
    import numpy as np

    discourse = attention.get("discourse_graph") or {}
    mechanism = attention.get("mechanism_graph") or {}
    constructor = attention.get("constructor") or {}
    claim_counts = discourse.get("claim_type_counts") or {}
    route_counts = mechanism.get("route_counts") or {}
    slots = constructor.get("slot_rows") or []

    fig, axes = plt.subplots(
        1,
        3,
        figsize=(15.4, 5.9),
        gridspec_kw={"width_ratios": [1.05, 1.55, 1.05], "wspace": 0.32},
    )

    ax = axes[0]
    claim_order = ["astrophysical_claim", "risk_claim", "safety_claim"]
    claim_labels = ["astrophysical", "risk", "safety"]
    claim_values = [int(claim_counts.get(key, 0)) for key in claim_order]
    y = np.arange(len(claim_values))
    ax.barh(y, claim_values, color=["#5f8f62", "#bc6b4c", "#4f7fa6"], height=0.54)
    ax.set_yticks(y, claim_labels)
    ax.invert_yaxis()
    ax.set_xlabel("claim nodes")
    ax.set_title("A. Discourse attention", fontsize=11, fontweight="bold")
    ax.grid(axis="x", alpha=0.18)
    for idx, value in enumerate(claim_values):
        ax.text(value + max(claim_values + [1]) * 0.02, idx, f"{value}", va="center", fontsize=9)
    ax.text(0.0, -0.19, "Ranks statements, not physical closure.", transform=ax.transAxes, fontsize=9.0, va="top")

    ax = axes[1]
    slot_label_map = {
        "production_selector": "production",
        "survival_lifetime": "survival",
        "stopping_capture": "capture",
        "net_positive_growth": "growth rate",
        "growth_timescale": "growth time",
        "astronomical_bound_evasion": "astronomical bound",
    }
    slot_labels = [slot_label_map.get(str(slot.get("slot_id")), str(slot.get("label") or "")) for slot in slots]
    direct = [int(slot.get("direct_receipts") or 0) for slot in slots]
    transfer = [int(slot.get("transfer_receipts") or 0) for slot in slots]
    y = np.arange(len(slots))
    ax.barh(y - 0.18, direct, height=0.30, color="#2d7f5e", label="direct collider receipts")
    ax.barh(y + 0.18, transfer, height=0.30, color="#4d7a9c", label="transfer receipts")
    ax.set_yticks(y, slot_labels)
    ax.invert_yaxis()
    ax.set_xlabel("formula receipts")
    ax.set_title("B. Constructor slot attention", fontsize=11, fontweight="bold")
    ax.grid(axis="x", alpha=0.18)
    ax.legend(loc="upper right", fontsize=8.4, frameon=False)
    for idx, (dval, tval) in enumerate(zip(direct, transfer)):
        ax.text(dval + 0.35, idx - 0.18, str(dval), va="center", fontsize=8.4, color="#22533f")
        ax.text(tval + 0.35, idx + 0.18, str(tval), va="center", fontsize=8.4, color="#28475b")
    if slots:
        ax.axhline(0.5, color="#b55242", lw=1.2, alpha=0.85)
        ax.text(0.98, 0.69, "0 direct downstream\ncollider closures", transform=ax.transAxes, ha="right", va="center", fontsize=9.0, color="#6b2f2a")

    ax = axes[2]
    route_order = [
        "spectral_operator",
        "constraint_closure",
        "transport_flow",
        "boundary_weak_form",
        "discrete_protocol",
        "commutator_incompatibility",
    ]
    route_labels = ["spectral", "closure", "transport", "boundary", "protocol", "commutator"]
    route_values = [int(route_counts.get(key, 0)) for key in route_order]
    y = np.arange(len(route_values))
    ax.barh(y, route_values, color="#8a6f9b", height=0.52)
    ax.set_yticks(y, route_labels)
    ax.invert_yaxis()
    ax.set_xlabel("route activations")
    ax.set_title("C. Equation route attention", fontsize=11, fontweight="bold")
    ax.grid(axis="x", alpha=0.18)
    for idx, value in enumerate(route_values):
        ax.text(value + max(route_values + [1]) * 0.02, idx, f"{value}", va="center", fontsize=8.6)
    ax.text(0.0, -0.19, "Tests the operations needed by the branch.", transform=ax.transAxes, fontsize=9.0, va="top")

    fig.suptitle(
        "Sparse-attention proof: discourse finds claims; the mechanism layer tests branch closure",
        fontsize=13,
        fontweight="bold",
        y=1.02,
    )
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def plot_formation_mechanism(path: Path) -> None:
    plt = ensure_matplotlib()
    fig, ax = plt.subplots(figsize=(10.6, 5.7))
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 6)
    ax.axis("off")
    draw_box(ax, 1.3, 3.6, "assumption", "gravity scale near\nTeV", "#f2ead7", w=2.0, h=0.95)
    draw_box(ax, 3.7, 3.6, "parton collision", r"$\sqrt{\hat{s}}=\sqrt{x_1x_2s}$", "#edf1f7", w=2.15, h=0.95)
    draw_box(ax, 6.05, 3.6, "formation test", r"$\sqrt{\hat{s}}>M_{\min}$", "#edf1f7", w=2.0, h=0.95)
    draw_box(ax, 8.35, 4.65, "semiclassical\nestimate", r"$\sigma\sim\pi r_s^2$", "#e8f1e3", w=2.0, h=0.95)
    draw_box(ax, 8.35, 2.55, "quantum\nthreshold", "model dependent", "#f4e2d8", w=2.0, h=0.95)
    draw_box(ax, 10.2, 3.6, "observable", "jets, missing energy,\nHawking products", "#e6f0f6", w=1.65, h=1.05)
    for a, b in [
        ((2.3, 3.6), (2.62, 3.6)),
        ((4.78, 3.6), (5.05, 3.6)),
        ((7.05, 3.6), (7.4, 4.45)),
        ((7.05, 3.6), (7.4, 2.75)),
        ((9.35, 4.65), (9.55, 3.95)),
        ((9.35, 2.55), (9.55, 3.25)),
    ]:
        arrow(ax, a, b, lw=1.35)
    ax.text(5.6, 0.75, "Formation is the first step. Danger also requires survival, stopping, capture and positive growth in matter.", ha="center", fontsize=10)
    ax.set_title("LHC microscopic black-hole formation hypothesis", fontsize=12, fontweight="bold", pad=10)
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def plot_transfer_graph(graph: Dict[str, Any], path: Path) -> None:
    plt = ensure_matplotlib()
    fig, ax = plt.subplots(figsize=(13.2, 7.2))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 8.4)
    ax.axis("off")
    ax.text(7.0, 8.15, "Equation transfer: what must survive when astrophysical black-hole equations are moved to an LHC object", ha="center", fontsize=12, fontweight="bold")

    headers = [
        (1.15, "astrophysical\nreceipt"),
        (3.8, "preserved\nphysical role"),
        (6.55, "LHC variables\nneeded"),
        (9.55, "required\ncollider closure"),
        (12.35, "status in\nretained equations"),
    ]
    for x, label in headers:
        ax.text(x, 7.55, label, ha="center", va="center", fontsize=9.3, fontweight="bold")

    rows = [
        (
            6.55,
            "production",
            "TeV-scale\nformation hook",
            "threshold",
            r"$\sqrt{\hat{s}}>M_{\min}$",
            "production\npossible",
            "1 direct hook",
            "#f2ead7",
            "#f0d98b",
        ),
        (
            5.25,
            "evaporation",
            "mass loss /\nlifetime",
            "lifetime ordering",
            r"$\tau_{\rm evap}>\tau_{\rm capture}$",
            "survival after\nformation",
            "transfer only",
            "#e6f0f6",
            "#9ebbd2",
        ),
        (
            3.95,
            "capture",
            "stopping in\nmatter",
            "capture condition",
            r"$\rho,\ v,\ \sigma_{\rm cap}$",
            "object remains\ninside matter",
            "transfer only",
            "#edf1f7",
            "#9ebbd2",
        ),
        (
            2.65,
            "growth",
            "accretion /\ncompact mass",
            "net growth",
            r"$\dot M=\rho\sigma_{\rm cap}v-P_{\rm evap}/c^2$",
            "positive growth\nfast enough",
            "transfer only",
            "#f7e7df",
            "#9ebbd2",
        ),
        (
            1.35,
            "astronomical\nbound",
            "observed compact\nobject survival",
            "bound evasion",
            r"$t_{\rm grow}>t_{\rm WD,NS}$",
            "no contradiction\nwith observed stars",
            "not closed",
            "#e9f2e5",
            "#f4e2d8",
        ),
    ]
    for y, label, receipt, role, variables, closure, status, left_color, status_color in rows:
        draw_box(ax, 1.15, y, label, receipt, left_color, w=2.0, h=0.88, fs=7.9)
        draw_box(ax, 3.8, y, role, "same role must\nsurvive transfer", "#f2e6bf", w=2.18, h=0.88, fs=7.8)
        draw_box(ax, 6.55, y, "translation", variables, "#edf1f7", w=2.36, h=0.88, fs=7.8)
        draw_box(ax, 9.55, y, "closure test", closure, "#eef1f5", w=2.35, h=0.88, fs=7.8)
        draw_box(ax, 12.35, y, status, "", status_color, w=1.80, h=0.72, fs=8.1)
        for a, b in [
            ((2.17, y), (2.70, y)),
            ((4.90, y), (5.37, y)),
            ((7.75, y), (8.36, y)),
            ((10.75, y), (11.43, y)),
        ]:
            arrow(ax, a, b, lw=1.05, color="#4f5561")

    ax.plot([12.35, 12.35], [1.80, 5.58], color="#b55242", lw=1.0, alpha=0.65)
    ax.text(12.35, 0.45, f"direct collider-safety closures retained: {graph.get('direct_lhc_safety_mechanism_node_count', 0)}", ha="center", fontsize=9.2)
    ax.text(4.1, 0.45, f"astrophysical analogue receipts retained: {graph.get('astrophysical_analogue_mechanism_node_count', 0)}", ha="center", fontsize=9.2)
    ax.text(7.0, 0.10, "Result: the literature supplies adjacent mechanisms and bounds, but it does not supply the continuous collider survival-capture-growth chain.", ha="center", fontsize=9.2)
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def pick_receipt_sample(graph: Dict[str, Any]) -> List[Dict[str, Any]]:
    nodes = receipt_nodes(graph)
    selected: List[Dict[str, Any]] = []
    seen = set()
    preferred = [
        "production_threshold_branch",
        "evaporation_branch",
        "stable_growth_or_capture_branch",
        "astrophysical_black_hole_analogue",
    ]
    for branch in preferred:
        ranked = sorted(
            [
                node
                for node in nodes
                if branch in (node.get("case_evidence") or {}).get("branch_labels", [])
            ],
            key=lambda node: (int(node.get("formula_detail_score") or 0), len(node.get("route_signature") or [])),
            reverse=True,
        )
        for node in ranked:
            key = (node.get("source_id"), node.get("formula"))
            if key in seen:
                continue
            selected.append(node)
            seen.add(key)
            break
    for node in sorted(nodes, key=lambda n: int(n.get("formula_detail_score") or 0), reverse=True):
        key = (node.get("source_id"), node.get("formula"))
        if key not in seen:
            selected.append(node)
            seen.add(key)
        if len(selected) >= 7:
            break
    return selected


def branch_plain(labels: Iterable[str]) -> str:
    mapping = {
        "production_threshold_branch": "production threshold",
        "evaporation_branch": "evaporation or lifetime",
        "stable_growth_or_capture_branch": "stable growth/capture",
        "astrophysical_black_hole_analogue": "astronomical analogue",
    }
    return "; ".join(mapping.get(label, compact(label)) for label in labels) or "case branch"


def receipt_meaning(node: Dict[str, Any]) -> str:
    labels = set((node.get("case_evidence") or {}).get("branch_labels") or [])
    formula = str(node.get("formula") or "").lower()
    if "production_threshold_branch" in labels:
        return "Collider-side selection or threshold condition. It is a production hook; the survival and growth steps remain separate."
    if "evaporation_branch" in labels and ("dot" in formula or "yr" in formula or "tau" in formula):
        return "Mass-change or lifetime evidence. It belongs to the branch that can close the risk by evaporation or slow evolution."
    if "stable_growth_or_capture_branch" in labels:
        return "Growth, capture or compact-object scale evidence. It tests the stable-remnant branch."
    if "astrophysical_black_hole_analogue" in labels:
        return "Astronomical analogue evidence. It constrains whether a similar growth mechanism is compatible with observed compact objects."
    return "Formula receipt used to place one physical step in the branch tree."


def receipt_table(graph: Dict[str, Any]) -> str:
    rows: List[str] = []
    for index, node in enumerate(pick_receipt_sample(graph), start=1):
        source = str(node.get("source_id") or "")
        source_link = rf"\href{{{latex_escape(arxiv_url(source))}}}{{{latex_escape(source)}}}"
        labels = branch_plain((node.get("case_evidence") or {}).get("branch_labels") or [])
        formula = formula_cell(node.get("formula"))
        meaning = latex_escape(receipt_meaning(node))
        receipt_id = rf"\begin{{tabular}}[t]{{@{{}}l@{{}}}}\textbf{{R{index}}}\\ \scriptsize {source_link}\end{{tabular}}"
        rows.append(rf"{receipt_id} & {latex_escape(labels)} & {formula} & {meaning}\tabularnewline")
    return "\n".join(
        [
            r"\small",
            r"\begin{tabularx}{\linewidth}{p{0.16\linewidth}p{0.19\linewidth}p{0.29\linewidth}X}",
            r"\toprule",
            r"Receipt & Branch & Equation receipt & Interpretation\\",
            r"\midrule",
            *rows,
            r"\bottomrule",
            r"\end{tabularx}",
        ]
    )


def cern_alignment_table() -> str:
    rows = [
        (
            r"Production",
            r"\(\sqrt{\hat s}=\sqrt{x_1x_2s}>M_{\min}\sim{\rm few}\,M_D\)",
            r"Aligned with the threshold logic of microscopic black-hole production in TeV-scale gravity models. The corrected variable is the partonic energy \(\hat s\), not the full proton--proton energy \(s\).",
        ),
        (
            r"Four-dimensional black-hole size",
            r"\(R_S=2GM=M/M_P^2\)",
            r"Directly matches the CERN-2003-001 four-dimensional argument: ordinary gravity requires masses far above any accelerator energy.",
        ),
        (
            r"Decay versus accretion",
            r"\(\Gamma_D\simeq T_{\rm BH}^4R_S^2,\quad \Gamma_A\simeq \pi R_S^2\rho\)",
            r"Matches CERN's branch test: growth requires accretion to exceed thermal decay. In the present report this is compressed into the necessary condition \(\dot M_{\rm net}>0\).",
        ),
        (
            r"Higher-dimensional decay",
            r"\(T_{\rm BH}\simeq M_\ast(M_\ast/M)^{1/(1+d)}\)",
            r"Aligned with CERN's extra-dimensional stability calculation. Low-mass black holes evaporate rapidly; only extremely massive objects survive the bound.",
        ),
        (
            r"Constructor growth slot",
            r"\(\dot M_{\rm net}=\rho\,\sigma_{\rm cap}(M,v)\,v-P_{\rm evap}(M)/c^2\)",
            r"Rate-balance form of CERN's decay-versus-accretion test. A collider danger branch must make this balance positive in collider variables.",
        ),
    ]
    body = "\n".join(
        rf"{step} & {equation} & {interpretation}\tabularnewline"
        for step, equation, interpretation in rows
    )
    return "\n".join(
        [
            r"\small",
            r"\begin{tabularx}{\linewidth}{p{0.17\linewidth}p{0.30\linewidth}X}",
            r"\toprule",
            r"Branch step & Equation used here & Evaluation against CERN-2003-001\\",
            r"\midrule",
            body,
            r"\bottomrule",
            r"\end{tabularx}",
        ]
    )


def formation_table() -> str:
    rows = [
        (
            "hep-ph0111052",
            "large-extra-dimension production and high transverse-momentum jet suppression",
            r"\sigma(pp\to{\rm jet}+X)",
            "production/signature model; no growth-in-matter term",
        ),
        (
            "hep-ph0605062",
            "TeV-scale large-extra-dimension black holes",
            r"M_f=1~{\rm TeV};\ \sqrt{s}=14~{\rm TeV};\ M>M_f",
            "requires a low gravity scale; rate is model-dependent",
        ),
        (
            "hep-ph0602129",
            "Higgs production from black-hole evaporation",
            r"T_{\rm BH}\sim 1~{\rm TeV}",
            "decay/signature channel; accretion untested",
        ),
        (
            "0904.0230",
            "TeV black-hole decay products",
            r"p_T^H>100~{\rm GeV};\ |y_{\gamma\gamma}|\leq 1;\ M_P=1~{\rm TeV}",
            "detector selections after assumed production",
        ),
        (
            "0806.3801",
            "many-species microscopic black holes",
            r"M_{\rm Planck}/\sqrt{N}",
            "collider threshold changes only in modified gravity",
        ),
        (
            "0710.4344",
            "species bound and lowered gravitational cutoff",
            r"\Lambda_G\approx M_{\rm Planck}/\sqrt{N}",
            "formation tied to a lowered cutoff beyond Standard Model assumptions",
        ),
    ]
    body = [
        rf"\href{{{latex_escape(arxiv_url(src))}}}{{{latex_escape(src)}}} & {latex_escape(role)} & ${eq}$ & {latex_escape(meaning)}\\"
        for src, role, eq, meaning in rows
    ]
    return "\n".join(
        [
            r"\small",
            r"\begin{tabularx}{\linewidth}{p{0.15\linewidth}p{0.30\linewidth}p{0.26\linewidth}X}",
            r"\toprule",
            r"Source & Formation-side role & Formula or scale & Meaning\\",
            r"\midrule",
            *body,
            r"\bottomrule",
            r"\end{tabularx}",
        ]
    )


def constructor_slots_table(constructor: Dict[str, Any]) -> str:
    rows: List[str] = []
    for slot in constructor.get("slots") or []:
        rows.append(
            rf"{latex_escape(str(slot.get('label') or ''))} & "
            rf"{latex_escape(str(slot.get('status') or '').replace('_', ' '))} & "
            rf"{count(slot.get('direct_receipt_count'))} & "
            rf"{count(slot.get('transfer_receipt_count'))} & "
            rf"{latex_escape(str(slot.get('required_condition') or ''))}\\"
        )
    return "\n".join(
        [
            r"\small",
            r"\begin{tabularx}{\linewidth}{p{0.20\linewidth}p{0.16\linewidth}rrX}",
            r"\toprule",
            r"Physical slot & Status & Direct & Transfer & Required condition\\",
            r"\midrule",
            *rows,
            r"\bottomrule",
            r"\end{tabularx}",
        ]
    )


def counts_table(items: Iterable[Tuple[str, int]]) -> str:
    rows = [rf"{latex_escape(compact(k))} & {count(v)}\\" for k, v in items]
    return "\n".join(
        [
            r"\begin{tabular}{lr}",
            r"\toprule",
            r"Quantity & Count\\",
            r"\midrule",
            *rows,
            r"\bottomrule",
            r"\end{tabular}",
        ]
    )


def write_tex(run_dir: Path, paper_dir: Path, manifest: Dict[str, Any], provenance: Dict[str, Any], graph: Dict[str, Any], sparse: Dict[str, Any], constructor: Dict[str, Any], kg: Dict[str, Any], discourse_attention: Dict[str, Any]) -> Path:
    tex_path = paper_dir / "lhc_black_hole_answer.tex"
    claims = claim_type_counts(provenance)
    branch_counts = graph.get("case_branch_counts") or {}
    route_counts = sorted_counts(graph.get("route_counts") or {})
    provenance_paper_count = len([n for n in provenance.get("nodes", []) if not str(n.get("id", "")).startswith("C")])
    provenance_claim_count = len([n for n in provenance.get("nodes", []) if str(n.get("id", "")).startswith("C")])
    provenance_edge_count = len(provenance.get("edges") or [])
    discourse = discourse_attention.get("discourse_graph") or {}
    mechanism_attention = discourse_attention.get("mechanism_graph") or {}
    constructor_attention = discourse_attention.get("constructor") or {}

    tex = rf"""\documentclass[11pt]{{article}}
\usepackage[a4paper,margin=0.82in]{{geometry}}
\usepackage{{graphicx}}
\usepackage{{amsmath,amssymb}}
\usepackage{{booktabs}}
\usepackage{{tabularx}}
\usepackage{{array}}
\usepackage{{hyperref}}
\usepackage{{caption}}
\usepackage{{float}}
\usepackage{{pdflscape}}
\hypersetup{{hidelinks}}
\graphicspath{{{{figures/}}}}

\title{{Do the arXiv papers support a dangerous LHC black-hole scenario?}}
\author{{Processed arXiv evidence: claims, equations and physical transfer}}
\date{{}}

\begin{{document}}
\maketitle

\begin{{abstract}}
The dangerous LHC black-hole scenario fails at the mechanism level. A catastrophe
requires one continuous physical branch: production in a collision, survival
against evaporation, stopping or capture in matter, net positive mass growth,
and evasion of astronomical survival bounds. The claim graph contains
{count(len(provenance.get('nodes') or []))} nodes and
{count(len(provenance.get('edges') or []))} source-to-claim links. It places the
source set: mostly astrophysical black-hole material, a smaller risk surface, and
very few explicit safety statements. The equation graph tests the physical
branch. From {count(graph.get('source_witness_count'))} processed equation
windows, {count(graph.get('usable_mechanism_node_count'))} usable equation nodes
remain; {count(graph.get('case_relevant_mechanism_node_count'))} touch the LHC
black-hole question and {count(graph.get('evidence_grade_case_mechanism_node_count'))}
remain as branch receipts. Those receipts populate astronomical growth,
accretion, compact-object and lifetime constraints, plus one collider selection
hook. The collider-growth branch is broken at the required links from production
to survival, from survival to capture, and from capture to fast positive growth.
The scientific result is a transfer calculation: astrophysical rate and bound
equations constrain any microscopic collider-product scenario, and the retained
equations stop before the missing bridge.
\end{{abstract}}

The public question is usually phrased as whether the LHC could make a dangerous
black hole. That wording hides the physics. A dangerous outcome would require a
sequence of events, not a single production claim: a microscopic object must be
created in a parton collision, survive evaporation, slow down or be captured by
matter, accrete faster than it loses mass, and remain compatible with the
survival of astronomical bodies exposed to much higher natural collision
histories. The analysis below turns that sequence into an equation-level
constructor. The claim graph shows what the literature says; the mechanism graph
tests which steps are actually filled by formulas and where the physical branch
stops.

\section{{Mechanism verdict}}

A dangerous LHC branch must connect a collider event to a long-lived object,
then to stopping or capture in matter, then to positive mass growth on a relevant
time scale. The retained equations fill adjacent astrophysical branches:
accretion rates, luminosity limits, compact-object masses, merger parameters and
survival constraints. The collider side contributes a threshold or event-selection
hook. The later growth chain remains absent.

The physical question is therefore concrete. Let \(s\) denote the squared
proton--proton centre-of-mass energy at the collider, \(x_1\) and \(x_2\) the
parton momentum fractions, and \(\hat s=x_1x_2s\) the parton-level squared
centre-of-mass energy. Let \(M_D\) denote the fundamental gravitational scale in
the low-scale-gravity model, \(M_{{\min}}\) the minimum black-hole mass assumed by
that model, \(M\) the mass of the candidate microscopic black hole,
\(\tau_{{\rm evap}}\) its evaporation lifetime, \(\tau_{{\rm capture}}\) the time
required for stopping or capture in matter, \(\rho\) the density of the material
it traverses, \(\sigma_{{\rm cap}}(M,v)\) the effective capture or accretion
cross-section, \(v\) the speed relative to the material, \(P_{{\rm evap}}(M)\)
the evaporation power, and \(c\) the speed of light. In this notation the
minimum danger chain is
\begin{{equation}}
\sqrt{{\hat s}}=\sqrt{{x_1x_2s}}>M_{{\min}}\sim {{\rm few}}\,M_D,
\qquad
\tau_{{\rm evap}}>\tau_{{\rm capture}},
\qquad
\dot M_{{\rm net}}=\rho\,\sigma_{{\rm cap}}(M,v)\,v-\frac{{P_{{\rm evap}}(M)}}{{c^2}}>0 .
\label{{eq:danger-chain}}
\end{{equation}}
Equation~\eqref{{eq:danger-chain}} states the three required steps: the
collision can access the new-gravity channel, the object survives long enough
to be captured, and the net mass-growth rate \(\dot M_{{\rm net}}\) is positive.
The chain also requires a growth time short enough to matter and no
contradiction with compact-object survival. The retained equations leave this
chain open.

\section{{Physical constructor}}

In this report, a constructor is an ordered physical branch with acceptance
tests at each step. It is closer to a derivation recipe than to a topic label:
each step must supply a quantity that the next step can use. For the LHC
black-hole question the constructor has six slots. The production slot asks
whether a parton collision can enter the low-scale-gravity channel. The survival
slot asks whether the object lives long enough to interact with matter. The
capture slot asks whether it can stop or remain bound inside matter. The growth
slot asks whether intake exceeds evaporation. The timescale slot asks whether
the integrated growth is fast enough to matter. The astronomical-bound slot asks
whether the same mechanism would contradict the survival of dense astronomical
objects.

Each slot is represented by a minimal equation condition:
\begin{{align}}
&\text{{production:}}          && \sqrt{{\hat s}}>M_{{\min}}, \nonumber\\
&\text{{survival:}}            && \tau_{{\rm evap}}>\tau_{{\rm capture}}, \nonumber\\
&\text{{capture:}}             && L_{{\rm stop}}<L_{{\rm body}}, \nonumber\\
&\text{{net growth:}}          && \dot M_{{\rm net}}>0, \nonumber\\
&\text{{growth time:}}         && t_{{\rm grow}}<t_{{\rm exposure}}, \nonumber\\
&\text{{astronomical closure:}}&& N_{{\rm CR}}P_{{\rm cap}}P_{{\rm grow}}\ll 1 .
\label{{eq:constructor-slots}}
\end{{align}}
Here \(L_{{\rm stop}}\) is the stopping length, \(L_{{\rm body}}\) the material
length scale, \(t_{{\rm grow}}\) the time required for dangerous growth,
\(t_{{\rm exposure}}\) the relevant exposure time, \(N_{{\rm CR}}\) the number of
cosmic-ray production trials in the astronomical comparison, \(P_{{\rm cap}}\)
the probability of capture and \(P_{{\rm grow}}\) the probability of subsequent
growth. These conditions are intentionally minimal. They specify what must be
shown before the scenario can become a closed physical branch.

The constructor then classifies equation receipts. A direct receipt is a formula
written in collider variables for the slot it fills. A transfer receipt is a
formula from an adjacent astrophysical setting that carries the same physical
role, such as accretion rate, lifetime, capture scale or compact-object bound.
Transfer receipts are valuable because they show the relevant physics and the
variables that must be translated. Branch closure, however, requires direct
collider receipts for the downstream slots and composability between slots:
production must feed survival, survival must feed capture and capture must feed
positive growth. In the retained corpus, production has a direct hook; the
downstream slots are transfer-only.

\begin{{figure}}[H]
\centering
\includegraphics[width=0.98\linewidth]{{lhc_physical_constructor.pdf}}
\caption{{Physical constructor for the danger branch. The first slot has a
collider-side production hook. The downstream slots are filled only by transfer
equations from astrophysical black-hole, accretion or compact-object papers.
Thus the continuous branch from LHC production to survival, capture and fast
growth is not present in the retained equations.}}
\label{{fig:constructor}}
\end{{figure}}

\begin{{table}}[H]
\caption{{Evidence status of each required physical slot.}}
\label{{tab:constructor}}
{constructor_slots_table(constructor)}
\end{{table}}

\clearpage
\begin{{landscape}}
\begin{{figure}}[p]
\centering
\includegraphics[width=0.98\linewidth,height=0.78\textheight,keepaspectratio]{{lhc_constructor_demonstration.pdf}}
\caption{{How the constructor works. The upper row shows the operation:
define the physical slots, match formula receipts to those slots, separate
direct collider evidence from transfer analogues and then test whether the
branch closes continuously. The lower matrix shows the actual fill state for
this run. Production has one direct hook; every downstream safety-critical slot
is transfer-only, so the danger branch does not close.}}
\label{{fig:constructor-demo}}
\end{{figure}}
\end{{landscape}}
\clearpage

\section{{Discourse graph and mechanism graph}}

The same source set gives two different graphs. The first graph is a discourse
graph: {count(discourse.get('paper_nodes'))} paper nodes, {count(discourse.get('claim_nodes'))}
claim nodes and {count(discourse.get('source_to_claim_edges'))}
source-to-claim links. It records attribution and coverage: most extracted
statements in this run are astrophysical black-hole statements, with a smaller
risk surface and very few explicit safety statements.

The second graph is an equation mechanism graph. It starts from formula windows,
keeps the windows that contain usable mathematical structure, assigns
operator/substrate constructor roles, and asks whether those formulas fill the
physical slots in Fig.~\ref{{fig:constructor}}. Its sparse attention is not over
words. It is over physical roles: threshold, lifetime, capture, growth and
astronomical-bound closure. This graph contains
{count(mechanism_attention.get('evidence_grade_receipts'))} evidence-grade
receipts for the case layer. The decisive comparison is that the discourse graph
can count claim families, whereas the mechanism graph can test branch closure.
For the required downstream slots, the constructor finds
{count(constructor_attention.get('direct_downstream_slots'))} direct collider
closures and {count(constructor_attention.get('transfer_only_downstream_slots'))}
transfer-only slots.

\clearpage
\begin{{landscape}}
\begin{{figure}}[p]
\centering
\includegraphics[width=0.98\linewidth,height=0.72\textheight,keepaspectratio]{{lhc_discourse_mechanism_proof.pdf}}
\caption{{Discourse graph versus mechanism graph on the same source set. Panel
A shows claim-family attention: it ranks statements. Panel B shows the physical
constructor: it tests whether required equation slots are filled by direct
collider receipts or only by transfer analogues. Panel C shows route attention
inside the retained equation receipts. The claim graph locates statements; the
mechanism graph identifies the missing physical bridge from production to
survival, capture and growth.}}
\label{{fig:discourse-mechanism-proof}}
\end{{figure}}
\end{{landscape}}
\clearpage

The comparison changes the question from literature coverage to physical
closure. Source and claim counts show where statements occur. The constructor
asks a stricter question: which formulas occupy the required physical roles, and
do those roles connect into a continuous collider branch? Clean formula
extraction, operator/substrate constructor roles, sparse route attention and
slot-by-slot assembly give that answer directly.

\begin{{figure}}[H]
\centering
\includegraphics[width=0.98\linewidth]{{lhc_public_knowledge_graph.pdf}}
\caption{{Typed knowledge graph assembled from the static run. It contains
{count(kg.get('node_count'))} typed nodes and {count(kg.get('edge_count'))}
typed edges. The left side is provenance; the middle is the retained equation
layer; the right side is the constructor layer that decides whether the
danger branch closes.}}
\label{{fig:public-kg}}
\end{{figure}}

\clearpage
\begin{{landscape}}
\begin{{figure}}[p]
\centering
\includegraphics[width=0.98\linewidth,height=0.78\textheight,keepaspectratio]{{lhc_public_knowledge_graph_full.pdf}}
\caption{{Full public knowledge graph. Each point is one node in the
{count(kg.get('node_count'))}-node graph. The dense paper and claim layers
remain on the left; sparse equation receipts, route labels, physical branches
and constructor slots appear on the right. Labels are omitted in this overview
because the graph is topology-first; source names and formulas are given in the
receipt tables and machine-readable JSON. The coordinates are layout
coordinates only: horizontal position separates node layers, while vertical
position groups claim families and physical branches and spreads overlapping
nodes.}}
\label{{fig:public-kg-full}}
\end{{figure}}
\end{{landscape}}
\clearpage

\section{{How formation is supposed to work}}

The LHC formation hypothesis used in these papers belongs to low-scale gravity
models. The fundamental gravitational scale is lowered to the TeV range, for
example by large extra dimensions or many particle species. The collider energy
\(\sqrt{{s}}\) is shared by two partons carrying momentum fractions \(x_1\) and
\(x_2\). The parton-level squared centre-of-mass energy is \(\hat{{s}}\), defined
by
\begin{{equation}}
\sqrt{{\hat s}}=\sqrt{{x_1x_2s}} .
\label{{eq:parton-energy}}
\end{{equation}}
Formation is then treated as possible only if the parton-level energy exceeds a
model-dependent minimum black-hole mass \(M_{{\min}}\). In the collider papers
this threshold is usually expressed relative to \(M_D\), the fundamental
gravitational scale:
\begin{{equation}}
\sqrt{{\hat s}}>M_{{\min}}\sim {{\rm few}}\,M_D .
\label{{eq:formation-threshold}}
\end{{equation}}
In the semiclassical picture the production cross-section \(\sigma_{{\rm form}}\)
is estimated from a higher-dimensional horizon radius \(r_s\). Here
\(M_{{\rm BH}}\) is the produced black-hole mass and \(n\) is the number of extra
dimensions:
\begin{{equation}}
\sigma_{{\rm form}}\sim \pi r_s^2(M_{{\rm BH}},M_D,n).
\label{{eq:geometric-cross-section}}
\end{{equation}}
Close to threshold, Eq.~\eqref{{eq:geometric-cross-section}} becomes a
quantum-gravity assumption rather than a clean classical black-hole calculation.
Formation papers can predict detector signatures; a danger argument still
requires survival, capture and positive growth.

\begin{{figure}}[H]
\centering
\includegraphics[width=0.98\linewidth]{{lhc_formation_mechanism.pdf}}
\caption{{Formation-side mechanism. The LHC black-hole hypothesis begins with a
low gravitational scale, then applies a parton-level threshold. Above threshold,
some papers use a geometric cross-section estimate; near threshold the object is
model-dependent quantum gravity. The later growth-in-matter branch is a separate
physical requirement.}}
\label{{fig:formation}}
\end{{figure}}

\begin{{table}}[H]
\caption{{Formation-side sources and what they actually support.}}
\label{{tab:formation}}
{formation_table()}
\end{{table}}

The formation-side result is specific. The selected literature contains papers
on possible production and possible decay signatures of TeV-scale black holes.
These formulas support search channels: high-\(p_T\) suppression, Hawking-like
decay products, heavy-particle production and model-dependent threshold
behavior. The safety-critical steps remain separate: survival, stopping, capture
and sustained accretion. Formation occupies the first box in
Fig.~\ref{{fig:physical-tree}}.

\begin{{figure}}[H]
\centering
\includegraphics[width=0.98\linewidth]{{lhc_physical_tree.pdf}}
\caption{{Physical knowledge tree for the LHC black-hole catastrophe claim. A
dangerous branch requires all steps: production, survival, capture, fast growth
and failure of astronomical bounds. The retained equations populate the adjacent
astronomical and growth/capture parts of this tree.}}
\label{{fig:physical-tree}}
\end{{figure}}

\begin{{figure}}[H]
\centering
\includegraphics[width=0.98\linewidth]{{lhc_mechanism_retention.pdf}}
\caption{{Equation funnel for the LHC black-hole question. The graph starts with
{count(graph.get('source_witness_count'))} equation windows and retains
{count(graph.get('usable_mechanism_node_count'))} usable equation nodes. Of these,
{count(graph.get('case_relevant_mechanism_node_count'))} are relevant to the
LHC black-hole question and {count(graph.get('evidence_grade_case_mechanism_node_count'))}
remain as branch receipts. Branch counts overlap because
one equation can support more than one physical branch.}}
\label{{fig:mechanism-retention}}
\end{{figure}}

\section{{The claim graph}}

The provenance graph contains {count(provenance_paper_count)} paper nodes,
{count(provenance_claim_count)} claim nodes and {count(provenance_edge_count)}
source-to-claim links. Its result is simple: the selected source set contains
many papers where black holes appear in astrophysical settings, fewer explicit
risk statements, and very few explicit safety statements.

\begin{{figure}}[H]
\centering
\includegraphics[width=0.98\linewidth]{{lhc_provenance_full.pdf}}
\caption{{Full claim graph. Paper nodes are on the left; extracted claim nodes
are on the right; each line is a source-to-claim link. This graph contains
{count(provenance_paper_count)} papers, {count(provenance_claim_count)} claims
and {count(provenance_edge_count)} links. The coordinates are graph-layout
coordinates only: horizontal position separates papers from claim nodes, while
vertical position groups claim families and adds jitter so overlapping nodes
can be seen.}}
\label{{fig:provenance-full}}
\end{{figure}}

\begin{{figure}}[H]
\centering
\includegraphics[width=0.90\linewidth]{{lhc_provenance_matrix.pdf}}
\caption{{Source-level provenance matrix. Rows are the highest-claim sources;
columns are extracted claim families. Cell values are individual source-to-claim
links. This view preserves provenance rather than collapsing the literature to
one aggregate edge.}}
\label{{fig:provenance-matrix}}
\end{{figure}}

The claim labels are:
\begin{{center}}
{counts_table(sorted_counts(claims))}
\end{{center}}

The claim graph gives the social surface of the literature: where black-hole,
risk and safety statements appear. The physical question starts after that.
The required route is a mathematical one, from LHC production to survival,
capture and growth.

\section{{The equation graph}}

The equation graph tests whether formulas assemble into the danger chain. It
retains {count(graph.get('evidence_grade_case_mechanism_node_count'))} branch
receipts. They sit mainly on astronomical analogues and stable growth/capture
constraints. The missing step is specific: no retained formula chain directly
connects an LHC-produced object to survival, stopping or capture in ordinary
matter, and net positive growth on a dangerous timescale.

\clearpage
\begin{{landscape}}
\begin{{figure}}[p]
\centering
\includegraphics[width=0.98\linewidth,height=0.78\textheight,keepaspectratio]{{lhc_mechanism_actual.pdf}}
\caption{{Retained equation graph. Each point is a formula receipt placed into
one physical branch. Panel A shows all case-relevant equation nodes, with the
evidence-grade receipts drawn larger and darker. Edges are source-local
transitions or cross-source route analogues. Panel B shows which mathematical
routes are attached to the plotted nodes. The graph shows that retained formulas
are dense in spectral, closure and transport roles, but the collider side has
only a production hook. The survival--capture--growth steps are transfer
constraints drawn from adjacent astrophysical mechanisms, not a direct collider
derivation in the selected corpus.}}
\label{{fig:mechanism-actual}}
\end{{figure}}
\end{{landscape}}
\clearpage

The retained branches are:
\begin{{center}}
{counts_table(sorted_counts(branch_counts))}
\end{{center}}

The retained equations support rate laws, constraints and scale relations for
compact objects. The missing physical bridge is the one from collider production
to survival, stopping, capture and fast growth inside ordinary matter.

\section{{Equation receipts}}

Representative receipts are shown in Table~\ref{{tab:receipts}}. Each receipt is
a local mathematical object that places a source inside one branch of the
physical tree. The identifiers R1--R7 refer to source-local formula windows;
the report-level variables used for the LHC mechanism are defined in
Eqs.~\eqref{{eq:danger-chain}}--\eqref{{eq:timescale-transfer}}.

\begin{{table}}[H]
\caption{{Representative equation receipts from the retained branch layer.}}
\label{{tab:receipts}}
{receipt_table(graph)}
\end{{table}}

\section{{What the equations imply}}

The selected equations support a transfer calculation. Astrophysical systems
provide constraints on growth, accretion, luminosity and compact-object
survival. Let \(\dot M_{{\rm astro}}\) denote an astrophysical mass-growth rate
and \(\dot M_{{\rm LHC}}\) the corresponding growth term proposed for a
microscopic object moving through matter. The LHC scenario can borrow
astrophysical equations only if the same physical role survives the change of
scale:
\begin{{equation}}
\dot M_{{\rm astro}}\quad\longrightarrow\quad
\dot M_{{\rm LHC}}=\rho\,\sigma_{{\rm cap}}(M,v)\,v .
\label{{eq:growth-transfer}}
\end{{equation}}
Let \(t_{{\rm grow}}^{{\rm astro}}\) be the astrophysical growth time inferred from
compact-object systems, and let \(t_{{\rm WD,NS}}\) denote the observed survival
time of white dwarfs or neutron stars used as astronomical bounds. A collider
translation must replace that astrophysical time-scale by the microscopic
capture and evaporation variables already defined above:
\begin{{equation}}
t_{{\rm grow}}^{{\rm astro}}>t_{{\rm WD,NS}}
\quad\longrightarrow\quad
\left\lbrace \tau_{{\rm capture}},\tau_{{\rm evap}},\rho,\sigma_{{\rm cap}}(M,v),v \right\rbrace
\quad\hbox{{for a microscopic object in matter.}}
\label{{eq:timescale-transfer}}
\end{{equation}}
Equations~\eqref{{eq:growth-transfer}} and \eqref{{eq:timescale-transfer}} are
valid only where the same growth or capture mechanism is preserved. Evaporation,
failed capture, or slow growth each breaks the dangerous branch.

Plain-language result:
\begin{{itemize}}
\item Production alone gives the starting condition. A threshold condition says
where the scenario could begin.
\item Evaporation closes the danger branch if the object loses mass before it can
be captured.
\item Stable survival gives only a lifetime condition. A stable object must also
be stopped, captured and made to grow.
\item Growth requires a medium, a cross-section and time. In equations this is
the role of $\rho$, $\sigma_{{\rm cap}}(M,v)$, $v$ and the growth timescale.
\item Astronomical bounds matter because long-lived compact objects test whether
similar growth mechanisms would already have destroyed observed systems.
\item In this corpus the equations mostly support the astronomical-bound side of
the argument. The absent formula is not just a missing citation. It is the
specific constructor step
\[
  \hbox{{LHC production}}\;\to\;\hbox{{survival}}\;\to\;\hbox{{stopping/capture}}
  \;\to\; \dot M_{{\rm LHC}}>0
\]
with a growth timescale short enough to matter. The retained equations do not
provide that source-local collider chain; they provide transfer constraints
against it.
\end{{itemize}}

\clearpage
\begin{{landscape}}
\begin{{figure}}[p]
\centering
\includegraphics[width=0.98\linewidth,height=0.78\textheight,keepaspectratio]{{lhc_transfer_graph.pdf}}
\caption{{Equation transfer from astrophysics to the LHC case. The retained
equations constrain growth, luminosity, compact-object survival and accretion in
astrophysical settings. Each row shows the required transfer: an astrophysical
receipt must preserve its physical role, be rewritten in LHC variables and pass
the corresponding collider closure test. The retained corpus supplies transfer
receipts but no direct collider closure beyond the production hook.}}
\label{{fig:transfer}}
\end{{figure}}
\end{{landscape}}
\clearpage

\section{{Alignment with CERN-2003-001 and equation correctness}}

CERN-2003-001 studied potentially dangerous events in heavy-ion collisions and
treated negatively charged strangelets, gravitational black holes and magnetic
monopoles \cite{{CERN2003}}. Its gravitational section uses the same branch
structure used here. Production is only the first step. A dangerous case also
requires stability against thermal decay, accretion faster than decay, and a
mechanism that remains compatible with ordinary matter and astrophysical
constraints. The agreement is structural: both arguments test whether
production, survival, capture, growth and astronomical closure can be connected
into one physical branch.

For ordinary four-dimensional gravity, CERN writes the Schwarzschild radius as
\begin{{equation}}
R_S=2GM=\frac{{M}}{{M_P^2}},
\label{{eq:cern-rs}}
\end{{equation}}
where \(G\) is Newton's constant and \(M_P\) is the four-dimensional Planck
mass. Comparing \(R_S\) with the LHC localization scale gives a required mass
far beyond accelerator energies. CERN then compares the Hawking decay rate
\begin{{equation}}
\Gamma_D\simeq T_{{\rm BH}}^4R_S^2
\label{{eq:cern-decay}}
\end{{equation}}
with an upper bound on accretion through matter,
\begin{{equation}}
\Gamma_A\simeq \pi R_S^2\rho .
\label{{eq:cern-accretion}}
\end{{equation}}
Here \(T_{{\rm BH}}\) is the black-hole temperature and \(\rho\) is the density
of matter. Growth requires \(\Gamma_A>\Gamma_D\), which CERN rewrites as a mass
bound many orders of magnitude above the LHC. In models with \(d\) extra
dimensions and fundamental scale \(M_\ast\), CERN uses
\begin{{equation}}
T_{{\rm BH}}\simeq M_\ast\left(\frac{{M_\ast}}{{M}}\right)^{{1/(1+d)}}
\label{{eq:cern-extra-temperature}}
\end{{equation}}
and again obtains a stability mass far beyond accelerator production, even in
the extreme case \(M_\ast=1\,{{\rm TeV}}\). Stable extremal black holes become a
growth mechanism only if ordinary matter carries the conserved charge needed to
feed them.

The equation status is as follows. Equation~\eqref{{eq:danger-chain}} is the
constructor form of the danger branch, with the production condition written at
parton level through \(\hat s=x_1x_2s\). Equation~\eqref{{eq:cern-rs}} is the
standard Schwarzschild-radius relation in units \(c=\hbar=1\).
Equations~\eqref{{eq:cern-decay}} and \eqref{{eq:cern-accretion}} are the
same scaling comparison used in CERN-2003-001: Hawking loss must be beaten by
matter intake before growth can begin. Equation~\eqref{{eq:cern-extra-temperature}}
is the higher-dimensional temperature scaling used for the TeV-gravity case.
The rate-balance term in Eq.~\eqref{{eq:danger-chain}} is the CERN
decay-versus-accretion comparison written as a sign test for
\(\dot M_{{\rm net}}\).

The present analysis adds four elements to the CERN report. First, it separates
the literature into a discourse graph, which records who states which kind of
claim, and an equation graph, which records which formulas occupy the physical
slots of the branch. Second, it keeps direct collider receipts separate from
astrophysical transfer receipts, so an accretion equation from a compact-object
paper cannot be mistaken for a collider closure. Third, it shows the missing
links explicitly: after the production hook, the survival, capture and growth
slots are filled only by transfer equations. Fourth, it makes the CERN safety
logic inspectable on a corpus: any new paper can be tested by asking which slot
it fills and whether it closes the branch. The conclusion remains aligned with
CERN-2003-001: the selected arXiv evidence does not connect production to a
direct collider survival--capture--growth chain.

\begin{{table}}[H]
\caption{{Equation audit against CERN-2003-001.}}
\label{{tab:cern-alignment}}
{cern_alignment_table()}
\end{{table}}

\section{{Conclusion}}

The dangerous LHC black-hole claim fails as a mechanism in the retained equation
set. The claim graph shows where black-hole statements occur. The equation graph
shows where the physical branch breaks: retained formulas populate adjacent
astrophysical mechanisms and growth/capture constraints, plus one
production-threshold hook. The missing links are survival after production,
stopping or capture in matter, positive growth at microscopic mass and velocity,
and evasion of astronomical survival bounds.

The strongest equation support is for adjacent astrophysical mechanisms:
accretion, luminosity limits, compact-object masses and survival bounds. A
danger argument would have to preserve those equations after changing the mass,
velocity, density, capture and lifetime assumptions to the collider case. The
retained equations stop before that preservation step.

\begin{{thebibliography}}{{9}}
\bibitem{{CERN2003}} J.-P. Blaizot, J. Iliopoulos, J. Madsen, G. G. Ross, P. Sonderegger and H.-J. Specht, ``Study of potentially dangerous events during heavy-ion collisions at the LHC: Report of the LHC Safety Study Group,'' CERN-2003-001 (2003), \url{{https://cds.cern.ch/record/613175/files/CERN-2003-001.pdf}}.
\bibitem{{GiddingsMangano2008}} S. B. Giddings and M. L. Mangano, ``Astrophysical implications of hypothetical stable TeV-scale black holes,'' arXiv:0806.3381 (2008).
\bibitem{{Ellis2008}} J. Ellis, G. Giudice, M. L. Mangano, I. Tkachev and U. Wiedemann, ``Review of the Safety of LHC Collisions,'' arXiv:0806.3414 (2008).
\bibitem{{Plaga2008}} R. Plaga, ``On the potential catastrophic risk from metastable quantum-black holes produced at particle colliders,'' arXiv:0808.1415 (2008).
\bibitem{{Koch2008}} B. Koch, M. Bleicher and H. Stoecker, ``Exclusion of black hole disaster scenarios at the LHC,'' arXiv:0807.3349 (2008).
\bibitem{{GiddingsManganoComment2008}} S. B. Giddings and M. L. Mangano, ``Comments on claimed risk from metastable black holes,'' arXiv:0808.4087 (2008).
\bibitem{{Casadio2009}} R. Casadio, S. Fabi and B. Harms, ``Possibility of catastrophic black hole growth in the warped brane-world scenario at the LHC,'' arXiv:0901.2948 (2009).
\bibitem{{Hawking1975}} S. W. Hawking, ``Particle creation by black holes,'' Communications in Mathematical Physics 43, 199--220 (1975).
\end{{thebibliography}}

\end{{document}}
"""
    tex_path.write_text(tex, encoding="utf-8")
    return tex_path


def build(args: argparse.Namespace) -> Dict[str, Any]:
    run_dir = Path(args.run_dir)
    paper_dir = Path(args.paper_dir)
    fig_dir = paper_dir / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    manifest = read_json(run_dir / "manifest.json")
    provenance = read_json(run_dir / "provenance_graph.json")
    graph = read_json(run_dir / "equation_mechanism_graph.json")
    sparse = read_json(run_dir / "sparse_attention_audit.json")
    constructor = build_physical_constructor(run_dir)
    write_constructor(run_dir)
    write_discourse_mechanism_attention(run_dir)
    discourse_attention = build_discourse_mechanism_attention(run_dir)
    kg = build_public_knowledge_graph(run_dir)
    write_public_knowledge_graph(run_dir)

    plot_provenance_graph(provenance, fig_dir / "lhc_provenance_full.pdf")
    plot_provenance_summary(provenance, fig_dir / "lhc_provenance_summary.pdf")
    plot_provenance_matrix(provenance, fig_dir / "lhc_provenance_matrix.pdf")
    plot_public_knowledge_graph(kg, fig_dir / "lhc_public_knowledge_graph.pdf")
    plot_public_knowledge_graph_full(kg, fig_dir / "lhc_public_knowledge_graph_full.pdf")
    plot_formation_mechanism(fig_dir / "lhc_formation_mechanism.pdf")
    plot_mechanism_retention(graph, fig_dir / "lhc_mechanism_retention.pdf")
    plot_mechanism_actual_graph(graph, fig_dir / "lhc_mechanism_actual.pdf")
    plot_physical_tree(graph, fig_dir / "lhc_physical_tree.pdf")
    plot_transfer_graph(graph, fig_dir / "lhc_transfer_graph.pdf")
    plot_physical_constructor(constructor, fig_dir / "lhc_physical_constructor.pdf")
    plot_constructor_demonstration(constructor, fig_dir / "lhc_constructor_demonstration.pdf")
    plot_discourse_mechanism_proof(discourse_attention, fig_dir / "lhc_discourse_mechanism_proof.pdf")
    tex_path = write_tex(run_dir, paper_dir, manifest, provenance, graph, sparse, constructor, kg, discourse_attention)
    report = {
        "report_type": "lhc_black_hole_answer",
        "tex": str(tex_path),
        "pdf": str(tex_path.with_suffix(".pdf")),
        "figures": sorted(str(path) for path in fig_dir.glob("lhc_*.pdf")),
        "source_run": str(run_dir),
    }
    (paper_dir / "lhc_black_hole_answer_manifest.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build the LHC black-hole scientific answer report.")
    parser.add_argument("--run-dir", default=str(DEFAULT_RUN))
    parser.add_argument("--paper-dir", default=str(ROOT / "paper"))
    return parser


def main() -> None:
    print(json.dumps(build(build_parser().parse_args()), indent=2))


if __name__ == "__main__":
    main()
