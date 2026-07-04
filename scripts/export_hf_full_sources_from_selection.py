#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


ARXIV_ID_RE = re.compile(r"(\d{4}\.\d{4,5}|[a-z-]+/\d{7}|[a-z-]+\d{7})")
TEXT_FIELDS = (
    "latex",
    "source",
    "tex",
    "text",
    "content",
    "body",
    "article",
    "full_text",
    "abstract",
)


def normalize_arxiv_id(value: str) -> str:
    value = str(value or "").strip().replace("arXiv:", "")
    value = re.sub(r"\s+v\d+$", "", value)
    value = value.split()[0] if value.split() else ""
    value = value.strip("/")
    old_style = re.fullmatch(r"([a-z-]+)(\d{7})(?:v\d+)?", value)
    if old_style:
        return f"{old_style.group(1)}/{old_style.group(2)}"
    return value


def safe_name(arxiv_id: str) -> str:
    return normalize_arxiv_id(arxiv_id).replace("/", "_")


def row_ids(row: Dict[str, Any]) -> List[str]:
    ids: List[str] = []
    for key in ("arxiv_id", "id", "paper_id", "external_id"):
        value = row.get(key)
        if value:
            ids.append(normalize_arxiv_id(str(value)))
    for key in ("title", "abstract"):
        value = row.get(key)
        if isinstance(value, str):
            ids.extend(normalize_arxiv_id(match.group(1)) for match in ARXIV_ID_RE.finditer(value))
    out: List[str] = []
    seen: set[str] = set()
    for item in ids:
        if item and item not in seen:
            out.append(item)
            seen.add(item)
    return out


def equation_marker_count(text: str) -> int:
    return len(re.findall(r"\\begin\{(?:equation|align|gather|multline)|\\\[|\$\$|\\frac|\\sum|\\int|=", text))


def text_score(text: str) -> Tuple[int, int, int]:
    has_document = int("\\begin{document}" in text)
    markers = equation_marker_count(text)
    sections = len(re.findall(r"\\(?:section|subsection|chapter)\*?\{", text))
    return (has_document, markers + sections, len(text))


def best_text(row: Dict[str, Any]) -> Tuple[str, str]:
    candidates: List[Tuple[Tuple[int, int, int], str, str]] = []
    for key in TEXT_FIELDS:
        value = row.get(key)
        if isinstance(value, str) and value.strip():
            candidates.append((text_score(value), key, value))
    if not candidates:
        return "", ""
    _, key, value = max(candidates, key=lambda item: item[0])
    title = row.get("title")
    if isinstance(title, str) and title.strip() and title.strip() not in value[:1000]:
        value = title.strip() + "\n" + value
    return key, value


def load_selection(path: Path) -> Tuple[set[str], set[int]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    ids: set[str] = set()
    row_indices: set[int] = set()
    for row in data.get("records", []):
        paper_id = row.get("paper_id")
        if paper_id:
            ids.add(normalize_arxiv_id(str(paper_id)))
        row_index = row.get("row_index")
        if isinstance(row_index, int):
            row_indices.add(row_index)
    return ids, row_indices


def iter_hf_rows(dataset: str, split: str) -> Iterable[Dict[str, Any]]:
    try:
        from datasets import load_dataset  # type: ignore
    except Exception as exc:
        raise RuntimeError("Install `datasets` to stream Hugging Face rows.") from exc
    ds = load_dataset(dataset, split=split, streaming=True)
    for row in ds:
        yield dict(row)


def write_source(source_dir: Path, arxiv_id: str, row_index: int, field: str, text: str) -> Path:
    source_dir.mkdir(parents=True, exist_ok=True)
    path = source_dir / f"{safe_name(arxiv_id)}.tex"
    header = (
        f"% arXiv:{arxiv_id}\n"
        f"% HF row_index:{row_index}\n"
        f"% HF text_field:{field}\n"
        "% Exported for mechanism-constructor analysis.\n\n"
    )
    path.write_text(header + text, encoding="utf-8", errors="replace")
    return path


def export(args: argparse.Namespace) -> Dict[str, Any]:
    selection_ids, selection_indices = load_selection(Path(args.selection_manifest))
    out_dir = Path(args.out_dir)
    source_dir = out_dir / "sources"
    source_dir.mkdir(parents=True, exist_ok=True)

    best: Dict[str, Dict[str, Any]] = {}
    scanned = 0
    matched_rows = 0

    print(
        f"[hf-full-export] dataset={args.dataset} split={args.split} "
        f"targets={len(selection_ids)} index_targets={len(selection_indices)}",
        file=sys.stderr,
        flush=True,
    )

    for row_index, row in enumerate(iter_hf_rows(args.dataset, args.split)):
        scanned += 1
        ids = row_ids(row)
        matched_ids = [paper_id for paper_id in ids if paper_id in selection_ids]
        matched_by_index = row_index in selection_indices
        if matched_ids or matched_by_index:
            field, text = best_text(row)
            if text:
                if not matched_ids and ids:
                    matched_ids = [ids[0]]
                elif not matched_ids:
                    matched_ids = [f"row_{row_index:09d}"]
                for paper_id in matched_ids:
                    current = best.get(paper_id)
                    if current is None or text_score(text) > text_score(current["text"]):
                        best[paper_id] = {
                            "paper_id": paper_id,
                            "row_index": row_index,
                            "matched_by_id": paper_id in selection_ids,
                            "matched_by_index": matched_by_index,
                            "field": field,
                            "text": text,
                        }
                matched_rows += 1
                print(
                    f"[hf-full-export] matched row={row_index} ids={matched_ids} "
                    f"bytes={len(text)} markers={equation_marker_count(text)} field={field}",
                    file=sys.stderr,
                    flush=True,
                )
        if args.progress_every and scanned % args.progress_every == 0:
            print(
                f"[hf-full-export] progress scanned={scanned} matched_rows={matched_rows} exported_candidates={len(best)}",
                file=sys.stderr,
                flush=True,
            )
        if args.max_docs and scanned >= args.max_docs:
            break
        if args.stop_when_found and selection_ids.issubset(best.keys()):
            break

    records: List[Dict[str, Any]] = []
    for paper_id, item in sorted(best.items()):
        text = item.pop("text")
        path = write_source(source_dir, paper_id, item["row_index"], item["field"], text)
        byte_count = path.stat().st_size
        markers = equation_marker_count(text)
        records.append({
            **item,
            "source": str(path),
            "bytes": byte_count,
            "has_begin_document": "\\begin{document}" in text,
            "equation_markers": markers,
            "full_body_candidate": byte_count >= args.min_full_body_bytes and markers >= args.min_equation_markers,
        })

    exported_ids = {row["paper_id"] for row in records}
    missing_ids = sorted(selection_ids - exported_ids)
    full_body_count = sum(1 for row in records if row["full_body_candidate"])

    manifest = {
        "report_type": "hf_full_source_export_from_selection",
        "readiness": "usable" if full_body_count else "no_full_body_candidates",
        "dataset": args.dataset,
        "split": args.split,
        "selection_manifest": args.selection_manifest,
        "out_dir": str(out_dir),
        "source_dir": str(source_dir),
        "selected_ids": len(selection_ids),
        "selected_row_indices": len(selection_indices),
        "scanned_rows": scanned,
        "matched_stream_rows": matched_rows,
        "exported_sources": len(records),
        "full_body_candidates": full_body_count,
        "abstract_scale_sources": sum(1 for row in records if not row["full_body_candidate"]),
        "missing_ids": missing_ids[:200],
        "missing_id_count": len(missing_ids),
        "records": records,
    }
    (out_dir / "full_source_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return manifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Export full HF LaTeX sources for an existing LHC selection manifest.")
    parser.add_argument("--dataset", default="synthetix-institute/latex-data")
    parser.add_argument("--split", default="train")
    parser.add_argument("--selection-manifest", default="data/hf_lhc_selection_500k/selection_manifest.json")
    parser.add_argument("--out-dir", default="data/hf_lhc_full_selection_500k")
    parser.add_argument("--max-docs", type=int, default=0)
    parser.add_argument("--progress-every", type=int, default=10000)
    parser.add_argument("--min-full-body-bytes", type=int, default=10000)
    parser.add_argument("--min-equation-markers", type=int, default=10)
    parser.add_argument("--stop-when-found", action="store_true")
    return parser


def main() -> None:
    print(json.dumps(export(build_parser().parse_args()), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
