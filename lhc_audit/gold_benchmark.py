from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List

from .evidence_contract import SLOT_CONTRACTS, match_equation_to_slot
from .extract import extract_equations, iter_documents, local_context


def _slot(slot_id: str) -> Dict[str, Any]:
    for slot in SLOT_CONTRACTS:
        if slot["slot_id"] == slot_id:
            return slot
    raise KeyError(slot_id)


def evaluate_gold_benchmark(
    sources_dir: Path,
    benchmark_path: Path,
    *,
    context_window: int = 900,
) -> Dict[str, Any]:
    benchmark = json.loads(benchmark_path.read_text(encoding="utf-8"))
    documents = {document.source_id: document for document in iter_documents(sources_dir)}
    paper_results: List[Dict[str, Any]] = []
    missing_sources: List[str] = []
    failed_receipts: List[str] = []
    formula_found_contract_failed: List[str] = []
    total_receipts = 0
    recovered_receipts = 0

    for paper in benchmark.get("papers") or []:
        source_id = str(paper["arxiv_id"])
        document = documents.get(source_id)
        if document is None:
            if paper.get("required_source", True):
                missing_sources.append(source_id)
            paper_results.append({
                "arxiv_id": source_id,
                "source_present": False,
                "receipt_results": [],
            })
            continue

        equations = extract_equations(document.text)
        receipt_results: List[Dict[str, Any]] = []
        for expected in paper.get("receipts") or []:
            total_receipts += 1
            formula_pattern = re.compile(str(expected["formula_regex"]), re.S)
            context_pattern = re.compile(str(expected.get("context_regex") or ".*"), re.I | re.S)
            slot = _slot(str(expected["slot_id"]))
            formula_candidates = []
            accepted = None
            for equation in equations:
                formula = str(equation["formula"])
                if not formula_pattern.search(formula):
                    continue
                context = local_context(
                    document.text,
                    int(equation["start"]),
                    int(equation["end"]),
                    window=context_window,
                )
                context_ok = bool(context_pattern.search(context))
                node = {
                    "source_id": source_id,
                    "source_equation_ordinal": equation.get("ordinal"),
                    "formula": formula,
                    "context": context,
                    "route_signature": [],
                }
                contract_ok, contract = match_equation_to_slot(node, slot)
                candidate = {
                    "equation_ordinal": equation.get("ordinal"),
                    "kind": equation.get("kind"),
                    "formula": " ".join(formula.split()),
                    "context": " ".join(context.split()),
                    "context_match": context_ok,
                    "contract_match": contract_ok,
                    "contract": contract,
                }
                formula_candidates.append(candidate)
                if context_ok and contract_ok:
                    accepted = candidate
                    break

            receipt_id = str(expected["receipt_id"])
            recovered = accepted is not None
            if recovered:
                recovered_receipts += 1
            else:
                failed_receipts.append(receipt_id)
                if any(candidate["context_match"] for candidate in formula_candidates):
                    formula_found_contract_failed.append(receipt_id)
            receipt_results.append({
                "receipt_id": receipt_id,
                "slot_id": expected["slot_id"],
                "recovered": recovered,
                "accepted": accepted,
                "formula_candidate_count": len(formula_candidates),
                "formula_candidates": formula_candidates[:4],
            })

        paper_results.append({
            "arxiv_id": source_id,
            "source_present": True,
            "equation_count": len(equations),
            "title": document.metadata.get("title"),
            "citation_count": len(document.cited_arxiv_ids),
            "receipt_results": receipt_results,
        })

    required_source_count = sum(1 for paper in benchmark.get("papers") or [] if paper.get("required_source", True))
    present_required_sources = required_source_count - len(missing_sources)
    source_coverage = present_required_sources / max(1, required_source_count)
    receipt_coverage = recovered_receipts / max(1, total_receipts)
    readiness = "usable" if not missing_sources and not failed_receipts else "incomplete_gold_coverage"
    return {
        "report_type": "lhc_mechanism_gold_benchmark",
        "readiness": readiness,
        "schema": benchmark.get("schema"),
        "sources_dir": str(sources_dir),
        "benchmark": str(benchmark_path),
        "required_source_count": required_source_count,
        "present_required_sources": present_required_sources,
        "source_coverage": source_coverage,
        "total_receipts": total_receipts,
        "recovered_receipts": recovered_receipts,
        "receipt_coverage": receipt_coverage,
        "missing_sources": missing_sources,
        "failed_receipts": failed_receipts,
        "formula_found_contract_failed": formula_found_contract_failed,
        "papers": paper_results,
    }


def render_gold_markdown(result: Dict[str, Any]) -> str:
    lines = [
        "# LHC Primary-Source Mechanism Regression",
        "",
        f"Readiness: `{result['readiness']}`",
        "",
        f"Primary-source coverage: `{result['present_required_sources']}/{result['required_source_count']}`.",
        f"Typed equation-receipt coverage: `{result['recovered_receipts']}/{result['total_receipts']}`.",
        "",
        "| Paper | Equations | Required receipts recovered |",
        "|---|---:|---:|",
    ]
    for paper in result["papers"]:
        receipts = paper.get("receipt_results") or []
        recovered = sum(1 for receipt in receipts if receipt.get("recovered"))
        equations = paper.get("equation_count", 0) if paper.get("source_present") else "missing"
        lines.append(f"| `{paper['arxiv_id']}` | {equations} | {recovered}/{len(receipts)} |")
    if result["failed_receipts"]:
        lines += ["", "Missing typed receipts:", ""]
        lines.extend(f"- `{receipt}`" for receipt in result["failed_receipts"])
    return "\n".join(lines).rstrip() + "\n"


def write_gold_benchmark(
    sources_dir: Path,
    benchmark_path: Path,
    out_json: Path,
    out_markdown: Path,
) -> Dict[str, Any]:
    result = evaluate_gold_benchmark(sources_dir, benchmark_path)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_markdown.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    out_markdown.write_text(render_gold_markdown(result), encoding="utf-8")
    return result
