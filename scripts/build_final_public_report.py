#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import textwrap
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RUN = ROOT / "runs" / "lhc_black_hole_audit_500k_strict"
ROUTE_ORDER = [
    "transport_flow",
    "constraint_closure",
    "spectral_operator",
    "boundary_weak_form",
    "commutator_incompatibility",
    "discrete_protocol",
]


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def ensure_matplotlib():
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        return plt
    except Exception:
        return None


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


def latex_count(value: Any) -> str:
    return f"{int(value or 0):,}"


def compact_label(label: str) -> str:
    return str(label).replace("_", " ")


def sorted_items(mapping: Dict[str, Any], limit: int | None = None) -> List[Tuple[str, int]]:
    items = sorted(((str(k), int(v)) for k, v in (mapping or {}).items()), key=lambda x: (-x[1], x[0]))
    return items if limit is None else items[:limit]


def sorted_numeric(mapping: Dict[str, Any], limit: int | None = None) -> List[Tuple[str, float]]:
    items = sorted(((str(k), float(v)) for k, v in (mapping or {}).items()), key=lambda x: (-x[1], x[0]))
    return items if limit is None else items[:limit]


def coattention_items(value: Any, limit: int = 4) -> List[Tuple[str, int]]:
    if isinstance(value, dict):
        return sorted_items(value, limit=limit)
    if not isinstance(value, list):
        return []
    items: List[Tuple[str, int]] = []
    for row in value:
        if not isinstance(row, dict):
            continue
        left = compact_label(row.get("left") or "")
        right = compact_label(row.get("right") or "")
        count = int(row.get("count") or 0)
        if left and right:
            items.append((f"{left} + {right}", count))
    items.sort(key=lambda x: (-x[1], x[0]))
    return items[:limit]


def claim_type_counts(provenance: Dict[str, Any]) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for node in provenance.get("nodes") or []:
        if str(node.get("id", "")).startswith("C"):
            key = node.get("claim_type") or "unknown"
            out[key] = out.get(key, 0) + 1
    return out


def receipt_nodes(graph: Dict[str, Any]) -> List[Dict[str, Any]]:
    ids = set(graph.get("evidence_grade_case_node_ids") or [])
    return [node for node in graph.get("nodes") or [] if node.get("id") in ids]


def node_score(node: Dict[str, Any]) -> Tuple[int, int, int]:
    evidence = node.get("case_evidence") or {}
    return (
        int(node.get("formula_detail_score") or 0),
        int(evidence.get("score") or 0),
        len(node.get("route_signature") or []),
    )


def pick_receipts(nodes: List[Dict[str, Any]], branch: str, limit: int) -> List[Dict[str, Any]]:
    selected: List[Dict[str, Any]] = []
    seen = set()
    for node in sorted(nodes, key=node_score, reverse=True):
        evidence = node.get("case_evidence") or {}
        if branch not in (evidence.get("branch_labels") or []):
            continue
        key = (node.get("source_id"), node.get("formula"))
        if key in seen:
            continue
        seen.add(key)
        selected.append(node)
        if len(selected) >= limit:
            break
    return selected


def truncate(text: Any, n: int = 145) -> str:
    value = " ".join(str(text or "").split())
    return value if len(value) <= n else value[: n - 1] + "..."


def formula_cell(text: Any, width: int = 34) -> str:
    value = truncate(text, 145)
    lines = textwrap.wrap(value, width=width, break_long_words=True, break_on_hyphens=False)
    if not lines:
        lines = [""]
    escaped = [latex_escape(line).replace(r"\textbackslash{}", r"\textbackslash{}\hspace{0pt}") for line in lines]
    body = r"\\ ".join(escaped)
    return rf"\begin{{minipage}}[t]{{\linewidth}}\raggedright\sloppy\scriptsize\ttfamily {body}\end{{minipage}}"


def arxiv_url(source: Any) -> str:
    value = str(source or "")
    if value.startswith(("astro-ph", "cond-mat", "hep-", "math-ph", "quant-ph", "gr-qc")) and "/" not in value:
        prefix = "".join(ch for ch in value if not ch.isdigit())
        suffix = value[len(prefix) :]
        return f"https://arxiv.org/abs/{prefix}/{suffix}"
    return f"https://arxiv.org/abs/{value}"


def counts_table(items: Iterable[Tuple[str, int]]) -> str:
    rows = [rf"{latex_escape(compact_label(k))} & {latex_count(v)}\\" for k, v in items]
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


def receipt_table(nodes: List[Dict[str, Any]], limit: int = 5) -> str:
    if not nodes:
        return r"\emph{No receipt passed this branch filter in the public run.}"
    rows = []
    for node in nodes[:limit]:
        evidence = node.get("case_evidence") or {}
        routes = ", ".join(compact_label(r) for r in (node.get("route_signature") or []))
        branches = ", ".join(compact_label(r) for r in (evidence.get("branch_labels") or []))
        formula = formula_cell(node.get("formula"))
        source = node.get("source_id")
        source_text = rf"\href{{{latex_escape(arxiv_url(source))}}}{{{latex_escape(source)}}}"
        rows.append(rf"{source_text} & {latex_escape(routes)} & {latex_escape(branches)} & {formula}\tabularnewline")
    return "\n".join(
        [
            r"\begin{tabularx}{\linewidth}{p{0.13\linewidth}p{0.22\linewidth}p{0.25\linewidth}X}",
            r"\toprule",
            r"Source & Routes & Branch & Formula witness\\",
            r"\midrule",
            *rows,
            r"\bottomrule",
            r"\end{tabularx}",
        ]
    )


def plot_barh(
    data: Dict[str, Any],
    path: Path,
    title: str,
    xlabel: str = "count",
    limit: int | None = None,
    color: str = "#426d85",
) -> None:
    plt = ensure_matplotlib()
    items = sorted_items(data, limit=limit)
    if plt is None:
        path.with_suffix(".txt").write_text(title + "\n" + "\n".join(f"{k}: {v}" for k, v in items), encoding="utf-8")
        return
    labels = [compact_label(k) for k, _ in items]
    values = [v for _, v in items]
    fig_h = max(2.8, 0.36 * len(labels) + 1.25)
    fig, ax = plt.subplots(figsize=(7.2, fig_h))
    ax.barh(range(len(labels)), values, color=color)
    ax.set_yticks(range(len(labels)), labels, fontsize=8)
    ax.invert_yaxis()
    ax.set_xlabel(xlabel)
    ax.set_title(title, pad=10)
    xmax = max(values) if values else 1
    for i, value in enumerate(values):
        ax.text(value + xmax * 0.012, i, str(value), va="center", fontsize=8)
    ax.set_xlim(0, xmax * 1.18)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def plot_layer_comparison(manifest: Dict[str, Any], graph: Dict[str, Any], provenance: Dict[str, Any], path: Path) -> None:
    plt = ensure_matplotlib()
    if plt is None:
        path.with_suffix(".txt").write_text("Layer comparison unavailable\n", encoding="utf-8")
        return
    fig, ax = plt.subplots(figsize=(8.0, 4.2))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis("off")
    boxes = [
        (1.65, 4.85, "Literature map", "papers, claims,\nattribution", "#e8edf7"),
        (1.65, 3.25, "selected sources", latex_count(manifest.get("source_count")), "#eef3fb"),
        (1.65, 1.65, "claim nodes", latex_count(manifest.get("claim_count")), "#eef3fb"),
        (5.0, 4.85, "Formula layer", "local equation\nwindows", "#f6efe3"),
        (5.0, 3.25, "equation witnesses", latex_count(graph.get("source_witness_count")), "#fbf4e7"),
        (5.0, 1.65, "usable mechanisms", latex_count(graph.get("usable_mechanism_node_count")), "#fbf4e7"),
        (8.35, 4.85, "Mechanism map", "branches and\ntransfers", "#e6f1eb"),
        (8.35, 3.25, "case mechanisms", latex_count(graph.get("case_relevant_mechanism_node_count")), "#edf7f1"),
        (8.35, 1.65, "direct LHC branch", latex_count(graph.get("direct_lhc_safety_mechanism_node_count")), "#edf7f1"),
    ]
    for x, y, title, value, color in boxes:
        rect = plt.Rectangle((x - 1.2, y - 0.45), 2.4, 0.9, facecolor=color, edgecolor="#333333", linewidth=1.0)
        ax.add_patch(rect)
        ax.text(x, y + 0.12, title, ha="center", va="center", fontsize=9.2, fontweight="bold")
        ax.text(x, y - 0.18, value, ha="center", va="center", fontsize=9)
    for x0, x1 in [(2.85, 3.8), (6.2, 7.15)]:
        ax.annotate("", xy=(x1, 3.25), xytext=(x0, 3.25), arrowprops={"arrowstyle": "->", "lw": 1.6, "color": "#333333"})
    ax.text(
        5.0,
        0.35,
        "The source map locates the discussion. The mechanism map locates the physical branches carried by equations.",
        ha="center",
        va="center",
        fontsize=9.5,
    )
    fig.tight_layout(pad=0.35)
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def plot_evidence_funnel(graph: Dict[str, Any], path: Path) -> None:
    plt = ensure_matplotlib()
    stages = [
        ("equation\nwitnesses", int(graph.get("source_witness_count") or 0), "#2f5d7c"),
        ("usable\nmechanisms", int(graph.get("usable_mechanism_node_count") or 0), "#3d777a"),
        ("case-relevant\nmechanisms", int(graph.get("case_relevant_mechanism_node_count") or 0), "#5f8c66"),
        ("evidence-grade\ncase receipts", int(graph.get("evidence_grade_case_mechanism_node_count") or 0), "#a08d4f"),
        ("astrophysical\nanalogues", int(graph.get("astrophysical_analogue_mechanism_node_count") or 0), "#bf8c45"),
        ("threshold\nhook", int(graph.get("production_threshold_mechanism_node_count") or 0), "#b55d3c"),
        ("direct collider\nclosure", int(graph.get("direct_lhc_safety_mechanism_node_count") or 0), "#7b2835"),
    ]
    if plt is None:
        path.with_suffix(".txt").write_text("Evidence funnel\n" + "\n".join(f"{a}: {b}" for a, b, _ in stages), encoding="utf-8")
        return
    fig, ax = plt.subplots(figsize=(8.0, 4.6))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 8)
    ax.axis("off")
    max_value = max(v for _, v, _ in stages) or 1
    y_top = 7.25
    h = 0.68
    center = 5.0
    for i, (label, value, color) in enumerate(stages):
        y = y_top - i * 0.92
        width = 1.2 + 7.4 * (value / max_value) ** 0.45 if value else 0.62
        left = center - width / 2
        right = center + width / 2
        poly = plt.Polygon(
            [(left, y), (right, y), (right - 0.20, y - h), (left + 0.20, y - h)],
            closed=True,
            facecolor=color,
            edgecolor="#333333",
            linewidth=0.9,
            alpha=0.92,
        )
        ax.add_patch(poly)
        text_color = "white" if i < 4 else "black"
        ax.text(center, y - h * 0.48, f"{label}: {value}", ha="center", va="center", fontsize=9, color=text_color, fontweight="bold")
        if i < len(stages) - 1:
            ax.annotate("", xy=(center, y - h - 0.18), xytext=(center, y - h - 0.02), arrowprops={"arrowstyle": "->", "lw": 0.9, "color": "#444444"})
    ax.text(5.0, 0.35, "Each narrowing step is an evidence filter: formula quality, case relevance and branch specificity.", ha="center", fontsize=9.2)
    fig.tight_layout(pad=0.25)
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def plot_mechanism_translation(graph: Dict[str, Any], path: Path) -> None:
    plt = ensure_matplotlib()
    if plt is None:
        path.with_suffix(".txt").write_text("Mechanism translation unavailable\n", encoding="utf-8")
        return
    fig, ax = plt.subplots(figsize=(8.0, 4.1))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis("off")
    boxes = [
        (1.4, 4.6, "cosmic-ray or\ncompact-object setting", None, "#e8edf7"),
        (1.4, 2.9, "astrophysical\nanalogues", graph.get("astrophysical_analogue_mechanism_node_count", 0), "#e8edf7"),
        (5.0, 4.6, "shared mechanism slots", "production, capture,\ngrowth, evaporation", "#f5edcf"),
        (5.0, 2.9, "evidence-grade\ncase mechanisms", graph.get("evidence_grade_case_mechanism_node_count", 0), "#f5edcf"),
        (8.6, 4.6, "collider threshold", graph.get("production_threshold_mechanism_node_count", 0), "#eadbd2"),
        (8.6, 2.9, "direct LHC-safety\nmechanisms", graph.get("direct_lhc_safety_mechanism_node_count", 0), "#eadbd2"),
    ]
    for x, y, label, value, color in boxes:
        rect = plt.Rectangle((x - 1.22, y - 0.5), 2.44, 1.0, facecolor=color, edgecolor="#333333", linewidth=1.0)
        ax.add_patch(rect)
        text = label if value is None else f"{label}\n{value}"
        ax.text(x, y, text, ha="center", va="center", fontsize=9)
    for start, end in [((2.65, 4.6), (3.75, 4.6)), ((2.65, 2.9), (3.75, 2.9)), ((6.25, 4.6), (7.35, 4.6)), ((6.25, 2.9), (7.35, 2.9))]:
        ax.annotate("", xy=end, xytext=start, arrowprops={"arrowstyle": "->", "lw": 1.4, "color": "#333333"})
    ax.text(5.0, 1.0, "The scientific problem is transfer of a physical branch across source contexts.", ha="center", fontsize=9.5)
    fig.tight_layout(pad=0.35)
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def plot_branch_dag(graph: Dict[str, Any], sparse: Dict[str, Any], path: Path) -> None:
    plt = ensure_matplotlib()
    if plt is None:
        path.with_suffix(".txt").write_text("Branch map unavailable\n", encoding="utf-8")
        return
    branch_counts = sparse.get("case_branch_counts") or graph.get("case_branch_counts") or {}
    fig, ax = plt.subplots(figsize=(8.2, 4.9))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis("off")

    nodes = {
        "production": (1.2, 3.1, "production\nthreshold", graph.get("production_threshold_mechanism_node_count", 0), "#f2ead7"),
        "evaporation": (3.6, 4.55, "evaporation\npath", branch_counts.get("evaporation_branch", 0), "#e6f0f6"),
        "stable": (3.6, 1.85, "stable-remnant\npath", branch_counts.get("stable_growth_or_capture_branch", 0), "#f7e7df"),
        "capture": (6.15, 1.85, "capture and\ngrowth", graph.get("case_category_counts", {}).get("accretion_growth", 0), "#f7e7df"),
        "astro": (8.75, 1.85, "astronomical\nbound", graph.get("astrophysical_analogue_mechanism_node_count", 0), "#e9f2e5"),
        "safe": (6.15, 4.55, "rapid loss or\nfailed capture", branch_counts.get("evaporation_branch", 0), "#e6f0f6"),
        "direct": (8.75, 4.55, "direct collider\nclosure", graph.get("direct_lhc_safety_mechanism_node_count", 0), "#ececec"),
    }

    for key, (x, y, label, value, color) in nodes.items():
        rect = plt.Rectangle((x - 1.05, y - 0.48), 2.1, 0.96, facecolor=color, edgecolor="#333333", linewidth=1.0)
        ax.add_patch(rect)
        ax.text(x, y + 0.12, label, ha="center", va="center", fontsize=9, fontweight="bold")
        ax.text(x, y - 0.22, f"receipts: {int(value or 0)}", ha="center", va="center", fontsize=8.5)

    def arrow(a: str, b: str, rad: float = 0.0) -> None:
        x0, y0 = nodes[a][0], nodes[a][1]
        x1, y1 = nodes[b][0], nodes[b][1]
        ax.annotate(
            "",
            xy=(x1 - 1.08 if x1 > x0 else x1 + 1.08, y1),
            xytext=(x0 + 1.08 if x1 > x0 else x0 - 1.08, y0),
            arrowprops={
                "arrowstyle": "->",
                "lw": 1.5,
                "color": "#333333",
                "connectionstyle": f"arc3,rad={rad}",
            },
        )

    arrow("production", "evaporation", 0.18)
    arrow("production", "stable", -0.12)
    arrow("evaporation", "safe", 0.0)
    arrow("stable", "capture", 0.0)
    arrow("capture", "astro", 0.0)
    arrow("safe", "direct", 0.0)

    ax.text(
        5.0,
        0.65,
        "The public run concentrates evidence in the adjacent astrophysical branch.",
        ha="center",
        fontsize=9.3,
    )
    fig.tight_layout(pad=0.25)
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def plot_equation_branch_logic(graph: Dict[str, Any], path: Path) -> None:
    plt = ensure_matplotlib()
    if plt is None:
        path.with_suffix(".txt").write_text("Equation branch logic unavailable\n", encoding="utf-8")
        return
    fig, ax = plt.subplots(figsize=(8.2, 4.6))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis("off")
    boxes = [
        (1.55, 3.15, "production test", r"$\sqrt{s}>M_D$", graph.get("production_threshold_mechanism_node_count", 0), "#f2ead7"),
        (4.35, 4.65, "evaporation test", r"$dM/dt<0$", graph.get("case_branch_counts", {}).get("evaporation_branch", 0), "#e6f0f6"),
        (4.35, 1.65, "growth test", r"$dM/dt=\rho\sigma v$", graph.get("case_category_counts", {}).get("accretion_growth", 0), "#f7e7df"),
        (7.55, 4.65, "short lifetime", r"$\tau_{\rm evap}\ll\tau_{\rm capture}$", graph.get("case_branch_counts", {}).get("evaporation_branch", 0), "#e6f0f6"),
        (7.55, 1.65, "survival bound", r"$t_{\rm grow}>t_{\rm WD,NS}$", graph.get("astrophysical_analogue_mechanism_node_count", 0), "#e9f2e5"),
    ]
    for x, y, label, equation, count, color in boxes:
        rect = plt.Rectangle((x - 1.25, y - 0.58), 2.5, 1.16, facecolor=color, edgecolor="#333333", linewidth=1.0)
        ax.add_patch(rect)
        ax.text(x, y + 0.28, label, ha="center", va="center", fontsize=9, fontweight="bold")
        ax.text(x, y - 0.02, equation, ha="center", va="center", fontsize=11)
        ax.text(x, y - 0.35, f"receipts: {int(count or 0)}", ha="center", va="center", fontsize=8.3)
    for start, end in [((2.85, 3.15), (3.05, 4.65)), ((2.85, 3.15), (3.05, 1.65)), ((5.65, 4.65), (6.25, 4.65)), ((5.65, 1.65), (6.25, 1.65))]:
        ax.annotate("", xy=end, xytext=start, arrowprops={"arrowstyle": "->", "lw": 1.4, "color": "#333333"})
    ax.text(5.0, 0.45, "The formula role decides which physical branch is being tested.", ha="center", fontsize=9.3)
    fig.tight_layout(pad=0.25)
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def plot_branch_route_graph(sparse: Dict[str, Any], graph: Dict[str, Any], path: Path) -> None:
    plt = ensure_matplotlib()
    if plt is None:
        path.with_suffix(".txt").write_text("Branch-route graph unavailable\n", encoding="utf-8")
        return
    branch_attention = sparse.get("branch_route_attention") or {}
    branch_counts = sparse.get("case_branch_counts") or graph.get("case_branch_counts") or {}
    route_counts = sparse.get("evidence_route_counts") or graph.get("route_counts") or {}
    if not branch_attention:
        path.with_suffix(".txt").write_text("No branch route attention loaded\n", encoding="utf-8")
        return

    branch_order = [
        "production_threshold_branch",
        "evaporation_branch",
        "stable_growth_or_capture_branch",
        "astrophysical_black_hole_analogue",
    ]
    route_order = ["boundary_weak_form", "spectral_operator", "constraint_closure", "transport_flow", "discrete_protocol"]
    branches = [b for b in branch_order if b in branch_attention]
    routes = [r for r in route_order if any(float(branch_attention.get(b, {}).get(r, 0.0)) > 0 for b in branches)]
    fig, ax = plt.subplots(figsize=(8.2, 4.7))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis("off")

    branch_pos = {b: (1.7, 5.05 - i * 1.15) for i, b in enumerate(branches)}
    route_pos = {r: (8.1, 5.05 - i * (3.85 / max(1, len(routes) - 1))) for i, r in enumerate(routes)}
    branch_labels = {
        "production_threshold_branch": "production\nthreshold",
        "evaporation_branch": "evaporation",
        "stable_growth_or_capture_branch": "stable growth\nor capture",
        "astrophysical_black_hole_analogue": "astrophysical\nanalogue",
    }
    route_labels = {
        "boundary_weak_form": "boundary\nweak form",
        "spectral_operator": "spectral\noperator",
        "constraint_closure": "constraint\nclosure",
        "transport_flow": "transport\nflow",
        "discrete_protocol": "discrete\nprotocol",
    }

    for branch, (x, y) in branch_pos.items():
        label = branch_labels.get(branch, compact_label(branch).replace(" branch", ""))
        count = int(branch_counts.get(branch, 0))
        rect = plt.Rectangle((x - 1.20, y - 0.40), 2.4, 0.8, facecolor="#f5eadf", edgecolor="#333333")
        ax.add_patch(rect)
        ax.text(x, y + 0.12, label, ha="center", va="center", fontsize=8.2, fontweight="bold")
        ax.text(x, y - 0.22, f"n={count}", ha="center", va="center", fontsize=7.8)

    for route, (x, y) in route_pos.items():
        label = route_labels.get(route, compact_label(route))
        count = int(route_counts.get(route, 0))
        rect = plt.Rectangle((x - 1.10, y - 0.40), 2.2, 0.8, facecolor="#e7f0e8", edgecolor="#333333")
        ax.add_patch(rect)
        ax.text(x, y + 0.12, label, ha="center", va="center", fontsize=8.2, fontweight="bold")
        ax.text(x, y - 0.22, f"n={count}", ha="center", va="center", fontsize=7.8)

    for branch in branches:
        for route in routes:
            value = float(branch_attention.get(branch, {}).get(route, 0.0))
            if value <= 0:
                continue
            x0, y0 = branch_pos[branch]
            x1, y1 = route_pos[route]
            ax.plot([x0 + 1.38, x1 - 1.18], [y0, y1], color="#4c6f7a", alpha=0.22 + min(0.55, value), lw=0.8 + 5.5 * value)

    ax.text(5.0, 0.45, "Line thickness is branch-to-route attention in the evidence-grade case layer.", ha="center", fontsize=9)
    fig.tight_layout(pad=0.25)
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def plot_sparse_matrix(sparse: Dict[str, Any], path: Path) -> None:
    plt = ensure_matplotlib()
    branch_attention = sparse.get("branch_route_attention") or {}
    branches = list(branch_attention)
    if plt is None or not branches:
        path.with_suffix(".txt").write_text("Sparse attention unavailable\n", encoding="utf-8")
        return
    matrix = [[float(branch_attention.get(branch, {}).get(route, 0.0)) for route in ROUTE_ORDER] for branch in branches]
    vmax = max(0.01, max(max(row) for row in matrix))
    fig, ax = plt.subplots(figsize=(7.4, 3.8))
    image = ax.imshow(matrix, cmap="YlGnBu", vmin=0, vmax=vmax)
    ax.set_xticks(range(len(ROUTE_ORDER)), [r.replace("_", "\n") for r in ROUTE_ORDER], fontsize=8)
    ax.set_yticks(range(len(branches)), [b.replace("_", " ") for b in branches], fontsize=8)
    ax.set_title("Branch-to-route sparse attention", pad=10)
    for i, row in enumerate(matrix):
        for j, value in enumerate(row):
            if value:
                ax.text(j, i, f"{value:.2f}", ha="center", va="center", fontsize=7)
    fig.colorbar(image, ax=ax, fraction=0.035, pad=0.03)
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def write_figures(manifest: Dict[str, Any], graph: Dict[str, Any], provenance: Dict[str, Any], sparse: Dict[str, Any], fig_dir: Path) -> None:
    fig_dir.mkdir(parents=True, exist_ok=True)
    plot_layer_comparison(manifest, graph, provenance, fig_dir / "final_layer_comparison.pdf")
    plot_branch_dag(graph, sparse, fig_dir / "final_branch_dag.pdf")
    plot_equation_branch_logic(graph, fig_dir / "final_equation_branch_logic.pdf")
    plot_evidence_funnel(graph, fig_dir / "final_evidence_funnel.pdf")
    plot_mechanism_translation(graph, fig_dir / "final_mechanism_translation.pdf")
    plot_branch_route_graph(sparse, graph, fig_dir / "final_branch_route_graph.pdf")
    plot_barh(claim_type_counts(provenance), fig_dir / "final_claim_types.pdf", "Literature-map claim labels", color="#7c6f96")
    plot_barh(graph.get("route_counts") or {}, fig_dir / "final_route_counts.pdf", "Mechanism-route counts", color="#496f5d")
    plot_barh(graph.get("case_branch_counts") or {}, fig_dir / "final_case_branches.pdf", "Evidence-grade case branches", color="#a06145")
    plot_barh(graph.get("constructor_role_counts") or {}, fig_dir / "final_constructor_roles.pdf", "Constructor roles", color="#576a93")
    plot_sparse_matrix(sparse, fig_dir / "final_sparse_attention.pdf")


def sparse_paragraph(sparse: Dict[str, Any]) -> str:
    evidence_routes = sorted_items(sparse.get("evidence_route_counts") or {}, limit=4)
    coattention = coattention_items(sparse.get("route_route_coattention"), limit=3)
    branch_attention = sparse.get("branch_route_attention") or {}
    parts: List[str] = []
    if evidence_routes:
        parts.append(
            "In the evidence-grade case layer, the largest route counts are "
            + ", ".join(f"{compact_label(k)} ({v})" for k, v in evidence_routes)
            + "."
        )
    if "astrophysical_black_hole_analogue" in branch_attention:
        mix = sorted_numeric(branch_attention["astrophysical_black_hole_analogue"], limit=3)
        parts.append(
            "Astrophysical analogues distribute across "
            + ", ".join(f"{compact_label(k)} ({v:.2f})" for k, v in mix)
            + ", which is the expected pattern for mass, capture and growth mechanisms."
        )
    if coattention:
        parts.append("The strongest co-activations are " + ", ".join(f"{k} ({v})" for k, v in coattention) + ".")
    return " ".join(parts) if parts else "The sparse-attention artifact was not present in the run directory."


def write_tex(
    run_dir: Path,
    paper_dir: Path,
    manifest: Dict[str, Any],
    graph: Dict[str, Any],
    provenance: Dict[str, Any],
    sparse: Dict[str, Any],
) -> Path:
    tex_path = paper_dir / "lhc_mechanism_audit_final.tex"
    paper_dir.mkdir(parents=True, exist_ok=True)

    claims = claim_type_counts(provenance)
    route_counts = sorted_items(graph.get("route_counts") or {})
    branch_counts = sorted_items(graph.get("case_branch_counts") or {})
    role_counts = sorted_items(graph.get("constructor_role_counts") or {})
    formula_quality = sorted_items(graph.get("formula_quality_counts") or {}, limit=6)
    receipts = receipt_nodes(graph)
    receipt_sample: List[Dict[str, Any]] = []
    seen_receipts = set()
    for branch, limit in [
        ("production_threshold_branch", 1),
        ("astrophysical_black_hole_analogue", 3),
        ("stable_growth_or_capture_branch", 3),
        ("evaporation_branch", 2),
    ]:
        for node in pick_receipts(receipts, branch, limit):
            key = (node.get("source_id"), node.get("formula"))
            if key in seen_receipts:
                continue
            seen_receipts.add(key)
            receipt_sample.append(node)

    claim_register = [
        (
            "Literature map",
            f"{len(provenance.get('nodes') or [])} nodes and {len(provenance.get('edges') or [])} source-to-claim edges.",
            "This layer identifies documents, claim labels and attribution. Branch closure is tested in the equation mechanism map.",
        ),
        (
            "Equation mechanism map",
            f"{graph.get('source_witness_count', 0)} equation witnesses reduced to {graph.get('usable_mechanism_node_count', 0)} usable mechanism nodes.",
            "The evidence filter removes prose fragments and word-only matches, leaving equation windows that can be inspected.",
        ),
        (
            "Case split",
            f"{graph.get('direct_lhc_safety_mechanism_node_count', 0)} direct LHC-safety mechanisms, {graph.get('production_threshold_mechanism_node_count', 0)} threshold hook and {graph.get('astrophysical_analogue_mechanism_node_count', 0)} astrophysical analogues.",
            "The selected corpus populates adjacent black-hole mechanisms more strongly than direct collider-safety derivations.",
        ),
        (
            "Route content",
            ", ".join(f"{compact_label(k)}={v}" for k, v in route_counts[:3]),
            "The dominant equation roles are closure, operator structure and transport, which are the routes needed for growth or evaporation branches.",
        ),
        (
            "Sparse check",
            sparse_paragraph(sparse),
            "This calculation uses the public graph artifacts and supports the branch interpretation.",
        ),
    ]
    claim_rows = "\n".join(
        rf"{latex_escape(name)} & {latex_escape(evidence)} & {latex_escape(meaning)}\\"
        for name, evidence, meaning in claim_register
    )

    tex = rf"""\documentclass[11pt]{{article}}
\usepackage[a4paper,margin=0.9in]{{geometry}}
\usepackage{{graphicx}}
\usepackage{{amsmath,amssymb}}
\usepackage{{booktabs}}
\usepackage{{tabularx}}
\usepackage{{array}}
\usepackage{{hyperref}}
\usepackage{{caption}}
\usepackage{{xcolor}}
\usepackage{{enumitem}}
\usepackage{{float}}
\graphicspath{{{{figures/}}}}
\setlist[itemize]{{leftmargin=1.2em}}

\title{{Equation Branches in the LHC Black-Hole Safety Literature}}
\author{{Public mechanism map from source-derived artifacts}}
\date{{}}

\begin{{document}}
\maketitle

\begin{{abstract}}
The LHC microscopic-black-hole safety case is a branch problem in physics. A
dangerous branch would require production, survival, capture, growth and failure
of the astronomical bound. A safe branch can close through evaporation, failed
capture, slow accretion or compact-object survival constraints. We build a public
mechanism map of this literature from source-derived artifacts. The selected run contains {latex_count(manifest.get('source_count'))}
arXiv sources, {latex_count(manifest.get('claim_count'))} extracted claim labels and
{latex_count(graph.get('source_witness_count'))} equation witnesses. Formula filters reduce
these witnesses to {latex_count(graph.get('usable_mechanism_node_count'))} usable mechanism
nodes and {latex_count(graph.get('evidence_grade_case_mechanism_node_count'))} evidence-grade
case nodes. The result is a branch map:
{latex_count(graph.get('direct_lhc_safety_mechanism_node_count'))} direct formula-clean
LHC-safety mechanisms, {latex_count(graph.get('production_threshold_mechanism_node_count'))}
collider-threshold hook and {latex_count(graph.get('astrophysical_analogue_mechanism_node_count'))}
astrophysical black-hole analogues. The main result is a mechanism-transfer
problem: production, evaporation, capture, accretion and compact-object survival
must be connected by explicit equations before an adjacent astrophysical argument
can support a collider safety conclusion.
\end{{abstract}}

\section{{The safety case is a branch structure}}

The LHC black-hole debate turned on a branch structure in physics: whether
microscopic black holes could be
produced, whether they evaporate, whether a stable remnant could be captured, how
fast it could accrete matter, and whether astronomical observations already exclude
the dangerous branch. Those questions appear in the published safety literature and
its critics \cite{{GiddingsMangano2008,Ellis2008,Plaga2008,Koch2008,GiddingsManganoComment2008,Casadio2009}}.

For a non-specialist, the essential point is simple. A dangerous scenario needs
every step of one chain to work: the collider must make the object, the object
must survive, it must be trapped, it must grow fast enough, and astronomical
objects must fail to rule out the same growth mechanism. A safety argument can
close the chain at several places: no production, rapid evaporation, failed
capture, slow growth, or contradiction with observed compact-object survival.
	The evidence consists of equation-supported branch tests distributed across
	the source set.

\begin{{figure}}[H]
\centering
\includegraphics[width=0.96\linewidth]{{final_branch_dag.pdf}}
\caption{{Physical branch structure of the LHC black-hole safety case. Counts are
evidence-grade receipts retained by the public run. The populated route is mainly
the adjacent astrophysical branch; the direct collider branch remains empty under
the strict formula filter.}}
\label{{fig:branchdag}}
\end{{figure}}

The public repository first builds a literature map of papers, claim labels and
source-to-claim edges. It then builds an equation mechanism map from local formula
windows, formula-quality filters, route labels and cross-source analogues. The
literature map locates the discussion. The equation map asks which physical
branches are populated by inspectable formula receipts.

\begin{{figure}}[H]
\centering
\includegraphics[width=0.96\linewidth]{{final_layer_comparison.pdf}}
\caption{{Source and equation maps extracted from the same literature. The literature map
records attribution and claim labels. The equation mechanism map records whether
local formulas populate the physical branches of the argument.}}
\label{{fig:layers}}
\end{{figure}}

\section{{From formulas to mechanism receipts}}

An equation witness is a local formula window extracted from a source. It becomes
a usable mechanism node only when it survives formula-quality filters and activates
at least one route. The six route labels are broad physical operations:
\[
\begin{{array}}{{ll}}
\text{{transport or flow}} & \partial_t q+\nabla\cdot J=S,\\
\text{{constraint or closure}} & C(q,J,\lambda)=0,\\
\text{{spectral or operator}} & Lq=\lambda q,\\
\text{{boundary or weak form}} & \int_\Omega \phi Lq=\int_\Omega \phi f,\quad Bq=b,\\
\text{{commutator or residual}} & [A,B]=AB-BA,\\
\text{{ordered protocol}} & x_{{n+1}}=\Phi(x_n,u_n).
\end{{array}}
\]
The labels act as formula filters. They identify the role played by an equation
inside a possible derivation while leaving the physics in the source-local receipt.

This is the practical definition of evidence used in the report. A paragraph that
says a black hole is safe or dangerous is a claim. A formula such as a mass-loss
rate, an accretion rate, a threshold condition or a compact-object survival bound
is a mechanism receipt. The receipt can be inspected because it states what has to
change, what quantity is conserved or constrained, and what observation would
matter.

For the LHC case, the relevant branch can be written schematically as
\[
\mathrm{{production}}\rightarrow \mathrm{{evaporation\ or\ stability}}
\rightarrow \mathrm{{capture}}\rightarrow \mathrm{{growth}}
\rightarrow \mathrm{{astrophysical\ constraint}} .
\]
This is the mechanism structure behind the safety argument. The source map records
where the discussion occurs. The equation mechanism map asks which parts of the
branch are represented by formulas in the selected corpus.

\section{{What the run found}}

\begin{{figure}}[H]
\centering
\includegraphics[width=0.86\linewidth]{{final_evidence_funnel.pdf}}
\caption{{Evidence funnel under the public formula filter. Most equation windows are
kept as trace material or rejected. The retained layer is smaller and physically
more informative than a word-level source map.}}
\label{{fig:funnel}}
\end{{figure}}

The selected run starts with {latex_count(graph.get('source_witness_count'))}
equation witnesses. The formula filter retains {latex_count(graph.get('usable_mechanism_node_count'))}
usable mechanism nodes and {latex_count(graph.get('evidence_grade_case_mechanism_node_count'))}
evidence-grade case nodes. The direct LHC-safety branch has no formula-clean node
in this run. The adjacent branch is populated: the graph finds
{latex_count(graph.get('astrophysical_analogue_mechanism_node_count'))} astrophysical
black-hole analogues and {latex_count(graph.get('production_threshold_mechanism_node_count'))}
collider-threshold hook.

The result is a map of what the selected corpus can prove locally. It proves that
the run contains many formula-clean black-hole mechanisms relevant to growth,
capture and compact-object bounds. It also shows where the selected corpus is
	thin: direct collider-safety formulas are absent from the populated branch. The
safety argument therefore depends on mechanism translation: adjacent
astrophysical mechanisms must be carried into the collider setting with their
assumptions visible.

Published safety analyses use cosmic-ray and astronomical constraints in addition
to direct collider reasoning \cite{{GiddingsMangano2008,Ellis2008,Koch2008}}.
	In this public run, the source-local formula-clean receipts sit mainly in adjacent
	black-hole physics. The graph therefore makes the collider translation problem
	explicit.

\begin{{figure}}[H]
\centering
\includegraphics[width=0.92\linewidth]{{final_mechanism_translation.pdf}}
\caption{{Mechanism translation exposed by the graph. The populated side of the
run is adjacent astrophysical black-hole physics. The collider side contributes a
	threshold hook; direct source-local safety mechanisms are absent from the
	formula-clean retained layer.}}
\label{{fig:translation}}
\end{{figure}}

\section{{The physical branches}}

The production branch asks whether the collider reaches the threshold or event
condition assumed by a microscopic-black-hole model. A minimal form is
\[
\sqrt{{s}}>M_D .
\]
The selected public run found one threshold or event-selection hook. That is a
	small branch, so the report treats it as a hook, not as a closed collider
derivation.

The evaporation branch is different. Hawking radiation supplies the standard
mass-loss route for microscopic black holes \cite{{Hawking1975}}. A receipt in
this branch should support a sign or timescale relation such as
\[
\frac{{dM}}{{dt}}<0,\qquad \tau_{{\rm evap}}\ll \tau_{{\rm capture}} .
\]
The stable branch reverses the problem. If a black hole does not evaporate before
capture, the relevant equations become stopping, capture and accretion:
\[
\frac{{dM}}{{dt}}=\rho\,\sigma(M)\,v .
\]
Astronomical survival then becomes a constraint. If the same mechanism would
destroy white dwarfs or neutron stars on short timescales, observed survival of
those systems constrains the dangerous branch. This is why the safety argument is
best read as a transfer of a mechanism from collider production to compact-object
capture and growth.

	These equations are schematic, but they show what the graph is looking for. A
	threshold formula belongs to production. A negative mass-change or short lifetime
	belongs to evaporation. A positive growth law belongs to the stable-remnant
	branch. A compact-object lifetime bound belongs to the astronomical test. The
	graph is useful because it keeps these roles separate instead of mixing them into
	one textual controversy.

\begin{{figure}}[H]
\centering
\includegraphics[width=0.92\linewidth]{{final_equation_branch_logic.pdf}}
\caption{{Equation tests behind the physical branch map. The same source set is
sorted by formula role: production threshold, evaporation timescale, growth rate
and astronomical survival bound.}}
\label{{fig:eqbranch}}
\end{{figure}}

\section{{Route structure and sparse-attention result}}

The mechanism routes retained by the graph are concentrated in closure, operator
structure and transport:

\begin{{center}}
{counts_table(route_counts)}
\end{{center}}

\begin{{figure}}[H]
\centering
\includegraphics[width=0.80\linewidth]{{final_route_counts.pdf}}
\caption{{Mechanism-route counts among usable nodes. The retained layer is dominated
by closure, operator structure and transport, the routes needed for growth,
evaporation and capture arguments.}}
\label{{fig:routes}}
\end{{figure}}

The route co-activation calculation supports the same interpretation. {latex_escape(sparse_paragraph(sparse))}
	This route-level calculation marks shared equation operations across source
	contexts. Physical equivalence still depends on the assumptions carried by each
	source.

	In plain terms, the retained formulas show repeated structure. They combine
	three operations: an operator or rate law, a closure or constraint, and a
transport or growth term. That pattern is exactly what a black-hole safety branch
requires. A growth scenario needs a rate law and a constraint on available matter.
An evaporation scenario needs a rate law and a timescale. An astrophysical bound
needs a constraint that connects the same mechanism to observed survival.

\begin{{figure}}[H]
\centering
\includegraphics[width=0.92\linewidth]{{final_branch_route_graph.pdf}}
\caption{{Branch-to-route graph in the evidence-grade case layer. Branches are on
the left, equation routes are on the right, and line thickness gives route attention.
The dominant branch connections run through spectral/operator, closure and
transport operations.}}
\label{{fig:routegraph}}
\end{{figure}}

\begin{{figure}}[H]
\centering
\includegraphics[width=0.88\linewidth]{{final_sparse_attention.pdf}}
\caption{{Branch-to-route sparse attention. Adjacent astrophysical mechanisms
concentrate in operator, closure and transport routes; the production-threshold
branch is separate and small.}}
\label{{fig:sparse}}
\end{{figure}}

\section{{Source map result}}

The source map has {latex_count(len(provenance.get('nodes') or []))} nodes and
{latex_count(len(provenance.get('edges') or []))} source-to-claim edges. Its claim
labels are:

\begin{{center}}
{counts_table(sorted_items(claims))}
\end{{center}}

This layer is still useful. It records which sources belong to the safety, risk,
astrophysical-bound or collider-threshold discussion. It is also the right layer
for dates, author identity and citation provenance. Its limit is categorical:
source-to-claim edges leave the evaporation, capture and accretion branches
unresolved until the equation layer is inspected.

	The source map therefore plays a supporting role. It tells the reader where the
	discussion sits and which papers are involved. Closure of a mass-growth branch
	requires the local formulas and their physical roles.

\section{{Mechanism receipts}}

The report exposes local formula windows that can be checked against the source
papers. Table~\ref{{tab:receipts}}
shows a compact sample; the full receipt set remains in
\texttt{{equation\_mechanism\_graph.json}} and \texttt{{equation\_mechanism\_graph.md}}.
The table should be read as an evidence ledger. Each formula is a reason why a
branch was counted: a mass accretion rate, a bound on black-hole mass change, a
compact-object scale or a threshold-like condition.

\begin{{table}}[t]
\caption{{Representative mechanism receipts retained by the formula filter.}}
\label{{tab:receipts}}
{receipt_table(receipt_sample, 8)}
\end{{table}}

\section{{Evidence register}}

\begin{{tabularx}}{{\linewidth}}{{p{{0.17\linewidth}}p{{0.34\linewidth}}X}}
\toprule
Claim & Evidence & Interpretation\\
\midrule
{claim_rows}
\bottomrule
\end{{tabularx}}

\section{{Formula-quality boundary}}

The graph carries its own failure modes. Formula-quality labels in the public run
include:

\begin{{center}}
{counts_table(formula_quality)}
\end{{center}}

These counts explain why the evidence funnel is steep. Many local windows are
prose, bibliography, weak formula fragments or equations without a case-relevant
mechanism. The formula filter is deliberately conservative: noisy material remains
available in the source-derived artifacts, while formula-clean case windows are
promoted to mechanism receipts.

\section{{Conclusion}}

	The public run demonstrates a practical difference between two ways of reading
	scientific papers. A source map reconstructs attribution and claim labels. An
	equation mechanism map asks whether the equations needed by the argument are
	present and how they connect.
For the LHC black-hole case, that second graph exposes the main structure of the
	evidence: a sparse direct collider branch, a small threshold hook, and a populated
	set of adjacent astrophysical mechanisms. The scientific question becomes a
	controlled transfer problem between physical branches.

\begin{{thebibliography}}{{9}}
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
    manifest = read_json(run_dir / "manifest.json")
    graph = read_json(run_dir / "equation_mechanism_graph.json")
    provenance = read_json(run_dir / "provenance_graph.json")
    sparse = read_json(run_dir / "sparse_attention_audit.json")
    write_figures(manifest, graph, provenance, sparse, fig_dir)
    tex_path = write_tex(run_dir, paper_dir, manifest, graph, provenance, sparse)
    report = {
        "report_type": "lhc_final_public_report",
        "readiness": "usable",
        "tex": str(tex_path),
        "pdf": str(tex_path.with_suffix(".pdf")),
        "figures": sorted(str(p) for p in fig_dir.glob("final_*.pdf")),
        "source_run": str(run_dir),
    }
    (paper_dir / "final_report_manifest.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build the final public LHC mechanism report.")
    parser.add_argument("--run-dir", default=str(DEFAULT_RUN), help="Public run artifact directory.")
    parser.add_argument("--paper-dir", default="paper", help="Paper output directory.")
    return parser


def main() -> None:
    print(json.dumps(build(build_parser().parse_args()), indent=2))


if __name__ == "__main__":
    main()
