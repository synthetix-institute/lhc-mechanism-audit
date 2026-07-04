#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
import io
import json
import re
import tarfile
import time
import urllib.error
import urllib.request
from pathlib import Path, PurePosixPath
from typing import Any, Dict, Iterable, List, Tuple


TEXT_SUFFIXES = {".tex", ".ltx", ".bbl", ".bib", ".sty", ".cls"}


def normalize_arxiv_id(value: str) -> str:
    value = value.strip().replace("arXiv:", "")
    value = re.sub(r"\s+v\d+$", "", value)
    value = value.split()[0] if value.split() else ""
    value = value.strip("/")
    old_style = re.fullmatch(r"([a-z-]+)(\d{7})(?:v\d+)?", value)
    if old_style:
        return f"{old_style.group(1)}/{old_style.group(2)}"
    return value


def safe_name(arxiv_id: str) -> str:
    return normalize_arxiv_id(arxiv_id).replace("/", "_")


def load_seed_ids(path: Path) -> List[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return [normalize_arxiv_id(str(row["arxiv_id"])) for row in data]


def load_manifest_ids(path: Path, limit: int = 0) -> List[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    out: List[str] = []
    for row in data.get("records", []):
        paper_id = normalize_arxiv_id(str(row.get("paper_id") or ""))
        if paper_id:
            out.append(paper_id)
        if limit and len(out) >= limit:
            break
    return out


def unique_ids(ids: Iterable[str]) -> List[str]:
    seen: set[str] = set()
    out: List[str] = []
    for item in ids:
        value = normalize_arxiv_id(item)
        if value and value not in seen:
            out.append(value)
            seen.add(value)
    return out


def download_source(arxiv_id: str, raw_dir: Path, *, force: bool = False, timeout: int = 90) -> Path:
    raw_dir.mkdir(parents=True, exist_ok=True)
    raw_path = raw_dir / f"{safe_name(arxiv_id)}.src"
    if raw_path.exists() and raw_path.stat().st_size > 0 and not force:
        return raw_path
    url = f"https://arxiv.org/e-print/{arxiv_id}"
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "lhc-mechanism-audit/1.0 (constructor-layer source export)",
            "Accept": "application/octet-stream,*/*",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw_path.write_bytes(response.read())
    return raw_path


def safe_member_name(name: str) -> str:
    path = PurePosixPath(name)
    parts = [part for part in path.parts if part not in {"", ".", ".."}]
    return "/".join(parts)


def decode_bytes(data: bytes) -> str:
    for encoding in ("utf-8", "latin-1"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def extract_text_files(raw_path: Path) -> List[Tuple[str, str]]:
    data = raw_path.read_bytes()
    files: List[Tuple[str, str]] = []

    for mode in ("r:*",):
        try:
            with tarfile.open(fileobj=io.BytesIO(data), mode=mode) as tar:
                for member in tar.getmembers():
                    if not member.isfile():
                        continue
                    name = safe_member_name(member.name)
                    suffix = Path(name).suffix.lower()
                    if suffix not in TEXT_SUFFIXES:
                        continue
                    extracted = tar.extractfile(member)
                    if not extracted:
                        continue
                    files.append((name, decode_bytes(extracted.read())))
                if files:
                    return files
        except tarfile.TarError:
            pass

    try:
        text = decode_bytes(gzip.decompress(data))
        return [(raw_path.with_suffix(".tex").name, text)]
    except Exception:
        pass

    return [(raw_path.with_suffix(".tex").name, decode_bytes(data))]


def combine_sources(arxiv_id: str, files: List[Tuple[str, str]]) -> str:
    def rank(item: Tuple[str, str]) -> Tuple[int, str]:
        name, text = item
        lname = name.lower()
        main_score = 0
        if "\\begin{document}" in text:
            main_score -= 10
        if re.search(r"(?:^|/)(main|paper|ms|article|source)\.te?x$", lname):
            main_score -= 4
        if Path(lname).suffix.lower() not in {".tex", ".ltx"}:
            main_score += 5
        return (main_score, lname)

    chunks = [
        f"% arXiv:{arxiv_id}\n",
        f"% Combined source package for constructor-layer export.\n",
    ]
    for name, text in sorted(files, key=rank):
        chunks.append(f"\n\n% ===== SOURCE FILE: {name} =====\n")
        chunks.append(text)
    return "".join(chunks)


def build(args: argparse.Namespace) -> Dict[str, Any]:
    out_dir = Path(args.out_dir)
    raw_dir = out_dir / "raw"
    source_dir = out_dir / "sources"
    source_dir.mkdir(parents=True, exist_ok=True)

    ids: List[str] = []
    if args.seed_papers:
        ids.extend(load_seed_ids(Path(args.seed_papers)))
    if args.manifest:
        ids.extend(load_manifest_ids(Path(args.manifest), limit=args.manifest_limit))
    if args.ids:
        ids.extend([value for chunk in args.ids for value in chunk.split(",")])
    ids = unique_ids(ids)
    if args.limit:
        ids = ids[: args.limit]

    records: List[Dict[str, Any]] = []
    for index, arxiv_id in enumerate(ids, start=1):
        record: Dict[str, Any] = {"arxiv_id": arxiv_id, "status": "pending"}
        try:
            raw_path = download_source(arxiv_id, raw_dir, force=args.force, timeout=args.timeout)
            files = extract_text_files(raw_path)
            combined = combine_sources(arxiv_id, files)
            out_path = source_dir / f"{safe_name(arxiv_id)}.tex"
            out_path.write_text(combined, encoding="utf-8", errors="replace")
            record.update({
                "status": "downloaded",
                "raw": str(raw_path),
                "source": str(out_path),
                "file_count": len(files),
                "bytes": out_path.stat().st_size,
                "has_begin_document": bool(re.search(r"\\begin\{document\}", combined)),
                "display_equation_markers": len(re.findall(r"\\begin\{(?:equation|align|gather|multline)|\\\[|\$\$", combined)),
            })
        except urllib.error.HTTPError as exc:
            record.update({"status": "http_error", "error": f"{exc.code} {exc.reason}"})
        except Exception as exc:
            record.update({"status": "error", "error": str(exc)})
        records.append(record)
        print(json.dumps(record, ensure_ascii=False), flush=True)
        if args.sleep and index < len(ids):
            time.sleep(args.sleep)

    manifest = {
        "report_type": "arxiv_full_source_download",
        "readiness": "usable" if any(row["status"] == "downloaded" for row in records) else "no_sources_downloaded",
        "out_dir": str(out_dir),
        "source_dir": str(source_dir),
        "raw_dir": str(raw_dir),
        "requested": len(ids),
        "downloaded": sum(1 for row in records if row["status"] == "downloaded"),
        "records": records,
    }
    (out_dir / "download_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return manifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Download full arXiv source packages for constructor-layer export.")
    parser.add_argument("--out-dir", default="data/arxiv_lhc_full_sources")
    parser.add_argument("--seed-papers", default="data/seed_papers.json")
    parser.add_argument("--manifest", default="")
    parser.add_argument("--manifest-limit", type=int, default=0)
    parser.add_argument("--ids", action="append", default=[])
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--timeout", type=int, default=90)
    parser.add_argument("--sleep", type=float, default=3.0)
    parser.add_argument("--force", action="store_true")
    return parser


def main() -> None:
    print(json.dumps(build(build_parser().parse_args()), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
