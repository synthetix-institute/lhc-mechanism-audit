#!/usr/bin/env python3
"""Build the machine-readable receipt bundle used by the judges' guide."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "runs" / "lhc_black_hole_audit_revised"
SCREEN_RUN = ROOT / "runs" / "lhc_black_hole_audit_500k_strict"
PAPER = ROOT / "paper"
GENERATED = PAPER / "generated"

SELECTED_RECEIPTS = (
    "E00292",  # production cross-section
    "E00455",  # evaporation rate
    "E00124",  # coupled momentum and mass evolution
    "E00149",  # stopping and mass gain per path length
    "E00179",  # compact-star growth times
    "E00202",  # neutron-star consequence
)


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def tex_command(name: str, value: Any) -> str:
    return f"\\newcommand{{\\{name}}}{{{value}}}"


def require_files(paths: Iterable[Path]) -> None:
    missing = [str(path) for path in paths if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing judge-guide inputs: " + ", ".join(missing))


def build() -> Dict[str, Any]:
    inputs = {
        "manifest": RUN / "manifest.json",
        "screen_manifest": SCREEN_RUN / "manifest.json",
        "equation_graph": RUN / "equation_mechanism_graph.json",
        "constructor": RUN / "physical_constructor.json",
        "knowledge_graph": RUN / "public_knowledge_graph.json",
        "benchmark": RUN / "lhc_gold_benchmark.json",
        "comparison": RUN / "discourse_vs_mechanism_attention.json",
        "sparse_attention": RUN / "sparse_attention_audit.json",
    }
    require_files(inputs.values())

    manifest = load_json(inputs["manifest"])
    screen_manifest = load_json(inputs["screen_manifest"])
    equation_graph = load_json(inputs["equation_graph"])
    constructor = load_json(inputs["constructor"])
    knowledge_graph = load_json(inputs["knowledge_graph"])
    benchmark = load_json(inputs["benchmark"])
    comparison = load_json(inputs["comparison"])
    sparse_attention = load_json(inputs["sparse_attention"])

    nodes = {node["id"]: node for node in equation_graph["nodes"]}
    missing_receipts = [node_id for node_id in SELECTED_RECEIPTS if node_id not in nodes]
    if missing_receipts:
        raise ValueError(f"Selected receipt nodes are absent: {missing_receipts}")

    if benchmark["recovered_receipts"] != benchmark["total_receipts"]:
        raise ValueError("The prespecified primary-source equation benchmark is incomplete.")

    slots: List[Dict[str, Any]] = []
    for slot in constructor["slots"]:
        slots.append(
            {
                "slot_id": slot["slot_id"],
                "label": slot["label"],
                "status": slot["status"],
                "direct_receipt_count": slot["direct_receipt_count"],
                "candidate_transfer_count": slot["candidate_transfer_count"],
                "inputs": slot["inputs"],
                "outputs": slot["outputs"],
            }
        )

    receipts: List[Dict[str, Any]] = []
    for node_id in SELECTED_RECEIPTS:
        node = nodes[node_id]
        receipts.append(
            {
                "node_id": node_id,
                "source_id": node["source_id"],
                "source_title": node["source_title"],
                "source_url": node["source_url"],
                "source_equation_ordinal": node["source_equation_ordinal"],
                "source_start": node["source_start"],
                "source_end": node["source_end"],
                "formula": node["formula"],
                "source_context": node.get("context", ""),
                "route_signature": node["route_signature"],
                "constructor_roles": node["constructor_roles"],
                "case_categories": node["case_evidence"]["categories"],
                "case_branches": node["case_evidence"]["branch_labels"],
            }
        )

    kg_summary = knowledge_graph["summary"]
    metrics = {
        "global_archive_documents": 2500000,
        "documents_screened": 500000,
        "screened_sources_retained": screen_manifest["source_count"],
        "papers_in_reconstruction": manifest["source_count"],
        "claims": manifest["claim_count"],
        "citation_links": kg_summary["provenance_edge_type_counts"]["paper_cites_paper"],
        "equation_windows": manifest["equation_witness_count"],
        "fingerprinted_equations": equation_graph["fingerprinted_node_count"],
        "usable_equation_nodes": equation_graph["usable_mechanism_node_count"],
        "source_local_equation_edges": len(equation_graph["case_source_local_edges"]),
        "cross_paper_analogue_edges": len(equation_graph["analog_edges"]),
        "strict_equation_receipts": sparse_attention["strict_receipt_node_count"],
        "attended_receipt_edges": sparse_attention["attended_edge_count"],
        "knowledge_graph_nodes": knowledge_graph["node_count"],
        "knowledge_graph_edges": knowledge_graph["edge_count"],
        "benchmark_receipts_recovered": benchmark["recovered_receipts"],
        "benchmark_receipts_total": benchmark["total_receipts"],
    }

    bundle = {
        "report_type": "epistack_judge_receipt_bundle",
        "readiness": "usable",
        "question": "Could the Large Hadron Collider make a dangerous black hole?",
        "answer": (
            "The processed literature contains no physically complete catastrophe path. "
            "The semiclassical branch ends in evaporation; stable-object branches are "
            "constrained by stopping, growth-time and compact-star survival calculations."
        ),
        "two_graphs": {
            "provenance": "Who wrote, cited or asserted each claim.",
            "mechanism": "Which physical quantity each equation transforms and whether the transformations compose.",
        },
        "metrics": metrics,
        "constructor": {
            "danger_branch_closed": constructor["branch_closed"],
            "reported_branch_verdict": constructor["branch_verdict"],
            "interpretation": (
                "The dangerous branch requires astronomical-bound evasion. No direct receipt "
                "fills that condition; the retained compact-star equation predicts a rapid "
                "consequence instead, so observation closes the branch against danger."
            ),
            "slots": slots,
            "supported_transitions": constructor["supported_transitions"],
            "broken_transitions": constructor["broken_transitions"],
        },
        "selected_equation_receipts": receipts,
        "proof_checks": comparison["proof_checks"],
        "benchmark": {
            "source_coverage": benchmark["source_coverage"],
            "receipt_coverage": benchmark["receipt_coverage"],
            "failed_receipts": benchmark["failed_receipts"],
        },
        "artifact_index": {key: str(path.relative_to(ROOT)) for key, path in inputs.items()},
        "supporting_article": "paper/lhc_black_hole_answer.pdf",
    }

    GENERATED.mkdir(parents=True, exist_ok=True)
    bundle_path = PAPER / "lhc_judges_guide_receipts.json"
    with bundle_path.open("w", encoding="utf-8") as handle:
        json.dump(bundle, handle, indent=2, ensure_ascii=True)
        handle.write("\n")

    commands = [
        tex_command("GlobalArchiveDocuments", "2.5 million"),
        tex_command("DocumentsScreened", f"{metrics['documents_screened']:,}"),
        tex_command("ScreenedSources", f"{metrics['screened_sources_retained']:,}"),
        tex_command("PaperCount", f"{metrics['papers_in_reconstruction']:,}"),
        tex_command("ClaimCount", f"{metrics['claims']:,}"),
        tex_command("CitationCount", f"{metrics['citation_links']:,}"),
        tex_command("EquationWindowCount", f"{metrics['equation_windows']:,}"),
        tex_command("FingerprintCount", f"{metrics['fingerprinted_equations']:,}"),
        tex_command("UsableEquationCount", f"{metrics['usable_equation_nodes']:,}"),
        tex_command("SourceEdgeCount", f"{metrics['source_local_equation_edges']:,}"),
        tex_command("CrossPaperEdgeCount", f"{metrics['cross_paper_analogue_edges']:,}"),
        tex_command("StrictReceiptCount", f"{metrics['strict_equation_receipts']:,}"),
        tex_command("AttendedEdgeCount", f"{metrics['attended_receipt_edges']:,}"),
        tex_command("KnowledgeNodeCount", f"{metrics['knowledge_graph_nodes']:,}"),
        tex_command("KnowledgeEdgeCount", f"{metrics['knowledge_graph_edges']:,}"),
        tex_command("BenchmarkRecovered", benchmark["recovered_receipts"]),
        tex_command("BenchmarkTotal", benchmark["total_receipts"]),
    ]
    numbers_path = GENERATED / "judge_numbers.tex"
    numbers_path.write_text("\n".join(commands) + "\n", encoding="utf-8")

    manifest_out = {
        "report_type": "epistack_judges_guide_build",
        "readiness": "usable",
        "receipt_bundle": str(bundle_path.relative_to(ROOT)),
        "numbers": str(numbers_path.relative_to(ROOT)),
        "tex": "paper/lhc_judges_guide.tex",
        "pdf": "paper/lhc_judges_guide.pdf",
        "selected_receipts": list(SELECTED_RECEIPTS),
    }
    manifest_path = PAPER / "lhc_judges_guide_manifest.json"
    with manifest_path.open("w", encoding="utf-8") as handle:
        json.dump(manifest_out, handle, indent=2, ensure_ascii=True)
        handle.write("\n")
    return manifest_out


if __name__ == "__main__":
    print(json.dumps(build(), indent=2, ensure_ascii=True))
