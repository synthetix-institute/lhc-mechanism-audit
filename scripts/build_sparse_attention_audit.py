#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from lhc_audit.sparse_attention import build_graph_sparse_attention


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def render_markdown(result: Dict[str, Any]) -> str:
    lines: List[str] = [
        "# Equation-Graph Sparse Attention",
        "",
        result["method"],
        "",
        f"Strict equation receipts: `{result['strict_receipt_node_count']}`; "
        f"connected attended edges: `{result['attended_edge_count']}`.",
        "",
        "## Highest-attention equation transitions",
        "",
    ]
    for edge in result["top_edges"][:20]:
        lines.append(
            f"- `{edge['source_paper']}` `{edge['source']}` -> `{edge['target_paper']}` "
            f"`{edge['target']}`: attention `{edge['attention']:.4f}`; "
            f"shared `{', '.join(edge['shared_routes']) or 'none'}`; "
            f"introduced `{', '.join(edge['introduced_routes']) or 'none'}`."
        )
    lines += ["", "## Highest-attention equations", ""]
    for node in result["top_nodes"][:20]:
        lines.append(
            f"- `{node['source_id']}` / `{node['node_id']}`: `{node['attention']:.4f}`; "
            f"{node['formula']}"
        )
    lines += ["", "## Route prevalence", ""]
    for route, count in result["strict_receipt_route_prevalence"].items():
        lines.append(f"- `{route}`: `{count}` strict receipt nodes")
    return "\n".join(lines).rstrip() + "\n"


def build(args: argparse.Namespace) -> Dict[str, Any]:
    out_dir = Path(args.out_dir)
    graph_path = out_dir / "equation_mechanism_graph.json"
    if not graph_path.exists():
        raise FileNotFoundError(f"Missing {graph_path}. Build the equation mechanism graph first.")
    result = build_graph_sparse_attention(read_json(graph_path), top_k=args.top_k)
    json_path = out_dir / "sparse_attention_audit.json"
    md_path = out_dir / "sparse_attention_audit.md"
    json_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(render_markdown(result), encoding="utf-8")
    return {"json": str(json_path), "markdown": str(md_path), "readiness": result["readiness"]}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Compute hub-corrected sparse attention on equation-graph edges.")
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--top-k", type=int, default=40)
    return parser


def main() -> None:
    print(json.dumps(build(build_parser().parse_args()), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
