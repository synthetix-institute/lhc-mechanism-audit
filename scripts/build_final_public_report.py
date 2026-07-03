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
    return label.replace("_", " ")


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
    items = []
    for row in value:
        if not isinstance(row, dict):
            continue
        left = compact_label(str(row.get("left") or ""))
        right = compact_label(str(row.get("right") or ""))
        count = int(row.get("count") or 0)
        if left and right:
            items.append((f"{left} + {right}", count))
    items.sort(key=lambda x: (-x[1], x[0]))
    return items[:limit]


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
    fig_h = max(2.7, 0.36 * len(labels) + 1.1)
    fig, ax = plt.subplots(figsize=(7.1, fig_h))
    ax.barh(range(len(labels)), values, color=color)
    ax.set_yticks(range(len(labels)), labels, fontsize=8)
    ax.invert_yaxis()
    ax.set_xlabel(xlabel)
    ax.set_title(title)
    xmax = max(values) if values else 1
    for i, value in enumerate(values):
        ax.text(value + xmax * 0.012, i, str(value), va="center", fontsize=8)
    ax.set_xlim(0, xmax * 1.18)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def plot_evidence_funnel(graph: Dict[str, Any], path: Path) -> None:
    data = {
        "equation witnesses": graph.get("source_witness_count", 0),
        "usable formula-clean mechanisms": graph.get("usable_mechanism_node_count", 0),
        "case-relevant mechanisms": graph.get("case_relevant_mechanism_node_count", 0),
        "evidence-grade case mechanisms": graph.get("evidence_grade_case_mechanism_node_count", 0),
        "astrophysical analogues": graph.get("astrophysical_analogue_mechanism_node_count", 0),
        "collider threshold hooks": graph.get("production_threshold_mechanism_node_count", 0),
        "direct LHC-safety mechanisms": graph.get("direct_lhc_safety_mechanism_node_count", 0),
    }
    plot_barh(data, path, "Strict evidence funnel", color="#2f5d7c")


def plot_sparse_matrix(sparse: Dict[str, Any], path: Path) -> None:
    plt = ensure_matplotlib()
    branch_attention = sparse.get("branch_route_attention") or {}
    branches = list(branch_attention)
    if plt is None or not branches:
        path.with_suffix(".txt").write_text("Sparse attention unavailable\n", encoding="utf-8")
        return
    matrix = [[float(branch_attention.get(branch, {}).get(route, 0.0)) for route in ROUTE_ORDER] for branch in branches]
    vmax = max(0.01, max(max(row) for row in matrix))
    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    image = ax.imshow(matrix, cmap="YlGnBu", vmin=0, vmax=vmax)
    ax.set_xticks(range(len(ROUTE_ORDER)), [r.replace("_", "\n") for r in ROUTE_ORDER], fontsize=8)
    ax.set_yticks(range(len(branches)), [b.replace("_", " ") for b in branches], fontsize=8)
    ax.set_title("Branch-to-route sparse attention")
    for i, row in enumerate(matrix):
        for j, value in enumerate(row):
            if value:
                ax.text(j, i, f"{value:.2f}", ha="center", va="center", fontsize=7)
    fig.colorbar(image, ax=ax, fraction=0.035, pad=0.03)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


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
    selected = []
    seen = set()
    for node in sorted(nodes, key=node_score, reverse=True):
        evidence = node.get("case_evidence") or {}
        if branch not in (evidence.get("branch_labels") or []):
            continue
        source = node.get("source_id")
        key = (source, node.get("formula"))
        if key in seen:
            continue
        seen.add(key)
        selected.append(node)
        if len(selected) >= limit:
            break
    return selected


def truncate(text: Any, n: int = 165) -> str:
    value = " ".join(str(text or "").split())
    return value if len(value) <= n else value[: n - 1] + "..."


def formula_cell(text: Any, width: int = 28) -> str:
    value = truncate(text, 150)
    lines = textwrap.wrap(value, width=width, break_long_words=True, break_on_hyphens=False)
    if not lines:
        lines = [""]
    body = r"\\ ".join(latex_escape(line) for line in lines)
    return rf"\begin{{minipage}}[t]{{\linewidth}}\raggedright\scriptsize\ttfamily {body}\end{{minipage}}"


def receipt_table(nodes: List[Dict[str, Any]]) -> str:
    if not nodes:
        return r"\emph{No receipt passed the current gate.}"
    rows = []
    for node in nodes:
        evidence = node.get("case_evidence") or {}
        routes = ", ".join(compact_label(r) for r in (node.get("route_signature") or []))
        branches = ", ".join(compact_label(r) for r in (evidence.get("branch_labels") or []))
        formula = formula_cell(node.get("formula"))
        rows.append(
            rf"{latex_escape(node.get('source_id'))} / {latex_escape(node.get('id'))} & "
            rf"{latex_escape(routes)} & {latex_escape(branches)} & "
            rf"{formula}\tabularnewline"
        )
    return "\n".join(
        [
            r"\begin{tabularx}{\linewidth}{p{0.14\linewidth}p{0.23\linewidth}p{0.24\linewidth}X}",
            r"\toprule",
            r"Source & Routes & Branch labels & Formula witness\\",
            r"\midrule",
            *rows,
            r"\bottomrule",
            r"\end{tabularx}",
        ]
    )


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


def write_figures(graph: Dict[str, Any], provenance: Dict[str, Any], sparse: Dict[str, Any], fig_dir: Path) -> None:
    fig_dir.mkdir(parents=True, exist_ok=True)
    plot_evidence_funnel(graph, fig_dir / "final_evidence_funnel.pdf")
    plot_barh(claim_type_counts(provenance), fig_dir / "final_claim_types.pdf", "Provenance claim labels", color="#7c6f96")
    plot_barh(graph.get("route_counts") or {}, fig_dir / "final_route_counts.pdf", "Six-route mechanism counts", color="#496f5d")
    plot_barh(graph.get("case_branch_counts") or {}, fig_dir / "final_case_branches.pdf", "Evidence-grade case branches", color="#a06145")
    plot_barh(graph.get("constructor_role_counts") or {}, fig_dir / "final_constructor_roles.pdf", "Constructor roles in usable mechanisms", color="#576a93")
    plot_barh(graph.get("transition_label_counts") or {}, fig_dir / "final_transition_labels.pdf", "Frequent transition labels", limit=12, color="#6b7f3f")
    plot_sparse_matrix(sparse, fig_dir / "final_sparse_attention.pdf")


def write_tex(
    run_dir: Path,
    paper_dir: Path,
    manifest: Dict[str, Any],
    graph: Dict[str, Any],
    provenance: Dict[str, Any],
    operational: Dict[str, Any],
    sparse: Dict[str, Any],
) -> Path:
    tex_path = paper_dir / "lhc_mechanism_audit_final.tex"
    paper_dir.mkdir(parents=True, exist_ok=True)
    fig = "figures"
    claims = claim_type_counts(provenance)
    route_counts = sorted_items(graph.get("route_counts") or {})
    branch_counts = sorted_items(graph.get("case_branch_counts") or {})
    role_counts = sorted_items(graph.get("constructor_role_counts") or {})
    transition_counts = sorted_items(graph.get("transition_label_counts") or {}, limit=12)
    sparse_findings = sparse.get("findings") or []
    evidence_routes = sorted_items(sparse.get("evidence_route_counts") or {})
    branch_attention = sparse.get("branch_route_attention") or {}
    route_coattention = coattention_items(sparse.get("route_route_coattention"), limit=4)
    receipts = receipt_nodes(graph)
    threshold_receipts = pick_receipts(receipts, "production_threshold_branch", 5)
    astro_receipts = pick_receipts(receipts, "astrophysical_black_hole_analogue", 8)
    stable_receipts = pick_receipts(receipts, "stable_growth_or_capture_branch", 6)
    evaporation_receipts = pick_receipts(receipts, "evaporation_branch", 6)

    sparse_bullets = []
    if evidence_routes:
        sparse_bullets.append("Evidence-grade routes: " + ", ".join(f"{compact_label(k)}={v}" for k, v in evidence_routes[:4]) + ".")
    if "astrophysical_black_hole_analogue" in branch_attention:
        mix = sorted_numeric(branch_attention["astrophysical_black_hole_analogue"], limit=4)
        sparse_bullets.append("Astrophysical analogues concentrate on " + ", ".join(f"{compact_label(k)}={v:.2f}" for k, v in mix) + ".")
    if "production_threshold_branch" in branch_attention:
        mix = sorted_numeric(branch_attention["production_threshold_branch"], limit=3)
        sparse_bullets.append("The production-threshold branch is small and separate: " + ", ".join(f"{compact_label(k)}={v:.2f}" for k, v in mix) + ".")
    if route_coattention:
        sparse_bullets.append("The strongest route co-activations are " + ", ".join(f"{compact_label(k)}={v}" for k, v in route_coattention[:3]) + ".")
    sparse_items = "\n".join(rf"\item {latex_escape(item)}" for item in sparse_bullets)
    if not sparse_items:
        sparse_items = r"\item No sparse-attention artifact was present in the static run directory."

    claim_register = [
        (
            "The selected corpus supports a selected-corpus finding.",
            f"{manifest.get('source_count', 0)} selected sources from the high-recall scan.",
            "The scan is broad enough for this public audit object. A universal absence claim would require the full literature and non-arXiv safety reports.",
        ),
        (
            "The provenance layer is mostly attribution.",
            f"{len(provenance.get('nodes') or [])} provenance nodes and {len(provenance.get('edges') or [])} source-to-claim edges.",
            "It organizes who said what and where. Equation support has to be tested in a separate graph.",
        ),
        (
            "The mechanism layer is much stricter than the provenance layer.",
            f"{graph.get('source_witness_count', 0)} equation witnesses narrowed to {graph.get('usable_mechanism_node_count', 0)} usable mechanism nodes.",
            "Most extracted text is retained as audit material or rejected by formula-quality gates.",
        ),
        (
            "No direct LHC-safety equation branch passed the strict gate.",
            f"{graph.get('direct_lhc_safety_mechanism_node_count', 0)} direct LHC-safety mechanism nodes.",
            "The absence is defined by the selected corpus and the source-local equation gate.",
        ),
        (
            "The populated branch is adjacent black-hole physics.",
            f"{graph.get('astrophysical_analogue_mechanism_node_count', 0)} astrophysical analogues and {graph.get('production_threshold_mechanism_node_count', 0)} collider-threshold hook.",
            "The audit becomes mechanism translation from accretion, evaporation, capture and compact-object survival into the collider branch.",
        ),
        (
            "The dominant mechanism routes are operator/closure/transport.",
            ", ".join(f"{compact_label(k)}={v}" for k, v in route_counts[:3]),
            "The graph records equation roles and route co-activation.",
        ),
        (
            "Sparse attention supports the branch split.",
            ", ".join(f"{compact_label(k)}={v}" for k, v in evidence_routes[:3]) if evidence_routes else "No sparse-attention file loaded.",
            "The sparse audit is a consistency check over static graph artifacts.",
        ),
    ]
    claim_register_tex = "\n".join(
        rf"\item \textbf{{{latex_escape(claim)}}} Evidence: {latex_escape(evidence)} Interpretation: {latex_escape(interpretation)}"
        for claim, evidence, interpretation in claim_register
    )

    tex = rf"""\documentclass[11pt]{{article}}
\usepackage[a4paper,margin=0.85in]{{geometry}}
\usepackage{{graphicx}}
\usepackage{{amsmath,amssymb}}
\usepackage{{booktabs}}
\usepackage{{tabularx}}
\usepackage{{array}}
\usepackage{{hyperref}}
\usepackage{{caption}}
\usepackage{{xcolor}}
\usepackage{{enumitem}}
\setlist[itemize]{{leftmargin=1.2em}}
\setlist[enumerate]{{leftmargin=1.4em}}

\title{{Mechanism Graphs for the LHC Black-Hole Safety Case}}
\author{{Static audit report}}
\date{{}}

\begin{{document}}
\maketitle

\begin{{abstract}}
Scientific papers contain an attribution layer and an equation layer. The first records
sources and claims. The second records the mathematical steps that could make a claim
physically true. This report applies that separation to the LHC microscopic-black-hole
safety debate using a static public audit run. The selected corpus contains
{latex_count(manifest.get('source_count'))} arXiv sources, {latex_count(manifest.get('claim_count'))}
provenance claim nodes and {latex_count(graph.get('source_witness_count'))} equation witnesses.
Formula gates reduce the equation layer to {latex_count(graph.get('usable_mechanism_node_count'))}
usable mechanism nodes and {latex_count(graph.get('evidence_grade_case_mechanism_node_count'))}
evidence-grade case nodes. The branch split is sharp:
{latex_count(graph.get('direct_lhc_safety_mechanism_node_count'))} source-local formula-clean
direct LHC-safety mechanisms, {latex_count(graph.get('production_threshold_mechanism_node_count'))}
collider-threshold hook and {latex_count(graph.get('astrophysical_analogue_mechanism_node_count'))}
astrophysical black-hole analogues. The useful object is a translation map: accretion,
evaporation, capture, mass growth and compact-object survival mechanisms must be carried
explicitly into the collider branch before they can support a safety argument.
\end{{abstract}}

\section{{Main Claims and Evidence Register}}

\begin{{enumerate}}
{claim_register_tex}
\end{{enumerate}}

\section{{Data Object}}

The run directory is \texttt{{{latex_escape(run_dir)}}}. It contains derived public artifacts:
\texttt{{manifest.json}}, \texttt{{provenance\_graph.json}}, \texttt{{equation\_witnesses.json}},
\texttt{{operational\_graph.json}}, \texttt{{equation\_mechanism\_graph.json}} and
\texttt{{sparse\_attention\_audit.json}}. These files are enough to inspect the report. Private
fingerprints, model checkpoints and core pipeline files are outside this repository.

\begin{{figure}}[t]
\centering
\includegraphics[width=0.92\linewidth]{{{fig}/provenance_vs_mechanism.pdf}}
\caption{{Two graph layers in the same selected archive. Provenance organizes attribution and claims. The mechanism graph records which equation-level branches are present.}}
\end{{figure}}

\section{{Provenance Layer}}

The provenance layer contains {latex_count(len(provenance.get('nodes') or []))} nodes and
{latex_count(len(provenance.get('edges') or []))} source-to-claim edges. Claim labels in this selected
corpus are:

\begin{{center}}
{counts_table(sorted_items(claims))}
\end{{center}}

\begin{{figure}}[t]
\centering
\includegraphics[width=0.74\linewidth]{{{fig}/final_claim_types.pdf}}
\caption{{Claim labels in the provenance layer. This layer is an attribution record. Equation support is tested separately.}}
\end{{figure}}

\section{{Mechanism Layer and Gates}}

The mechanism layer begins with local equation witnesses and applies formula-quality, case-relevance
and route gates. The public audit uses six route labels:
\[
\begin{{array}}{{ll}}
\text{{transport/flow}} & \partial_t q + \nabla\cdot J = S,\\
\text{{constraint/closure}} & C(q,J,\lambda)=0,\\
\text{{spectral/operator}} & Lq=\lambda q,\\
\text{{boundary/weak form}} & \int_\Omega \phi Lq=\int_\Omega \phi f,\quad Bq=b,\\
\text{{commutator/residual}} & [A,B]=AB-BA,\\
\text{{discrete protocol}} & x_{{n+1}}=\Phi(x_n,u_n).
\end{{array}}
\]
These route labels are audit gates. They separate formula-clean mechanism receipts from word
matches and bibliographic residue.

\begin{{figure}}[t]
\centering
\includegraphics[width=0.82\linewidth]{{{fig}/final_evidence_funnel.pdf}}
\caption{{Strict evidence funnel from equation witnesses to case-specific mechanism receipts. The sharp drop is expected: the gate rejects prose fragments, local word matches without a relation operator, and formula windows without case-local mechanism content.}}
\end{{figure}}

\section{{Run Counts}}

\begin{{center}}
{counts_table([
    ('selected sources', manifest.get('source_count', 0)),
    ('provenance claims', manifest.get('claim_count', 0)),
    ('source equation witnesses', graph.get('source_witness_count', 0)),
    ('usable mechanism nodes', graph.get('usable_mechanism_node_count', 0)),
    ('case-relevant mechanism nodes', graph.get('case_relevant_mechanism_node_count', 0)),
    ('evidence-grade case nodes', graph.get('evidence_grade_case_mechanism_node_count', 0)),
    ('direct LHC-safety mechanism nodes', graph.get('direct_lhc_safety_mechanism_node_count', 0)),
    ('collider-threshold hooks', graph.get('production_threshold_mechanism_node_count', 0)),
    ('astrophysical analogues', graph.get('astrophysical_analogue_mechanism_node_count', 0)),
    ('source-local route-transition edges', len(graph.get('edges') or [])),
    ('rich cross-source route analogues', len(graph.get('analog_edges') or [])),
])}
\end{{center}}

\section{{Mechanism Distribution}}

The usable mechanism layer is dominated by closure, spectral/operator and transport routes:

\begin{{center}}
{counts_table(route_counts)}
\end{{center}}

\begin{{figure}}[t]
\centering
\includegraphics[width=0.82\linewidth]{{{fig}/final_route_counts.pdf}}
\caption{{Six-route counts among non-artifact constructor pairs. The reusable layer is a small set of equation operations.}}
\end{{figure}}

Constructor-role and transition-label diagnostics give the same picture:

\begin{{center}}
{counts_table(role_counts)}
\end{{center}}

\begin{{figure}}[t]
\centering
\includegraphics[width=0.82\linewidth]{{{fig}/final_constructor_roles.pdf}}
\caption{{Constructor roles present in usable mechanisms. Operator apparatus, selector and real substrate geometry appear as separable roles.}}
\end{{figure}}

\begin{{figure}}[t]
\centering
\includegraphics[width=0.86\linewidth]{{{fig}/final_transition_labels.pdf}}
\caption{{Frequent transition labels. Preservation, addition and projection of operator, selector and closure roles are common moves in the equation layer.}}
\end{{figure}}

\section{{LHC Case Branches}}

Evidence-grade branch counts are:

\begin{{center}}
{counts_table(branch_counts)}
\end{{center}}

\begin{{figure}}[t]
\centering
\includegraphics[width=0.82\linewidth]{{{fig}/final_case_branches.pdf}}
\caption{{Evidence-grade case branches. The populated branch is adjacent astrophysical black-hole physics; the direct LHC-safety branch remains empty under the strict gate.}}
\end{{figure}}

The collider branch first requires a production or event-selection condition, for example
\[
\sqrt{{s}} > M_D .
\]
If evaporation dominates, a local receipt should support a mass-loss or lifetime ordering such as
\[
\frac{{dM}}{{dt}} < 0,\qquad \tau_{{\rm evap}}\ll \tau_{{\rm capture}} .
\]
If a stable object is assumed, the mechanism changes to stopping, capture and growth:
\[
\frac{{dM}}{{dt}}=\rho\,\sigma(M)\,v .
\]
Compact-object survival then becomes an external constraint on the same mechanism:
\[
t_{{\rm grow}} < t_{{\rm WD}}
\]
would be inconsistent with observed white-dwarf survival if the same production, capture and
growth mechanism were realized in nature. The static graph found adjacent receipts for this
translation problem. It did not find a direct formula-clean collider-safety branch.

\section{{Sparse-Attention Check}}

The sparse-attention audit reads the static mechanism graph and measures route co-activation in
the evidence-grade case layer.

\begin{{itemize}}
{sparse_items}
\end{{itemize}}

\begin{{figure}}[t]
\centering
\includegraphics[width=0.88\linewidth]{{{fig}/final_sparse_attention.pdf}}
\caption{{Branch-to-route sparse attention. Astrophysical analogues activate operator, closure and transport routes; the production-threshold branch is separated.}}
\end{{figure}}

\section{{Equation Receipts}}

\subsection{{Direct LHC-Safety Receipts}}
{receipt_table(pick_receipts(receipts, 'direct_lhc_safety', 5))}

\subsection{{Collider-Threshold or Event-Selection Hook}}
{receipt_table(threshold_receipts)}

\subsection{{Astrophysical Black-Hole Analogues}}
{receipt_table(astro_receipts)}

\subsection{{Stable Growth or Capture Branch}}
{receipt_table(stable_receipts)}

\subsection{{Evaporation Branch}}
{receipt_table(evaporation_receipts)}

\section{{Interpretation}}

Provenance remains necessary for attribution, incentives and chronology. It cannot settle a
physics mechanism by itself. In the selected LHC black-hole corpus, claim extraction finds many
statements and few safety or risk claims. Equation gating finds a different object: an empty
direct collider-safety branch under the source-local gate, plus adjacent black-hole mechanisms
that can constrain the collider branch if the transfer assumptions are stated.

\section{{Scope}}

All claims in this report are scoped to the selected corpus and the public gates. A complete
safety review would require a full literature selection, non-arXiv safety reports and human review
of the equation receipts. The repository provides a static separation between provenance and
mechanism graphs.

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
    operational = read_json(run_dir / "operational_graph.json")
    sparse = read_json(run_dir / "sparse_attention_audit.json")
    write_figures(graph, provenance, sparse, fig_dir)
    tex_path = write_tex(run_dir, paper_dir, manifest, graph, provenance, operational, sparse)
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
    parser = argparse.ArgumentParser(description="Build the final public LHC mechanism audit report.")
    parser.add_argument("--run-dir", default=str(DEFAULT_RUN), help="Static run artifact directory.")
    parser.add_argument("--paper-dir", default="paper", help="Paper output directory.")
    return parser


def main() -> None:
    print(json.dumps(build(build_parser().parse_args()), indent=2))


if __name__ == "__main__":
    main()
