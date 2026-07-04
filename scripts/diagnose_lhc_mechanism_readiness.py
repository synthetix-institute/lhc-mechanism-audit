#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import statistics
from collections import Counter
from pathlib import Path
from typing import Any


SEED_IDS = ["0806.3381", "0806.3414", "0807.3349", "0808.1415", "0808.4087", "0901.2948"]
DISPLAY_RE = re.compile(r"\\begin\{equation\*?\}|\\begin\{align\*?\}|\$\$")
BAD_FORMULA_RE = re.compile(
    r"\$|\\(?:cite|ref|eqref|label|caption|section|subsection|paragraph)\b|"
    r"\b(?:The|These|Those|This|We|Recall|Fortunately|Analogous|Comparable|models|copies|"
    r"emission|observed|discussed|predict|larger|smaller|existing|limits|depends|"
    r"reside|study|found)\b",
    re.I,
)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def pct(value: float) -> float:
    return round(100.0 * value, 3)


def source_stats(source_dir: Path) -> dict[str, Any]:
    files = sorted(source_dir.glob("*.tex"))
    sizes = [path.stat().st_size for path in files]
    if not files:
        return {"source_count": 0}

    docclass = 0
    begin_doc = 0
    display_sources = 0
    display_markers = 0
    for path in files:
        text = path.read_text(encoding="utf-8", errors="replace")
        docclass += int("\\documentclass" in text)
        begin_doc += int("\\begin{document}" in text)
        markers = len(DISPLAY_RE.findall(text))
        display_markers += markers
        display_sources += int(markers > 0)

    seed_rows = []
    for seed in SEED_IDS:
        path = source_dir / f"{seed}.tex"
        seed_rows.append({
            "paper_id": seed,
            "present": path.exists(),
            "bytes": path.stat().st_size if path.exists() else 0,
            "has_display_equation_marker": bool(path.exists() and DISPLAY_RE.search(path.read_text(encoding="utf-8", errors="replace"))),
        })

    ordered = sorted(sizes)
    return {
        "source_count": len(files),
        "bytes": {
            "min": min(sizes),
            "median": statistics.median(sizes),
            "mean": statistics.mean(sizes),
            "p75": ordered[int(0.75 * (len(ordered) - 1))],
            "p90": ordered[int(0.90 * (len(ordered) - 1))],
            "max": max(sizes),
        },
        "under_5kb": sum(size <= 5000 for size in sizes),
        "under_5kb_rate": sum(size <= 5000 for size in sizes) / len(sizes),
        "full_latex_markers": {
            "documentclass_sources": docclass,
            "begin_document_sources": begin_doc,
            "display_equation_sources": display_sources,
            "display_equation_markers": display_markers,
        },
        "seed_sources": seed_rows,
    }


def droplet_reference_stats(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"present": False}
    text = path.read_text(encoding="utf-8", errors="replace")
    return {
        "present": True,
        "bytes": len(text),
        "equation_envs": len(re.findall(r"\\begin\{equation\*?\}", text)),
        "align_envs": len(re.findall(r"\\begin\{align\*?\}", text)),
        "equation_labels": len(re.findall(r"\\label\{eq:", text)),
        "tables": len(re.findall(r"\\begin\{tabular\}", text)),
        "figures": len(re.findall(r"\\begin\{figure\}", text)),
        "contains_force_balance": bool(re.search(r"force balance|F_M|F_D|F_W", text, re.I)),
        "contains_falsifier_or_controls": bool(re.search(r"falsif|control|erasure|fresh bath|written bath", text, re.I)),
    }


def witness_stats(out_dir: Path) -> dict[str, Any]:
    witnesses_path = out_dir / "equation_witnesses.json"
    graph_path = out_dir / "equation_mechanism_graph.json"
    chain_path = out_dir / "chain_evidence.json"
    if not witnesses_path.exists() or not graph_path.exists():
        return {"present": False}

    witnesses = read_json(witnesses_path).get("witnesses", [])
    graph = read_json(graph_path)
    seed_witnesses = {
        seed: sum(1 for witness in witnesses if witness.get("source_id") == seed)
        for seed in SEED_IDS
    }
    formulas = [str(witness.get("formula") or "") for witness in witnesses]
    bad_formula_count = sum(bool(BAD_FORMULA_RE.search(formula)) for formula in formulas)
    kind_counts = Counter(str(witness.get("kind")) for witness in witnesses)
    role_counts = Counter(str(witness.get("dominant_role")) for witness in witnesses)

    chain_bad = 0
    chain_formula_count = 0
    if chain_path.exists():
        chain = read_json(chain_path)
        for item in chain.get("chains", []):
            for role_items in (item.get("roles") or {}).values():
                for witness in role_items:
                    chain_formula_count += 1
                    chain_bad += int(bool(BAD_FORMULA_RE.search(str(witness.get("formula") or ""))))

    return {
        "present": True,
        "witness_count": len(witnesses),
        "kind_counts": dict(kind_counts),
        "dominant_role_counts": dict(role_counts),
        "bad_formula_count": bad_formula_count,
        "bad_formula_rate": bad_formula_count / max(1, len(witnesses)),
        "seed_witness_counts": seed_witnesses,
        "mechanism_graph_counts": {
            key: graph.get(key)
            for key in [
                "source_witness_count",
                "fingerprinted_node_count",
                "usable_mechanism_node_count",
                "case_relevant_mechanism_node_count",
                "evidence_grade_case_mechanism_node_count",
                "direct_lhc_safety_mechanism_node_count",
                "astrophysical_analogue_mechanism_node_count",
                "production_threshold_mechanism_node_count",
                "artifact_or_unusable_node_count",
            ]
        },
        "pair_status_counts": graph.get("pair_status_counts"),
        "formula_quality_counts": graph.get("formula_quality_counts"),
        "case_branch_counts": graph.get("case_branch_counts"),
        "chain_evidence_bad_formula_count": chain_bad,
        "chain_evidence_formula_count": chain_formula_count,
        "chain_evidence_bad_formula_rate": chain_bad / max(1, chain_formula_count),
    }


def diagnosis(report: dict[str, Any]) -> list[str]:
    out: list[str] = []
    src = report.get("source_stats") or {}
    wit = report.get("witness_stats") or {}
    if src.get("under_5kb_rate", 0) > 0.8:
        out.append("The selected LHC corpus is mostly title/abstract-scale text, not full papers.")
    if (src.get("full_latex_markers") or {}).get("begin_document_sources", 0) == 0:
        out.append("No selected source contains a full TeX document marker.")
    missing_seeds = [row["paper_id"] for row in src.get("seed_sources", []) if not row.get("present")]
    if missing_seeds:
        out.append(f"Critical seed papers are absent from the source folder: {', '.join(missing_seeds)}.")
    zero_seed_witnesses = [seed for seed, count in (wit.get("seed_witness_counts") or {}).items() if count == 0]
    if zero_seed_witnesses:
        out.append(f"No equation witnesses were extracted from seed papers: {', '.join(zero_seed_witnesses)}.")
    if wit.get("chain_evidence_bad_formula_rate", 0) > 0.2:
        out.append("The rendered chain evidence is contaminated by prose/math-boundary fragments.")
    counts = wit.get("mechanism_graph_counts") or {}
    if counts.get("direct_lhc_safety_mechanism_node_count", 0) == 0:
        out.append("The graph contains no formula-clean direct LHC-safety mechanism node.")
    if counts.get("astrophysical_analogue_mechanism_node_count", 0) > 0:
        out.append("The usable mechanism signal is mostly astrophysical analogue physics, not direct collider safety derivations.")
    return out


def write_markdown(path: Path, report: dict[str, Any]) -> None:
    src = report["source_stats"]
    wit = report["witness_stats"]
    drop = report["droplet_reference"]
    lines = [
        "# LHC Mechanism Readiness Diagnosis",
        "",
        "## Verdict",
        "",
    ]
    for item in report["diagnosis"]:
        lines.append(f"- {item}")
    lines += [
        "",
        "## Source Coverage",
        "",
        f"- selected source files: `{src.get('source_count')}`",
        f"- median source size: `{src.get('bytes', {}).get('median')}` bytes",
        f"- files under 5 KB: `{src.get('under_5kb')}` ({pct(src.get('under_5kb_rate', 0))}%)",
        f"- sources with `\\begin{{document}}`: `{src.get('full_latex_markers', {}).get('begin_document_sources')}`",
        f"- sources with display-equation markers: `{src.get('full_latex_markers', {}).get('display_equation_sources')}`",
        "",
        "Seed-paper coverage:",
        "",
    ]
    for row in src.get("seed_sources", []):
        lines.append(
            f"- `{row['paper_id']}`: present `{row['present']}`, bytes `{row['bytes']}`, "
            f"display markers `{row['has_display_equation_marker']}`"
        )
    lines += [
        "",
        "## Extracted Equation Layer",
        "",
        f"- equation witnesses: `{wit.get('witness_count')}`",
        f"- witness kinds: `{wit.get('kind_counts')}`",
        f"- bad formula rate in all witnesses: `{pct(wit.get('bad_formula_rate', 0))}%`",
        f"- bad formula rate in rendered chain evidence: `{pct(wit.get('chain_evidence_bad_formula_rate', 0))}%`",
        f"- mechanism graph counts: `{wit.get('mechanism_graph_counts')}`",
        f"- constructor pair statuses: `{wit.get('pair_status_counts')}`",
        "",
        "## Droplet Mechanism Reference",
        "",
        f"- bytes: `{drop.get('bytes')}`",
        f"- equation environments: `{drop.get('equation_envs')}`",
        f"- align environments: `{drop.get('align_envs')}`",
        f"- equation labels: `{drop.get('equation_labels')}`",
        f"- contains force balance: `{drop.get('contains_force_balance')}`",
        f"- contains controls/falsifiers: `{drop.get('contains_falsifier_or_controls')}`",
        "",
        "## Interpretation",
        "",
        "The droplet paper is a constructed mechanism model: it names variables, writes equations, closes the force balance, and defines falsifying controls. "
        "The current LHC artifact is mainly a graph over abstract-scale text plus short equation fragments. "
        "It can show that adjacent astrophysical mechanisms exist, but it cannot by itself produce a source-backed LHC safety derivation.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", default="data/hf_lhc_selection_500k/sources")
    parser.add_argument("--out-dir", default="outputs/lhc_black_hole_audit_500k_strict")
    parser.add_argument("--droplet-tex", default="../tex/active_memory_chemotactic_droplets/active_memory_chemotactic_droplets.tex")
    parser.add_argument("--out-json", default="outputs/lhc_black_hole_audit_500k_strict/mechanism_readiness_diagnosis.json")
    parser.add_argument("--out-md", default="outputs/lhc_black_hole_audit_500k_strict/mechanism_readiness_diagnosis.md")
    args = parser.parse_args()

    report = {
        "report_type": "lhc_mechanism_readiness_diagnosis",
        "source_dir": args.source_dir,
        "out_dir": args.out_dir,
        "source_stats": source_stats(Path(args.source_dir)),
        "witness_stats": witness_stats(Path(args.out_dir)),
        "droplet_reference": droplet_reference_stats(Path(args.droplet_tex)),
    }
    report["diagnosis"] = diagnosis(report)
    out_json = Path(args.out_json)
    out_md = Path(args.out_md)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    write_markdown(out_md, report)
    print(json.dumps({"json": str(out_json), "markdown": str(out_md), "diagnosis": report["diagnosis"]}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
