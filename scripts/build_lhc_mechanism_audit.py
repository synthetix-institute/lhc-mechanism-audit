#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
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


def source_metadata(
    source_id: str,
    seeds: List[Dict[str, Any]],
    extracted: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    extracted = dict(extracted or {})
    normalized = source_id.replace("/", "")
    for item in seeds:
        if item["arxiv_id"].replace("/", "") in normalized or normalized in item["arxiv_id"].replace("/", ""):
            return {**extracted, **item, "metadata_source": "curated_seed_and_latex"}
    return {
        "arxiv_id": source_id,
        "title": extracted.get("title") or source_id,
        "authors": extracted.get("authors") or [],
        "year": extracted.get("year"),
        "date": extracted.get("date"),
        "url": extracted.get("url") or f"https://arxiv.org/abs/{source_id}",
        "stance": "unknown",
        "role": "unclassified_source",
        "metadata_source": extracted.get("metadata_source") or "source_identifier",
    }


def author_node_id(name: str) -> str:
    digest = hashlib.sha1(name.encode("utf-8", errors="replace")).hexdigest()[:12]
    return f"A:{digest}"


def build(args: argparse.Namespace) -> Dict[str, Any]:
    papers_dirs = [Path(args.papers_dir)] + [Path(path) for path in (args.additional_papers_dir or [])]
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    seeds = load_seed_papers(Path(args.seed_papers))

    sources = []
    provenance_nodes = []
    provenance_edges = []
    witnesses = []
    claim_nodes = []
    source_citations: Dict[str, List[str]] = {}
    author_nodes: Dict[str, Dict[str, Any]] = {}

    documents_by_source = {}
    for papers_dir in papers_dirs:
        for document in iter_documents(papers_dir):
            # Later directories are explicit overlays; full primary-source
            # packages can replace abstract-scale HF rows with the same id.
            documents_by_source[document.source_id] = document

    for doc in sorted(documents_by_source.values(), key=lambda item: item.source_id):
        meta = source_metadata(doc.source_id, seeds, doc.metadata)
        source_citations[doc.source_id] = list(doc.cited_arxiv_ids)
        sources.append({"source_id": doc.source_id, "path": doc.path, "metadata": meta})
        provenance_nodes.append({
            "id": doc.source_id,
            "source_id": doc.source_id,
            "node_type": "paper",
            "title": meta.get("title"),
            "authors": meta.get("authors", []),
            "year": meta.get("year"),
            "stance": meta.get("stance", "unknown"),
            "role": meta.get("role", "unknown"),
            "url": meta.get("url"),
            "metadata_source": meta.get("metadata_source"),
        })
        for author in meta.get("authors") or []:
            name = str(author).strip()
            if not name:
                continue
            aid = author_node_id(name)
            author_nodes.setdefault(aid, {"id": aid, "node_type": "author", "name": name})
            provenance_edges.append({
                "source": aid,
                "target": doc.source_id,
                "edge_type": "author_wrote_paper",
            })
        for claim in extract_claims(doc.text):
            claim_id = f"C{len(claim_nodes):05d}"
            claim_nodes.append({"id": claim_id, "node_type": "claim", "source_id": doc.source_id, **claim})
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
                "witness_id": f"W{len(witnesses):06d}",
                "source_id": doc.source_id,
                "source_title": meta.get("title"),
                "source_stance": meta.get("stance"),
                "source_role": meta.get("role"),
                "source_url": meta.get("url"),
                "path": doc.path,
                "source_equation_ordinal": int(eq.get("ordinal", i)),
                "source_start": int(eq["start"]),
                "source_end": int(eq["end"]),
                "formula": eq["formula"],
                "kind": eq["kind"],
                "context": context,
                "role_scores": scores,
                "dominant_role": role,
                "fingerprint": fp,
            })

    selected_source_ids = {str(source["source_id"]) for source in sources}
    reference_nodes: Dict[str, Dict[str, Any]] = {}
    for source_id, citations in source_citations.items():
        for cited_id in citations:
            if cited_id == source_id:
                continue
            if cited_id not in selected_source_ids:
                reference_nodes.setdefault(cited_id, {
                    "id": cited_id,
                    "source_id": cited_id,
                    "node_type": "external_reference",
                    "title": cited_id,
                    "url": f"https://arxiv.org/abs/{cited_id}",
                })
            provenance_edges.append({
                "source": source_id,
                "target": cited_id,
                "edge_type": "paper_cites_paper",
            })

    provenance = {
        "nodes": provenance_nodes + list(author_nodes.values()) + list(reference_nodes.values()) + claim_nodes,
        "edges": provenance_edges,
        "node_type_counts": {
            "paper": len(provenance_nodes),
            "author": len(author_nodes),
            "external_reference": len(reference_nodes),
            "claim": len(claim_nodes),
        },
        "edge_type_counts": {
            edge_type: sum(1 for edge in provenance_edges if edge["edge_type"] == edge_type)
            for edge_type in sorted({edge["edge_type"] for edge in provenance_edges})
        },
        "graph_role": "Source, authorship, citation and claim provenance for the same papers used by the equation graph.",
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
        "papers_dir": str(papers_dirs[0]),
        "papers_dirs": [str(path) for path in papers_dirs],
        "source_overlay_count": max(0, sum(1 for path in papers_dirs[1:])),
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
    parser.add_argument(
        "--additional-papers-dir",
        action="append",
        default=[],
        help="Additional source directory; later directories replace duplicate source ids.",
    )
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
