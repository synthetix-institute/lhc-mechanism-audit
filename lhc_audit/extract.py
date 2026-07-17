from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


TEXT_EXTENSIONS = {".tex", ".txt", ".md", ".latex"}
PDF_EXTENSIONS = {".pdf"}

BEGIN_DOCUMENT_RE = re.compile(r"\\begin\s*\{\s*document\s*\}", re.I)
END_DOCUMENT_RE = re.compile(r"\\end\s*\{\s*document\s*\}", re.I)
BIBLIOGRAPHY_START_RE = re.compile(
    r"\\begin\s*\{\s*(?:thebibliography|references)\s*\}"
    r"|\\bibliography\s*\{"
    r"|\\printbibliography\b"
    r"|^\s*(?:references|bibliography)\s*$",
    re.I | re.M,
)
DROP_ENV_RE = re.compile(
    r"\\begin\s*\{\s*(?:figure|table|tabular|picture|tikzpicture|thebibliography)\s*\}"
    r".*?"
    r"\\end\s*\{\s*(?:figure|table|tabular|picture|tikzpicture|thebibliography)\s*\}",
    re.I | re.S,
)
MACRO_DEFINITION_LINE_RE = re.compile(
    r"^\s*\\(?:def|newcommand|renewcommand|providecommand|DeclareMathOperator|"
    r"DeclareRobustCommand|let)\b",
    re.I,
)
INLINE_DEF_RE = re.compile(
    r"\\(?:def|newcommand|renewcommand|providecommand)\b\s*\\?[A-Za-z@]+"
    r"(?:\s*\[[^\]]*\]){0,2}\s*\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}",
    re.I | re.S,
)


@dataclass
class SourceDocument:
    source_id: str
    path: str
    text: str
    metadata: Dict[str, Any]
    cited_arxiv_ids: List[str]


DISPLAY_ENV_PATTERN = re.compile(
    r"\\begin\{(?P<env>equation\*?|align\*?|alignat\*?|gather\*?|multline\*?|"
    r"eqnarray\*?|displaymath)\}(?P<body>.*?)\\end\{(?P=env)\}",
    re.S,
)
DISPLAY_PATTERNS = [
    ("display", re.compile(r"\\\[(.*?)\\\]", re.S), 1),
    ("system", DISPLAY_ENV_PATTERN, "body"),
    ("display", re.compile(r"\$\$(.*?)\$\$", re.S), 1),
]
INLINE_PATTERN = re.compile(
    r"\$([^$]{6,500}?(?:=|<|>|\\leq?|\\geq?|\\ll|\\gg|\\sim|\\simeq|"
    r"\\approx|\\propto|\\to|\\rightarrow|\\mapsto)[^$]{0,500}?)\$",
    re.S,
)
ARXIV_ID_RE = re.compile(r"(?:arXiv\s*:\s*)?(\d{4}\.\d{4,5}|[a-z-]+/\d{7})", re.I)
DISPLAY_ALIAS_RE = re.compile(
    r"\\(?:def\s*)?(?P<macro>\\[A-Za-z@]+)\s*(?:#\d\s*)*\{\s*"
    r"\\(?P<action>begin|end)\s*\{\s*(?P<env>equation\*?|align\*?|alignat\*?|"
    r"gather\*?|multline\*?|eqnarray\*?|displaymath)\s*\}\s*\}",
    re.I,
)
NEWCOMMAND_DISPLAY_ALIAS_RE = re.compile(
    r"\\(?:newcommand|renewcommand|providecommand)\s*\{(?P<macro>\\[A-Za-z@]+)\}"
    r"(?:\s*\[[^\]]*\]){0,2}\s*\{\s*\\(?P<action>begin|end)\s*"
    r"\{\s*(?P<env>equation\*?|align\*?|alignat\*?|gather\*?|multline\*?|"
    r"eqnarray\*?|displaymath)\s*\}\s*\}",
    re.I,
)


def source_id_from_path(path: Path) -> str:
    stem = path.stem
    match = re.search(r"(\d{4}\.\d{4,5}|[a-z-]+/\d{7})", stem)
    if match:
        return match.group(1)
    match = re.search(r"([a-z-]+)[_/](\d{7})", stem)
    if match:
        return f"{match.group(1)}/{match.group(2)}"
    match = re.search(r"([a-z-]+)(\d{7})", stem)
    if match:
        return f"{match.group(1)}/{match.group(2)}"
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


def normalize_arxiv_id(value: str) -> str:
    value = str(value or "").strip().replace("arXiv:", "")
    return re.sub(r"v\d+$", "", value, flags=re.I)


def _balanced_argument(text: str, start: int) -> Tuple[str, int]:
    depth = 0
    escaped = False
    for index in range(start, len(text)):
        char = text[index]
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start + 1:index], index + 1
    return "", start


def command_arguments(text: str, command: str, limit: int = 24) -> List[str]:
    pattern = re.compile(rf"\\{re.escape(command)}\s*(?:\[[^\]]*\]\s*)*\{{", re.I)
    values: List[str] = []
    for match in pattern.finditer(text):
        value, _ = _balanced_argument(text, match.end() - 1)
        if value.strip():
            values.append(value.strip())
        if len(values) >= limit:
            break
    return values


def plain_metadata_text(value: str) -> str:
    value = re.sub(r"%.*", "", value)
    value = re.sub(r"\\(?:thanks|affiliation|address|email)\s*\{.*?\}", " ", value, flags=re.I | re.S)
    value = re.sub(r"\\[A-Za-z@]+\*?(?:\[[^\]]*\])?", " ", value)
    value = value.replace("{", "").replace("}", "")
    return re.sub(r"\s+", " ", value).strip()


def extract_document_metadata(text: str, source_id: str) -> Dict[str, Any]:
    header = re.sub(r"(?m)(?<!\\)%.*$", "", text[:200000])
    titles = command_arguments(header, "title", limit=4)
    authors = command_arguments(header, "author", limit=40)
    dates = command_arguments(header, "date", limit=2)
    normalized = normalize_arxiv_id(source_id)
    year = None
    new_style = re.match(r"(\d{2})\d{2}\.\d+", normalized)
    if new_style:
        yy = int(new_style.group(1))
        year = 2000 + yy if yy < 90 else 1900 + yy
    return {
        "arxiv_id": normalized,
        "title": plain_metadata_text(titles[0]) if titles else normalized,
        "authors": [plain_metadata_text(author) for author in authors if plain_metadata_text(author)],
        "date": plain_metadata_text(dates[0]) if dates else None,
        "year": year,
        "url": f"https://arxiv.org/abs/{normalized}" if normalized else None,
        "metadata_source": "latex_source",
    }


def extract_cited_arxiv_ids(text: str) -> List[str]:
    seen: set[str] = set()
    values: List[str] = []
    for match in ARXIV_ID_RE.finditer(text):
        value = normalize_arxiv_id(match.group(1))
        if value and value not in seen:
            seen.add(value)
            values.append(value)
    return values


def extract_display_aliases(text: str) -> Dict[str, str]:
    aliases: Dict[str, str] = {}
    for pattern in (DISPLAY_ALIAS_RE, NEWCOMMAND_DISPLAY_ALIAS_RE):
        for match in pattern.finditer(text[:250000]):
            macro = match.group("macro")
            action = match.group("action").lower()
            env = match.group("env")
            aliases[macro] = f"\\{action}{{{env}}}"
    return aliases


def expand_display_aliases(text: str, aliases: Dict[str, str]) -> str:
    for macro in sorted(aliases, key=len, reverse=True):
        text = re.sub(re.escape(macro) + r"(?![A-Za-z@])", lambda _: aliases[macro], text)
    return text


def read_document(path: Path) -> SourceDocument:
    suffix = path.suffix.lower()
    if suffix in TEXT_EXTENSIONS:
        raw_text = path.read_text(encoding="utf-8", errors="replace")
    elif suffix in PDF_EXTENSIONS:
        raw_text = read_pdf_text(path)
    else:
        raise ValueError(f"Unsupported file type: {path}")
    source_id = source_id_from_path(path)
    metadata = extract_document_metadata(raw_text, source_id)
    citations = [item for item in extract_cited_arxiv_ids(raw_text) if item != normalize_arxiv_id(source_id)]
    aliases = extract_display_aliases(raw_text)
    text = expand_display_aliases(sanitize_latex_source(raw_text), aliases)
    return SourceDocument(
        source_id=source_id,
        path=str(path),
        text=text,
        metadata=metadata,
        cited_arxiv_ids=citations,
    )


def iter_documents(folder: Path) -> Iterable[SourceDocument]:
    for path in sorted(folder.rglob("*")):
        if path.is_file() and path.suffix.lower() in (TEXT_EXTENSIONS | PDF_EXTENSIONS):
            yield read_document(path)


def sanitize_latex_source(text: str) -> str:
    """Keep scientific body text and remove TeX infrastructure.

    The constructor layer needs equations from the paper body.  arXiv source
    preambles contain macro definitions that look like equations to a regex
    extractor, so they must be removed before display/inline math extraction.
    """
    if not text:
        return ""

    begin = BEGIN_DOCUMENT_RE.search(text)
    if begin:
        text = text[begin.end():]

    end = END_DOCUMENT_RE.search(text)
    if end:
        text = text[:end.start()]

    bibliography = BIBLIOGRAPHY_START_RE.search(text)
    if bibliography:
        text = text[:bibliography.start()]

    text = DROP_ENV_RE.sub("\n", text)
    text = INLINE_DEF_RE.sub(" ", text)

    kept_lines: List[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            kept_lines.append("")
            continue
        if MACRO_DEFINITION_LINE_RE.match(stripped):
            continue
        kept_lines.append(line)
    return "\n".join(kept_lines)


def clean_formula(formula: str) -> str:
    formula = re.sub(r"%.*", "", formula)
    formula = re.sub(r"\\label\{[^}]*\}|\\tag\{[^}]*\}", "", formula)
    formula = re.sub(r"\s+", " ", formula).strip()
    return formula


def extract_equations(text: str) -> List[dict]:
    out: List[dict] = []
    display_intervals: List[Tuple[int, int]] = []
    for kind, pattern, group in DISPLAY_PATTERNS:
        for match in pattern.finditer(text):
            formula = clean_formula(match.group(group))
            if len(formula) >= 6:
                out.append({"formula": formula, "start": match.start(), "end": match.end(), "kind": kind})
                display_intervals.append((match.start(), match.end()))
    for match in INLINE_PATTERN.finditer(text):
        if any(start <= match.start() < end for start, end in display_intervals):
            continue
        formula = clean_formula(match.group(1))
        if len(formula) >= 8 and "\\begin{" not in formula and "\\end{" not in formula:
            out.append({"formula": formula, "start": match.start(), "end": match.end(), "kind": "inline"})
    out.sort(key=lambda x: (x["start"], x["end"]))
    for ordinal, equation in enumerate(out):
        equation["ordinal"] = ordinal
    return out


def local_context(text: str, start: int, end: int, window: int = 700) -> str:
    left = max(0, start - window)
    right = min(len(text), end + window)
    return re.sub(r"\s+", " ", text[left:right]).strip()
