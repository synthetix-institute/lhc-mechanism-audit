from __future__ import annotations

import json
import re
from collections import Counter, defaultdict, deque
from pathlib import Path
from typing import Any, Deque, Dict, Iterable, List, Tuple

from lhc_audit.equation_mechanism import case_evidence
from lhc_audit.extract import extract_equations, iter_documents, source_id_from_path
from lhc_audit.physical_constructor import SLOT_DEFINITIONS, evidence_grade, slot_match


SECTION_RE = re.compile(
    r"\\(?P<level>section|subsection|subsubsection|paragraph)\*?\{(?P<title>[^{}]{1,180})\}",
    re.DOTALL,
)

KNOWN_VARIABLES: List[Tuple[str, str, str]] = [
    (r"\\hat\s*\{?s\}?", r"\hat{s}", "parton-level squared centre-of-mass energy"),
    (r"\bs\b", "s", "proton-proton squared centre-of-mass energy or generic invariant"),
    (r"x_?\{?1\}?|x_?\{?2\}?", "x_1,x_2", "parton momentum fractions"),
    (r"M_\{?\\?min\}?|M_\{?min\}?", r"M_{\min}", "minimum mass threshold for production"),
    (r"M_\{?D\}?|M_D", r"M_D", "fundamental gravity scale in extra-dimensional models"),
    (r"M_\{?\\ast\}?|M_\\ast", r"M_\ast", "fundamental high-energy scale"),
    (r"M_\{?BH\}?|M_\{?\\rm\s*BH\}?|M_{bh}|M_\{?bh\}?", r"M_{\rm BH}", "black-hole mass"),
    (r"M_\{?WD\}?|M_\{?\\rm\s*WD\}?", r"M_{\rm WD}", "white-dwarf mass"),
    (r"M_\{?NS\}?|M_\{?\\rm\s*NS\}?", r"M_{\rm NS}", "neutron-star mass"),
    (r"R_\{?S\}?|R_S|r_\{?s\}?|r_s", r"R_S", "Schwarzschild or horizon radius"),
    (r"T_\{?BH\}?|T_\{?\\rm\s*BH\}?", r"T_{\rm BH}", "black-hole temperature"),
    (r"\\Gamma_?\{?D\}?|Gamma_?\{?D\}?", r"\Gamma_D", "decay or evaporation rate"),
    (r"\\Gamma_?\{?A\}?|Gamma_?\{?A\}?", r"\Gamma_A", "accretion rate"),
    (r"\\rho|rho", r"\rho", "density of matter or medium"),
    (r"\\sigma|sigma", r"\sigma", "cross-section or dispersion depending on context"),
    (r"\\sigma_\{?cap\}?|sigma_\{?cap\}?", r"\sigma_{\rm cap}", "capture cross-section"),
    (r"\\dot\{?M\}?|dM\s*/\s*dt|dM\s*\\over\s*dt", r"\dot M", "mass-change rate"),
    (r"P_\{?evap\}?|P_\{?\\rm\s*evap\}?", r"P_{\rm evap}", "evaporation power"),
    (r"\\tau|tau", r"\tau", "lifetime or characteristic time"),
    (r"t_\{?grow\}?|t_\{?\\rm\s*grow\}?", r"t_{\rm grow}", "growth time"),
    (r"\bv\b", "v", "velocity through matter"),
    (r"L_\{?Edd\}?|L_\{?\\rm\s*Edd\}?", r"L_{\rm Edd}", "Eddington luminosity"),
]


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def compact(text: Any, limit: int = 700) -> str:
    value = " ".join(str(text or "").split())
    return value if len(value) <= limit else value[: limit - 3] + "..."


def normalize_formula(text: Any) -> str:
    value = str(text or "").lower()
    value = re.sub(r"\\(?:left|right|quad|qquad)\b|\\[,;:!]", "", value)
    value = re.sub(r"\s+", "", value)
    value = re.sub(r"[{}]", "", value)
    return value


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def section_index(text: str) -> List[Dict[str, Any]]:
    sections: List[Dict[str, Any]] = []
    for match in SECTION_RE.finditer(text):
        title = compact(re.sub(r"\\[A-Za-z]+\*?(?:\[[^\]]*\])?", "", match.group("title")), 160)
        sections.append({
            "start": match.start(),
            "level": match.group("level"),
            "title": title or "untitled section",
        })
    return sections


def section_for_position(sections: List[Dict[str, Any]], start: int) -> Dict[str, str]:
    current = {"level": "document", "title": "front matter or abstract"}
    for section in sections:
        if int(section["start"]) <= start:
            current = {"level": str(section["level"]), "title": str(section["title"])}
        else:
            break
    return current


def context_sides(text: str, start: int, end: int, window: int) -> Tuple[str, str, str]:
    before = normalize_text(text[max(0, start - window):start])
    after = normalize_text(text[end:min(len(text), end + window)])
    local = normalize_text(text[max(0, start - window):min(len(text), end + window)])
    return before, after, local


def variable_dictionary(formula: str, context: str) -> List[Dict[str, str]]:
    blob = f"{formula} {context}"
    out: List[Dict[str, str]] = []
    seen: set[str] = set()
    for pattern, symbol, role in KNOWN_VARIABLES:
        if re.search(pattern, blob, re.IGNORECASE):
            if symbol not in seen:
                out.append({"symbol": symbol, "role": role})
                seen.add(symbol)
    return out


def source_document_stats(source_dir: Path) -> Dict[str, Any]:
    paths = sorted(path for path in source_dir.rglob("*") if path.is_file() and path.suffix.lower() in {".tex", ".txt", ".md", ".latex"})
    sizes = [path.stat().st_size for path in paths]
    begin_doc = 0
    display_markers = 0
    for path in paths:
        text = path.read_text(encoding="utf-8", errors="replace")
        begin_doc += int(bool(re.search(r"\\begin\{document\}", text)))
        display_markers += int(bool(re.search(r"\\begin\{(?:equation|align|gather|multline)|\\\[|\$\$", text)))
    return {
        "source_count": len(paths),
        "median_bytes": sorted(sizes)[len(sizes) // 2] if sizes else 0,
        "files_under_5kb": sum(size < 5000 for size in sizes),
        "begin_document_sources": begin_doc,
        "display_equation_sources": display_markers,
    }


def graph_node_index(graph: Dict[str, Any]) -> Dict[Tuple[str, str], Deque[Dict[str, Any]]]:
    index: Dict[Tuple[str, str], Deque[Dict[str, Any]]] = defaultdict(deque)
    for node in graph.get("nodes") or []:
        key = (str(node.get("source_id") or ""), normalize_formula(node.get("formula")))
        index[key].append(node)
    return index


def source_paths(source_dir: Path) -> Dict[str, Path]:
    paths: Dict[str, Path] = {}
    for path in source_dir.rglob("*"):
        if path.is_file() and path.suffix.lower() in {".tex", ".txt", ".md", ".latex", ".pdf"}:
            paths[source_id_from_path(path)] = path
    return paths


def slot_matches_for_node(node: Dict[str, Any]) -> List[Dict[str, Any]]:
    matches: List[Dict[str, Any]] = []
    for slot in SLOT_DEFINITIONS:
        matched, details = slot_match(node, slot)
        grade, grade_details = evidence_grade(node, slot)
        if matched or grade:
            matches.append({
                "slot_id": slot["slot_id"],
                "label": slot["label"],
                "grade": grade or "weak_slot_match",
                "required_condition": slot["required_condition"],
                "match": grade_details if grade else details,
            })
    return matches


def build_source_equations(
    source_dir: Path,
    graph: Dict[str, Any],
    *,
    context_window: int,
    max_context_chars: int,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    node_index = graph_node_index(graph)
    equations: List[Dict[str, Any]] = []
    matched = 0
    unmatched = 0
    per_source = Counter()

    for doc in iter_documents(source_dir):
        sections = section_index(doc.text)
        source_equations = extract_equations(doc.text)
        per_source[doc.source_id] = len(source_equations)
        for ordinal, equation in enumerate(source_equations, start=1):
            formula = str(equation.get("formula") or "")
            start = int(equation.get("start") or 0)
            end = int(equation.get("end") or start)
            before, after, local = context_sides(doc.text, start, end, context_window)
            key = (doc.source_id, normalize_formula(formula))
            graph_node = node_index[key].popleft() if node_index.get(key) else None
            if graph_node:
                matched += 1
                node = dict(graph_node)
            else:
                unmatched += 1
                node = {
                    "id": None,
                    "source_id": doc.source_id,
                    "formula": formula,
                    "context": local,
                    "route_signature": [],
                    "constructor_roles": [],
                    "transition_labels": [],
                    "case_evidence": case_evidence(formula, local, doc.source_id, ""),
                }
            section = section_for_position(sections, start)
            variables = variable_dictionary(formula, local)
            equations.append({
                "constructor_equation_id": f"K{len(equations):06d}",
                "source_id": doc.source_id,
                "source_path": doc.path,
                "source_equation_ordinal": ordinal,
                "section": section,
                "kind": equation.get("kind"),
                "formula": formula,
                "start": start,
                "end": end,
                "context_before": compact(before, max_context_chars),
                "context_after": compact(after, max_context_chars),
                "local_context": compact(local, max_context_chars * 2),
                "variables": variables,
                "matched_graph_node_id": node.get("id"),
                "formula_core": node.get("formula_core"),
                "formula_quality_flags": node.get("formula_quality_flags") or [],
                "text_role": node.get("text_role"),
                "route_signature": node.get("route_signature") or [],
                "route_profile": node.get("route_profile") or {},
                "constructor_roles": node.get("constructor_roles") or [],
                "transition_labels": node.get("transition_labels") or [],
                "source_frame_audit": node.get("source_frame_audit") or {},
                "target_frame_audit": node.get("target_frame_audit") or {},
                "case_evidence": node.get("case_evidence") or {},
                "slot_matches": slot_matches_for_node(node),
            })
    stats = {
        "source_count_with_equations": sum(1 for value in per_source.values() if value),
        "extracted_equation_count": len(equations),
        "matched_graph_node_count": matched,
        "unmatched_source_equation_count": unmatched,
        "top_sources_by_equation_count": per_source.most_common(12),
    }
    return equations, stats


def build_source_chains(equations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for equation in equations:
        grouped[str(equation["source_id"])].append(equation)

    chains: List[Dict[str, Any]] = []
    for source_id, rows in grouped.items():
        relevant = [
            row for row in sorted(rows, key=lambda item: int(item["source_equation_ordinal"]))
            if row.get("slot_matches") or (row.get("case_evidence") or {}).get("case_relevant")
        ]
        if not relevant:
            continue
        chains.append({
            "chain_id": f"CH{len(chains):05d}",
            "source_id": source_id,
            "equation_count": len(relevant),
            "equation_ids": [row["constructor_equation_id"] for row in relevant],
            "route_sequence": [row.get("route_signature") or [] for row in relevant],
            "slot_sequence": [
                [slot["slot_id"] for slot in row.get("slot_matches") or []]
                for row in relevant
            ],
            "section_sequence": [row.get("section") for row in relevant],
            "has_direct_collider_step": any(
                any(slot.get("grade") == "direct_collider_receipt" for slot in row.get("slot_matches") or [])
                for row in relevant
            ),
            "has_transfer_step": any(
                any(slot.get("grade") == "astrophysical_transfer_receipt" for slot in row.get("slot_matches") or [])
                for row in relevant
            ),
        })
    return chains


def readiness(source_stats: Dict[str, Any], chain_count: int) -> str:
    if source_stats.get("begin_document_sources", 0) == 0:
        return "limited_abstract_scale_sources"
    if chain_count == 0:
        return "no_constructor_chains"
    return "usable"


def render_markdown(export: Dict[str, Any]) -> str:
    counts = export["counts"]
    source_stats = export["source_document_stats"]
    lines = [
        "# Constructor-Layer Export",
        "",
        f"- readiness: `{export['readiness']}`",
        f"- sources: `{source_stats['source_count']}`",
        f"- sources with full-document markers: `{source_stats['begin_document_sources']}`",
        f"- sources with display-equation markers: `{source_stats['display_equation_sources']}`",
        f"- extracted equations: `{counts['extracted_equation_count']}`",
        f"- graph-node matches: `{counts['matched_graph_node_count']}`",
        f"- source-local constructor chains: `{counts['source_local_chain_count']}`",
        "",
        "## What This Export Adds",
        "",
        "Each constructor equation contains source id, section, equation order, local context, variable roles, graph match, route signature, constructor roles and slot matches.",
        "",
        "## Limits",
        "",
    ]
    if export["readiness"] == "limited_abstract_scale_sources":
        lines.append(
            "The current source folder is mostly abstract-scale text. This export is structurally valid, but it cannot reconstruct full paper derivations until run on full LaTeX/PDF sources."
        )
    else:
        lines.append("The source folder contains full document markers, so source-local equation chains can be interpreted as paper-level constructor evidence.")
    lines += ["", "## Source-Local Chains", ""]
    for chain in export.get("source_local_chains", [])[:20]:
        lines.append(
            f"- `{chain['source_id']}`: {chain['equation_count']} equations; "
            f"direct={chain['has_direct_collider_step']}; transfer={chain['has_transfer_step']}"
        )
    return "\n".join(lines).rstrip() + "\n"


def build_constructor_layer_export(
    *,
    run_dir: Path,
    source_dir: Path,
    out_dir: Path,
    context_window: int = 1400,
    max_context_chars: int = 900,
) -> Dict[str, Any]:
    graph = read_json(run_dir / "equation_mechanism_graph.json")
    source_stats = source_document_stats(source_dir)
    equations, equation_stats = build_source_equations(
        source_dir,
        graph,
        context_window=context_window,
        max_context_chars=max_context_chars,
    )
    chains = build_source_chains(equations)
    counts = {
        **equation_stats,
        "source_local_chain_count": len(chains),
        "slot_match_equation_count": sum(1 for row in equations if row.get("slot_matches")),
        "case_relevant_equation_count": sum(1 for row in equations if (row.get("case_evidence") or {}).get("case_relevant")),
    }
    export = {
        "report_type": "lhc_constructor_layer_export",
        "readiness": readiness(source_stats, len(chains)),
        "source_run": str(run_dir),
        "source_dir": str(source_dir),
        "source_document_stats": source_stats,
        "counts": counts,
        "constructor_equations": equations,
        "source_local_chains": chains,
        "claim_scope": (
            "This export reconstructs source-local constructor objects from available source text and the public equation mechanism graph. "
            "Full derivation claims require full source papers; abstract-scale sources are marked as limited."
        ),
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    write_json(out_dir / "constructor_layer_export.json", export)
    (out_dir / "constructor_layer_export.md").write_text(render_markdown(export), encoding="utf-8")
    return {
        "json": str(out_dir / "constructor_layer_export.json"),
        "markdown": str(out_dir / "constructor_layer_export.md"),
        "readiness": export["readiness"],
        "counts": counts,
    }
