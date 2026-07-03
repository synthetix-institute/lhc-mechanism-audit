#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any, Dict, List, Tuple


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SUMMARY = ROOT / "runs" / "lhc_black_hole_audit_500k_strict" / "summary.json"
CASE_BRANCHES = [
    "direct_lhc_safety",
    "production_threshold_branch",
    "astrophysical_black_hole_analogue",
    "stable_growth_or_capture_branch",
    "evaporation_branch",
]


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def graph_summary(graph: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "source_equation_witnesses": graph.get("source_witness_count", 0),
        "fingerprinted_mechanism_nodes": graph.get("fingerprinted_node_count", 0),
        "usable_non_artifact_mechanism_nodes": graph.get("usable_mechanism_node_count", 0),
        "case_relevant_mechanism_nodes": graph.get("case_relevant_mechanism_node_count", 0),
        "evidence_grade_case_mechanism_nodes": graph.get("evidence_grade_case_mechanism_node_count", 0),
        "direct_lhc_safety_mechanism_nodes": graph.get("direct_lhc_safety_mechanism_node_count", 0),
        "collider_threshold_selection_nodes": graph.get("production_threshold_mechanism_node_count", 0),
        "astrophysical_analogue_mechanism_nodes": graph.get("astrophysical_analogue_mechanism_node_count", 0),
        "artifact_or_unusable_nodes": graph.get("artifact_or_unusable_node_count", 0),
        "source_local_route_transition_edges": len(graph.get("edges") or []),
        "case_relevant_source_local_route_transition_edges": len(graph.get("case_source_local_edges") or []),
        "rich_cross_source_route_analogues": len(graph.get("analog_edges") or []),
        "case_internal_rich_analogues": len(graph.get("case_internal_analog_edges") or []),
        "case_transfer_rich_analogues": len(graph.get("case_transfer_analog_edges") or []),
        "evidence_grade_case_internal_rich_analogues": len(graph.get("evidence_grade_case_internal_analog_edges") or []),
        "evidence_grade_case_transfer_rich_analogues": len(graph.get("evidence_grade_case_transfer_analog_edges") or []),
        "route_counts": graph.get("route_counts") or {},
        "case_category_counts": graph.get("case_category_counts") or {},
        "evidence_grade_branch_counts": graph.get("case_branch_counts") or {},
    }


def load_summary(out_dir: Path, summary_path: Path) -> Dict[str, Any]:
    graph_path = out_dir / "equation_mechanism_graph.json"
    if graph_path.exists():
        summary = graph_summary(read_json(graph_path))
        manifest_path = out_dir / "manifest.json"
        if manifest_path.exists():
            manifest = read_json(manifest_path)
            summary["selected_sources"] = manifest.get("source_count", 0)
        return summary
    return read_json(summary_path)


def load_sparse(out_dir: Path) -> Dict[str, Any]:
    sparse_path = out_dir / "sparse_attention_audit.json"
    if sparse_path.exists():
        return read_json(sparse_path)
    return {}


def ensure_matplotlib():
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        return plt
    except Exception:
        return None


def write_placeholder(path: Path, title: str, lines: List[str]) -> None:
    path.with_suffix(".txt").write_text(title + "\n" + "\n".join(lines) + "\n", encoding="utf-8")


def plot_evidence_funnel(summary: Dict[str, Any], figure_dir: Path) -> None:
    plt = ensure_matplotlib()
    labels = [
        "equation witnesses",
        "usable mechanism nodes",
        "case-relevant nodes",
        "evidence-grade nodes",
        "astro analogues",
        "threshold hooks",
        "direct safety",
    ]
    values = [
        int(summary.get("source_equation_witnesses") or 0),
        int(summary.get("usable_non_artifact_mechanism_nodes") or 0),
        int(summary.get("case_relevant_mechanism_nodes") or 0),
        int(summary.get("evidence_grade_case_mechanism_nodes") or 0),
        int(summary.get("astrophysical_analogue_mechanism_nodes") or 0),
        int(summary.get("collider_threshold_selection_nodes") or 0),
        int(summary.get("direct_lhc_safety_mechanism_nodes") or 0),
    ]
    if plt is None:
        write_placeholder(figure_dir / "evidence_funnel.pdf", "Evidence funnel", [f"{label}: {value}" for label, value in zip(labels, values)])
        return
    fig, ax = plt.subplots(figsize=(7.2, 3.9))
    colors = ["#2f5d7c", "#3c7d7b", "#5b946e", "#9aa35d", "#bf8c45", "#b65c39", "#7b2835"]
    ax.barh(range(len(labels)), values, color=colors)
    ax.set_yticks(range(len(labels)), labels)
    ax.invert_yaxis()
    ax.set_xlabel("count")
    ax.set_title("Strict evidence funnel")
    for i, value in enumerate(values):
        ax.text(value + max(values) * 0.012, i, str(value), va="center", fontsize=9)
    ax.set_xlim(0, max(values) * 1.15 if values else 1)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(figure_dir / "evidence_funnel.pdf")
    plt.close(fig)


def plot_provenance_vs_mechanism(summary: Dict[str, Any], figure_dir: Path) -> None:
    plt = ensure_matplotlib()
    if plt is None:
        write_placeholder(figure_dir / "provenance_vs_mechanism.pdf", "Provenance vs mechanism", [])
        return
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.4))
    panels = [
        (
            axes[0],
            "Provenance graph",
            [
                ("papers", int(summary.get("selected_sources") or 0)),
                ("claims / stances", 0),
                ("citations / attribution", 0),
                ("mechanism test", None),
            ],
            "#d9e2ec",
        ),
        (
            axes[1],
            "Mechanism graph",
            [
                ("equation witnesses", int(summary.get("source_equation_witnesses") or 0)),
                ("usable mechanisms", int(summary.get("usable_non_artifact_mechanism_nodes") or 0)),
                ("case mechanisms", int(summary.get("case_relevant_mechanism_nodes") or 0)),
                ("direct safety", int(summary.get("direct_lhc_safety_mechanism_nodes") or 0)),
            ],
            "#dcebdc",
        ),
    ]
    for ax, title, boxes, color in panels:
        ax.set_title(title)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis("off")
        for i, (label, value) in enumerate(boxes):
            y = 0.82 - i * 0.21
            text = label if value is None else f"{label}\n{value}"
            rect = plt.Rectangle((0.13, y - 0.07), 0.74, 0.13, facecolor=color, edgecolor="#334", linewidth=1.0)
            ax.add_patch(rect)
            ax.text(0.5, y, text, ha="center", va="center", fontsize=9)
            if i < len(boxes) - 1:
                ax.annotate("", xy=(0.5, y - 0.14), xytext=(0.5, y - 0.075), arrowprops={"arrowstyle": "->", "lw": 1})
    fig.tight_layout(rect=[0, 0, 1, 0.98])
    fig.savefig(figure_dir / "provenance_vs_mechanism.pdf", bbox_inches="tight")
    plt.close(fig)


def plot_translation_graph(summary: Dict[str, Any], figure_dir: Path) -> None:
    plt = ensure_matplotlib()
    if plt is None:
        write_placeholder(figure_dir / "mechanism_translation.pdf", "Mechanism translation", [])
        return
    fig, ax = plt.subplots(figsize=(7.2, 3.4))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis("off")
    boxes = [
        (1.4, 4.7, "Astrophysical\nblack-hole mechanisms", int(summary.get("astrophysical_analogue_mechanism_nodes") or 0), "#e8eef7"),
        (1.4, 2.9, "Accretion / evaporation\ncapture / survival", int(summary.get("evidence_grade_case_mechanism_nodes") or 0), "#e8eef7"),
        (5.0, 3.8, "Mechanism\ntranslation", None, "#f5edcf"),
        (8.4, 4.7, "Collider-threshold\nselection hook", int(summary.get("collider_threshold_selection_nodes") or 0), "#eadbd2"),
        (8.4, 2.9, "Direct LHC-safety\nmechanism", int(summary.get("direct_lhc_safety_mechanism_nodes") or 0), "#eadbd2"),
    ]
    for x, y, label, value, color in boxes:
        rect = plt.Rectangle((x - 1.15, y - 0.45), 2.3, 0.9, facecolor=color, edgecolor="#333", linewidth=1)
        ax.add_patch(rect)
        text = label if value is None else f"{label}\n{value}"
        ax.text(x, y, text, ha="center", va="center", fontsize=9)
    arrows = [((2.55, 4.7), (3.85, 4.0)), ((2.55, 2.9), (3.85, 3.55)), ((6.15, 4.0), (7.25, 4.7)), ((6.15, 3.55), (7.25, 2.9))]
    for start, end in arrows:
        ax.annotate("", xy=end, xytext=start, arrowprops={"arrowstyle": "->", "lw": 1.4, "color": "#333"})
    ax.text(5.0, 1.0, "Result: audit shifts from claim counting to mechanism transfer.", ha="center", fontsize=10)
    fig.tight_layout()
    fig.savefig(figure_dir / "mechanism_translation.pdf")
    plt.close(fig)


def plot_sparse_attention(sparse: Dict[str, Any], figure_dir: Path) -> None:
    plt = ensure_matplotlib()
    route_order = [
        "transport_flow",
        "constraint_closure",
        "spectral_operator",
        "boundary_weak_form",
        "commutator_incompatibility",
        "discrete_protocol",
    ]
    branch_attention = sparse.get("branch_route_attention") or {}
    branches = [branch for branch in CASE_BRANCHES if branch in branch_attention]
    if not branches:
        branches = list(branch_attention)[:5]
    if plt is None:
        write_placeholder(figure_dir / "sparse_attention_routes.pdf", "Sparse attention", [])
        return
    if not branches:
        fig, ax = plt.subplots(figsize=(7.2, 3.4))
        ax.axis("off")
        ax.text(
            0.5,
            0.58,
            "Sparse-attention audit requires\nsparse_attention_audit.json",
            ha="center",
            va="center",
            fontsize=13,
        )
        ax.text(
            0.5,
            0.35,
            "Run scripts/build_sparse_attention_audit.py on the full static graph.",
            ha="center",
            va="center",
            fontsize=9,
        )
        fig.tight_layout()
        fig.savefig(figure_dir / "sparse_attention_routes.pdf")
        plt.close(fig)
        return
    matrix = [[float(branch_attention.get(branch, {}).get(route, 0.0)) for route in route_order] for branch in branches]
    fig, ax = plt.subplots(figsize=(7.2, 3.4))
    im = ax.imshow(matrix, cmap="YlGnBu", vmin=0, vmax=max(0.01, max(max(row) for row in matrix)))
    ax.set_xticks(range(len(route_order)), [r.replace("_", "\n") for r in route_order], fontsize=8)
    ax.set_yticks(range(len(branches)), [b.replace("_", " ") for b in branches], fontsize=8)
    ax.set_title("Sparse attention: case branch to mechanism route")
    for i, row in enumerate(matrix):
        for j, value in enumerate(row):
            if value > 0:
                ax.text(j, i, f"{value:.2f}", ha="center", va="center", fontsize=7)
    fig.colorbar(im, ax=ax, fraction=0.035, pad=0.03)
    fig.tight_layout()
    fig.savefig(figure_dir / "sparse_attention_routes.pdf")
    plt.close(fig)


def latex_escape(text: Any) -> str:
    value = str(text)
    replacements = {
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
    }
    for src, dst in replacements.items():
        value = value.replace(src, dst)
    return value


def write_numbers_tex(summary: Dict[str, Any], path: Path) -> None:
    macros = {
        "SelectedSources": summary.get("selected_sources", 0),
        "EquationWitnesses": summary.get("source_equation_witnesses", 0),
        "UsableMechanisms": summary.get("usable_non_artifact_mechanism_nodes", 0),
        "CaseMechanisms": summary.get("case_relevant_mechanism_nodes", 0),
        "EvidenceGradeMechanisms": summary.get("evidence_grade_case_mechanism_nodes", 0),
        "DirectSafetyMechanisms": summary.get("direct_lhc_safety_mechanism_nodes", 0),
        "AstroAnalogues": summary.get("astrophysical_analogue_mechanism_nodes", 0),
        "ThresholdHooks": summary.get("collider_threshold_selection_nodes", 0),
        "CaseAnalogues": summary.get("case_internal_rich_analogues", 0),
        "CaseTransferAnalogues": summary.get("case_transfer_rich_analogues", 0),
    }
    lines = ["% Auto-generated by scripts/build_public_demo_report.py"]
    for name, value in macros.items():
        lines.append(f"\\newcommand{{\\{name}}}{{{value}}}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_latex(summary: Dict[str, Any], sparse: Dict[str, Any], paper_dir: Path) -> Path:
    tex_path = paper_dir / "lhc_mechanism_audit_demo.tex"
    findings = sparse.get("findings") or []
    finding_items = "\n".join(f"\\item {latex_escape(item)}" for item in findings[:4])
    if not finding_items:
        finding_items = r"\item Sparse-attention receipts are generated when \texttt{sparse\_attention\_audit.json} is available."

    tex = rf"""\documentclass[11pt]{{article}}
\usepackage[a4paper,margin=1in]{{geometry}}
\usepackage{{graphicx}}
\usepackage{{amsmath,amssymb}}
\usepackage{{booktabs}}
\usepackage{{hyperref}}
\usepackage{{xcolor}}
\usepackage{{caption}}

\IfFileExists{{generated/run_numbers.tex}}{{\input{{generated/run_numbers.tex}}}}{{%
\newcommand{{\SelectedSources}}{{{summary.get('selected_sources', 0)}}}
\newcommand{{\EquationWitnesses}}{{{summary.get('source_equation_witnesses', 0)}}}
\newcommand{{\UsableMechanisms}}{{{summary.get('usable_non_artifact_mechanism_nodes', 0)}}}
\newcommand{{\CaseMechanisms}}{{{summary.get('case_relevant_mechanism_nodes', 0)}}}
\newcommand{{\EvidenceGradeMechanisms}}{{{summary.get('evidence_grade_case_mechanism_nodes', 0)}}}
\newcommand{{\DirectSafetyMechanisms}}{{{summary.get('direct_lhc_safety_mechanism_nodes', 0)}}}
\newcommand{{\AstroAnalogues}}{{{summary.get('astrophysical_analogue_mechanism_nodes', 0)}}}
\newcommand{{\ThresholdHooks}}{{{summary.get('collider_threshold_selection_nodes', 0)}}}
\newcommand{{\CaseAnalogues}}{{{summary.get('case_internal_rich_analogues', 0)}}}
\newcommand{{\CaseTransferAnalogues}}{{{summary.get('case_transfer_rich_analogues', 0)}}}
}}

\title{{A Mechanism-First Audit of the LHC Black-Hole Safety Debate}}
\author{{Public demo generated from static audit artifacts}}
\date{{}}

\begin{{document}}
\sloppy
\maketitle

\begin{{abstract}}
Scientific evidence has two separable graph layers. A provenance graph records who
made a claim, where it appears, and how sources support or challenge one another.
A mechanism graph records something different: which equations instantiate the
physical steps by which a claim could become true. We demonstrate the distinction
on the LHC microscopic-black-hole debate using only static public audit artifacts.
In \SelectedSources{{}} selected arXiv sources, the strict gate recovered
\EquationWitnesses{{}} equation witnesses, \UsableMechanisms{{}} formula-clean
mechanism nodes, \CaseMechanisms{{}} LHC-black-hole case-relevant nodes, and
\EvidenceGradeMechanisms{{}} evidence-grade case nodes. The branch split was
asymmetric: \DirectSafetyMechanisms{{}} source-local formula-clean direct
LHC-safety mechanisms, \ThresholdHooks{{}} collider-threshold or event-selection
hook, and \AstroAnalogues{{}} astrophysical black-hole analogues. The substantive
output is therefore not another list of stances. It is a map of which physical
mechanisms are present in the corpus and which translation steps from adjacent
black-hole physics would have to be made explicit.
\end{{abstract}}

\section{{The Problem}}

Most automated controversy maps stop at statements: a source said that the collider
is safe, unsafe, misleading, or incomplete. That representation is useful, but it
places all evidence on the same social layer. The LHC black-hole case requires a
different object. The scientific content is the branch structure of the proposed
mechanism:
\[
\begin{{aligned}}
\mathrm{{production}} &\rightarrow \mathrm{{evaporation\ or\ stability}}
\rightarrow \mathrm{{capture/stopping}}\\
&\rightarrow \mathrm{{accretion/growth}}
\rightarrow \mathrm{{astrophysical\ bound}} .
\end{{aligned}}
\]
Each arrow is a physical slot that must be filled by equations, observations, or
controlled assumptions. This is why the demo builds two graphs from the same
papers.

\section{{Two Graphs in the Same Archive}}

\textbf{{Provenance graph.}} Nodes are sources and claims. Edges record that a
source makes a claim, belongs to a claim family, or supports a stated position.
This graph answers attribution questions: who said what, where, and in relation
to which other sources.

\textbf{{Mechanism graph.}} Nodes are equation witnesses and local formula
transitions. Edges record source-local route transitions and cross-source route
analogues. A node is evidence-grade only if the local formula window contains
both the black-hole case and a mechanism category. Source-level words alone are
not enough. In this report, ``formula-clean'' means that the extracted local
window survived the equation-quality gate and retained a recognizable mathematical
relation, not just prose or bibliographic residue.

\begin{{figure}}[t]
\centering
\IfFileExists{{figures/provenance_vs_mechanism.pdf}}{{\includegraphics[width=0.92\linewidth]{{figures/provenance_vs_mechanism.pdf}}}}{{\fbox{{Missing figure: provenance\_vs\_mechanism.pdf}}}}
\caption{{A provenance graph and a mechanism graph answer different questions. The first organizes attribution. The second records whether equation-level mechanisms are present and whether they can be translated between branches.}}
\end{{figure}}

\section{{Mechanism Gates}}

The mechanism graph uses six route labels as an interface to equation
transformations. The labels are deliberately coarse: they are gates for audit,
not names for complete theories.
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
A receipt is a local equation witness that activates one or more of these gates
inside a case-relevant formula window. This makes the audit stricter than keyword
search but more inspectable than an uninterpreted embedding.

\section{{Results}}

\begin{{figure}}[t]
\centering
\IfFileExists{{figures/evidence_funnel.pdf}}{{\includegraphics[width=0.86\linewidth]{{figures/evidence_funnel.pdf}}}}{{\fbox{{Missing figure: evidence\_funnel.pdf}}}}
\caption{{Strict evidence funnel. Most extracted witnesses are rejected or kept only as audit material. The public result is the branch split: no direct safety mechanism under the gate, one threshold hook, and many adjacent astrophysical mechanisms.}}
\end{{figure}}

The strict run gives the following public counts:
\[
\begin{{array}}{{lr}}
\text{{equation witnesses}} & \EquationWitnesses\\
\text{{usable formula-clean mechanism nodes}} & \UsableMechanisms\\
\text{{case-relevant nodes}} & \CaseMechanisms\\
\text{{evidence-grade case nodes}} & \EvidenceGradeMechanisms\\
\text{{direct LHC-safety mechanisms}} & \DirectSafetyMechanisms\\
\text{{collider-threshold hooks}} & \ThresholdHooks\\
\text{{astrophysical black-hole analogues}} & \AstroAnalogues.
\end{{array}}
\]

The result is precise within the selected corpus and gate definition. Direct
source-local LHC-safety equations did not survive the strict evidence gate.
Adjacent black-hole physics did: accretion, evaporation, capture, mass growth and
compact-object survival. The scientific task exposed by the graph is therefore a
translation problem: which adjacent mechanisms can be carried into the collider
branch, and what assumptions are required for that transfer?

\section{{Mechanism Translation to the LHC Branch}}

The equations below state the slots that the audit tries to fill. A collider
branch first needs a production or event-selection condition, for example
\[
\sqrt{{s}} > M_D ,
\]
followed by a branch decision. If evaporation dominates, the relevant local
receipt should support a mass-loss inequality or lifetime ordering such as
\[
\frac{{dM}}{{dt}} < 0,\qquad \tau_{{\rm evap}}\ll \tau_{{\rm capture}}.
\]
If a stable object is assumed, the mechanism changes to stopping, capture and
growth:
\[
\frac{{dM}}{{dt}} = \rho\,\sigma(M)\,v .
\]
Astrophysical survival bounds then become external tests on the same mechanism.
A dangerous growth branch would have to be compatible with compact-object
observations; schematically,
\[
t_{{\rm grow}} < t_{{\rm WD}}
\]
would conflict with the observed survival of white dwarfs if the same production,
capture and growth mechanism were already realized in nature. The graph therefore
does not merely count black-hole papers. It separates the collider threshold,
the evaporation branch, the stable-growth branch and the astrophysical bound.

\begin{{figure}}[t]
\centering
\IfFileExists{{figures/mechanism_translation.pdf}}{{\includegraphics[width=0.92\linewidth]{{figures/mechanism_translation.pdf}}}}{{\fbox{{Missing figure: mechanism\_translation.pdf}}}}
\caption{{The demo result is a mechanism-translation map. Adjacent black-hole mechanisms provide the inspectable scientific substrate. The collider branch supplies only a threshold hook in this run.}}
\end{{figure}}

\section{{Sparse-Attention Support}}

The sparse-attention audit reads the static mechanism graph and asks which routes
co-activate in the evidence-grade case layer. It is a consistency check on the
branch split: if the graph is meaningful, adjacent astrophysical receipts should
concentrate in growth, capture, evaporation or boundary-style mechanisms rather
than in direct collider-safety derivations.

\begin{{itemize}}
{finding_items}
\end{{itemize}}

\begin{{figure}}[t]
\centering
\IfFileExists{{figures/sparse_attention_routes.pdf}}{{\includegraphics[width=0.92\linewidth]{{figures/sparse_attention_routes.pdf}}}}{{\fbox{{Missing figure: sparse\_attention\_routes.pdf}}}}
\caption{{Sparse co-activation between case branches and mechanism routes. The important signal is concentration in adjacent astrophysical mechanisms, not direct collider-safety derivations.}}
\end{{figure}}

\section{{What the Mechanism Graph Adds}}

A provenance-only graph can identify papers, authors, dates and claim families.
It is useful for scrutiny of attribution and incentives. The mechanism graph adds
the missing scientific layer: whether a claimed branch has equation-level support.
In this run, provenance can organize disagreement about LHC safety, but the
mechanism graph explains the structure of the evidence. The direct safety branch
is empty under the strict gate. The adjacent astrophysical branch is populated.
This distinction is not visible from a claim map alone.

\section{{Scope and Reproducibility}}

The repository is a public audit object built from static outputs. It is designed
to be inspectable without private pipeline files: derived graphs, run summaries,
figures and report text are included; raw fingerprints, model checkpoints and core
pipeline code are not. A complete safety review would extend the same audit to
the full literature search and to non-arXiv safety reports.

\end{{document}}
"""
    tex_path.write_text(tex, encoding="utf-8")
    return tex_path


def build(args: argparse.Namespace) -> Dict[str, Any]:
    out_dir = Path(args.out_dir)
    paper_dir = Path(args.paper_dir)
    figure_dir = paper_dir / "figures"
    generated_dir = paper_dir / "generated"
    figure_dir.mkdir(parents=True, exist_ok=True)
    generated_dir.mkdir(parents=True, exist_ok=True)

    summary = load_summary(out_dir, Path(args.summary))
    sparse = load_sparse(out_dir)

    write_numbers_tex(summary, generated_dir / "run_numbers.tex")
    plot_evidence_funnel(summary, figure_dir)
    plot_provenance_vs_mechanism(summary, figure_dir)
    plot_translation_graph(summary, figure_dir)
    plot_sparse_attention(sparse, figure_dir)
    tex_path = write_latex(summary, sparse, paper_dir)

    manifest = {
        "report_type": "lhc_public_demo_report",
        "readiness": "usable",
        "paper": str(tex_path),
        "figures": {
            "evidence_funnel": str(figure_dir / "evidence_funnel.pdf"),
            "provenance_vs_mechanism": str(figure_dir / "provenance_vs_mechanism.pdf"),
            "mechanism_translation": str(figure_dir / "mechanism_translation.pdf"),
            "sparse_attention_routes": str(figure_dir / "sparse_attention_routes.pdf"),
        },
        "numbers": str(generated_dir / "run_numbers.tex"),
        "source": str(out_dir),
    }
    (generated_dir / "public_demo_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build public LaTeX demo report and figures from static audit artifacts.")
    parser.add_argument("--out-dir", required=True, help="Directory containing static audit outputs.")
    parser.add_argument("--paper-dir", default="paper", help="Directory where LaTeX and figures are written.")
    parser.add_argument("--summary", default=str(DEFAULT_SUMMARY), help="Fallback sanitized summary JSON.")
    return parser


def main() -> None:
    print(json.dumps(build(build_parser().parse_args()), indent=2))


if __name__ == "__main__":
    main()
