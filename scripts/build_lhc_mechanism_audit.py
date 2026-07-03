#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from lhc_audit.extract import extract_equations, iter_documents, local_context
from lhc_audit.hyperion_adapter import fingerprint_pair
from lhc_audit.mechanism import build_operational_graph, classify_roles, dominant_role, extract_claims
from lhc_audit.render import render_audit_report, render_shallow_failure


def load_seed_papers(path: Path) -> List[Dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def source_metadata(source_id: str, seeds: List[Dict[str, Any]]) -> Dict[str, Any]:
    normalized = source_id.replace("/", "")
    for item in seeds:
        if item["arxiv_id"].replace("/", "") in normalized or normalized in item["arxiv_id"].replace("/", ""):
            return item
    return {"arxiv_id": source_id, "title": source_id, "authors": [], "stance": "unknown", "role": "unknown"}


def build(args: argparse.Namespace) -> Dict[str, Any]:
    papers_dir = Path(args.papers_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    seeds = load_seed_papers(Path(args.seed_papers))

    sources = []
    provenance_nodes = []
    provenance_edges = []
    witnesses = []
    claim_nodes = []

    for doc in iter_documents(papers_dir):
        meta = source_metadata(doc.source_id, seeds)
        sources.append({"source_id": doc.source_id, "path": doc.path, "metadata": meta})
        provenance_nodes.append({
            "id": doc.source_id,
            "title": meta.get("title"),
            "authors": meta.get("authors", []),
            "year": meta.get("year"),
            "stance": meta.get("stance", "unknown"),
            "role": meta.get("role", "unknown"),
            "url": meta.get("url"),
        })
        for claim in extract_claims(doc.text):
            claim_id = f"C{len(claim_nodes):05d}"
            claim_nodes.append({"id": claim_id, "source_id": doc.source_id, **claim})
            provenance_edges.append({
                "source": doc.source_id,
                "target": claim_id,
                "edge_type": "source_makes_claim",
            })

        equations = extract_equations(doc.text)
        for i, eq in enumerate(equations):
            context = local_context(doc.text, int(eq["start"]), int(eq["end"]), window=args.context_window)
            scores = classify_roles(context, eq["formula"])
            role = dominant_role(scores)
            prev_formula = equations[i - 1]["formula"] if i > 0 else ""
            next_formula = equations[i + 1]["formula"] if i + 1 < len(equations) else ""
            relation_target = next_formula or prev_formula or eq["formula"]
            fp = fingerprint_pair(
                eq["formula"],
                relation_target,
                "source_local_equation_transition",
                knowledgeparser_root=args.knowledgeparser_root,
            )
            witnesses.append({
                "source_id": doc.source_id,
                "path": doc.path,
                "formula": eq["formula"],
                "kind": eq["kind"],
                "context": context[: args.max_context_chars],
                "role_scores": scores,
                "dominant_role": role,
                "fingerprint": fp,
            })

    provenance = {
        "nodes": provenance_nodes + claim_nodes,
        "edges": provenance_edges,
        "claim_scope": "Provenance/discourse graph. It records sources and claim families, not mechanism validity.",
    }
    operational = build_operational_graph(witnesses)
    sources_obj = {"sources": sources}

    outputs = {
        "sources.json": sources_obj,
        "provenance_graph.json": provenance,
        "equation_witnesses.json": {"witnesses": witnesses},
        "operational_graph.json": operational,
    }
    for name, data in outputs.items():
        (out_dir / name).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    (out_dir / "shallow_failure.md").write_text(render_shallow_failure(provenance, operational), encoding="utf-8")
    (out_dir / "audit_report.md").write_text(render_audit_report(sources_obj, provenance, operational), encoding="utf-8")
    manifest = {
        "report_type": "lhc_mechanism_audit_manifest",
        "readiness": "usable" if witnesses else "no_equation_witnesses",
        "papers_dir": str(papers_dir),
        "out_dir": str(out_dir),
        "source_count": len(sources),
        "claim_count": len(claim_nodes),
        "equation_witness_count": len(witnesses),
        "chain_candidate_count": len(operational.get("chain_candidates", [])),
        "outputs": {k: str(out_dir / k) for k in outputs},
        "markdown": {
            "shallow_failure": str(out_dir / "shallow_failure.md"),
            "audit_report": str(out_dir / "audit_report.md"),
        },
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return manifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--papers-dir", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--seed-papers", default=str(ROOT / "data" / "seed_papers.json"))
    parser.add_argument("--knowledgeparser-root", default="")
    parser.add_argument("--context-window", type=int, default=700)
    parser.add_argument("--max-context-chars", type=int, default=1400)
    return parser


def main() -> None:
    print(json.dumps(build(build_parser().parse_args()), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
