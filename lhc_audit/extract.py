from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List


TEXT_EXTENSIONS = {".tex", ".txt", ".md", ".latex"}
PDF_EXTENSIONS = {".pdf"}


@dataclass
class SourceDocument:
    source_id: str
    path: str
    text: str


DISPLAY_PATTERNS = [
    re.compile(r"\\\[(.*?)\\\]", re.S),
    re.compile(r"\\begin\{equation\*?\}(.*?)\\end\{equation\*?\}", re.S),
    re.compile(r"\\begin\{align\*?\}(.*?)\\end\{align\*?\}", re.S),
    re.compile(r"\$\$(.*?)\$\$", re.S),
]
INLINE_PATTERN = re.compile(r"\$(.{8,240}?[=<>\\][^$]{0,240}?)\$", re.S)


def source_id_from_path(path: Path) -> str:
    stem = path.stem
    match = re.search(r"(\d{4}\.\d{4,5}|[a-z-]+/\d{7})", stem)
    if match:
        return match.group(1).replace("/", "")
    return stem


def read_pdf_text(path: Path) -> str:
    try:
        from pypdf import PdfReader  # type: ignore

        reader = PdfReader(str(path))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception:
        pass
    try:
        result = subprocess.run(
            ["pdftotext", str(path), "-"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return result.stdout
    except Exception as exc:
        raise RuntimeError(f"Could not extract text from PDF {path}: {exc}") from exc


def read_document(path: Path) -> SourceDocument:
    suffix = path.suffix.lower()
    if suffix in TEXT_EXTENSIONS:
        text = path.read_text(encoding="utf-8", errors="replace")
    elif suffix in PDF_EXTENSIONS:
        text = read_pdf_text(path)
    else:
        raise ValueError(f"Unsupported file type: {path}")
    return SourceDocument(source_id=source_id_from_path(path), path=str(path), text=text)


def iter_documents(folder: Path) -> Iterable[SourceDocument]:
    for path in sorted(folder.rglob("*")):
        if path.is_file() and path.suffix.lower() in (TEXT_EXTENSIONS | PDF_EXTENSIONS):
            yield read_document(path)


def clean_formula(formula: str) -> str:
    formula = re.sub(r"%.*", "", formula)
    formula = re.sub(r"\\label\{[^}]*\}|\\tag\{[^}]*\}", "", formula)
    formula = re.sub(r"\s+", " ", formula).strip()
    return formula


def extract_equations(text: str) -> List[dict]:
    out: List[dict] = []
    for pattern in DISPLAY_PATTERNS:
        for match in pattern.finditer(text):
            formula = clean_formula(match.group(1))
            if len(formula) >= 6:
                out.append({"formula": formula, "start": match.start(), "end": match.end(), "kind": "display"})
    for match in INLINE_PATTERN.finditer(text):
        formula = clean_formula(match.group(1))
        if len(formula) >= 8:
            out.append({"formula": formula, "start": match.start(), "end": match.end(), "kind": "inline"})
    out.sort(key=lambda x: (x["start"], x["end"]))
    return out


def local_context(text: str, start: int, end: int, window: int = 700) -> str:
    left = max(0, start - window)
    right = min(len(text), end + window)
    return re.sub(r"\s+", " ", text[left:right]).strip()
