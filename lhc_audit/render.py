from __future__ import annotations

from collections import Counter
from typing import Any, Dict, List


ROLE_EXPLANATIONS = {
    "production_threshold": "conditions under which a collider event could produce the hypothesized object",
    "evaporation_branch": "mass-loss or lifetime branch, usually through Hawking-radiation assumptions",
    "stable_branch": "counterfactual branch in which the object is long-lived or does not evaporate promptly",
    "capture_stopping": "whether the object is slowed, trapped, or passes through matter",
    "accretion_growth": "whether captured matter can produce growth rather than loss or escape",
    "astrophysical_bound": "external survival constraint from cosmic-ray exposure, white dwarfs, neutron stars, or related systems",
    "exclusion_conclusion": "source-local conclusion that a branch is ruled out or safe under specified premises",
    "unclassified": "equation witness without enough local context for a mechanism-role label",
}


def _source_inventory(sources: Dict[str, Any], limit: int = 30) -> List[str]:
    items = sources.get("sources", [])
    lines: List[str] = []
    lines.append(f"Total selected sources: `{len(items)}`.")
    if not items:
        return lines
    years = Counter()
    for item in items:
        sid = str(item.get("source_id", ""))
        year = sid[:2]
        if year.isdigit():
            years[f"20{year}" if int(year) < 80 else f"19{year}"] += 1
    if years:
        lines.append(
            "Year coverage: "
            + ", ".join(f"{year}: {count}" for year, count in sorted(years.items())[:12])
            + (" ..." if len(years) > 12 else "")
        )
    lines.append("")
    lines.append("Representative source files:")
    for item in items[:limit]:
        lines.append(f"- `{item.get('source_id')}`: `{item.get('path')}`")
    if len(items) > limit:
        lines.append(f"- ... `{len(items) - limit}` additional selected sources omitted from this report.")
    return lines


def _role_count_lines(operational: Dict[str, Any]) -> List[str]:
    lines: List[str] = []
    role_counts = operational.get("role_counts", {})
    total = sum(int(v) for v in role_counts.values()) or 1
    for role, count in sorted(role_counts.items(), key=lambda kv: (-int(kv[1]), kv[0])):
        pct = 100.0 * int(count) / total
        explanation = ROLE_EXPLANATIONS.get(role, "mechanism role")
        lines.append(f"- `{role}`: `{count}` witness(es), {pct:.1f}% — {explanation}.")
    return lines


def _chain_lines(chains: List[Dict[str, Any]]) -> List[str]:
    if not chains:
        return [
            "No complete extracted chain candidate was found. The correct audit output is therefore a request for more source-local equations or manual review.",
        ]
    lines: List[str] = []
    by_type = Counter(chain.get("chain_type", "unknown") for chain in chains)
    lines.append(
        "Detected chain types: "
        + ", ".join(f"`{name}`: `{count}`" for name, count in sorted(by_type.items()))
        + "."
    )
    lines.append("")
    for chain in chains[:20]:
        lines.append(f"### {chain['chain_type']} ({chain['source_id']})")
        lines.append("")
        for step in chain.get("logic", []):
            lines.append(f"- {step}")
        lines.append("")
    if len(chains) > 20:
        lines.append(f"`{len(chains) - 20}` additional chain candidates omitted from this report.")
        lines.append("")
    return lines


def render_shallow_failure(provenance: Dict[str, Any], operational: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append("# Why Provenance Alone Fails On The LHC Black-Hole Case")
    lines.append("")
    lines.append("A provenance/discourse graph can say which papers support or challenge the safety conclusion.")
    lines.append("It cannot by itself decide whether the safety conclusion follows from the physical mechanism.")
    lines.append("")
    lines.append("## What the provenance graph sees")
    lines.append("")
    nodes = provenance.get("nodes", [])
    source_nodes = [node for node in nodes if node.get("url") or node.get("role") not in (None, "unknown")]
    claim_nodes = [node for node in nodes if str(node.get("id", "")).startswith("C")]
    lines.append(f"- source/provenance nodes: `{len(source_nodes)}`")
    lines.append(f"- extracted claim nodes: `{len(claim_nodes)}`")
    lines.append("")
    for node in source_nodes[:30]:
        lines.append(f"- `{node['id']}`: {node.get('title', node['id'])} — stance `{node.get('stance')}`")
    if len(source_nodes) > 30:
        lines.append(f"- ... `{len(source_nodes) - 30}` additional source nodes omitted.")
    lines.append("")
    lines.append("## What it misses")
    lines.append("")
    lines.append("- whether the paper contains a production-threshold branch, not only a safety claim;")
    lines.append("- whether Hawking evaporation is treated as a branch or as an assumed conclusion;")
    lines.append("- whether the stable-object branch is propagated through capture, stopping and accretion;")
    lines.append("- whether cosmic-ray, white-dwarf or neutron-star arguments act as physical exclusion bounds;")
    lines.append("- whether a risk challenge breaks a derivation step or only disputes a premise.")
    lines.append("")
    lines.append("## Mechanism evidence found")
    lines.append("")
    lines.extend(_role_count_lines(operational))
    lines.append("")
    lines.append("## Chain candidates")
    lines.append("")
    for chain in operational.get("chain_candidates", [])[:20]:
        lines.append(f"- `{chain['source_id']}` / `{chain['chain_type']}` / `{chain['status']}`")
        for step in chain.get("logic", []):
            lines.append(f"  - {step}")
    if len(operational.get("chain_candidates", [])) > 20:
        lines.append(f"- ... `{len(operational.get('chain_candidates', [])) - 20}` additional chain candidates omitted.")
    return "\n".join(lines) + "\n"


def render_audit_report(sources: Dict[str, Any], provenance: Dict[str, Any], operational: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append("# LHC Black-Hole Safety: Mechanism-First Audit")
    lines.append("")
    lines.append("## Result")
    lines.append("")
    chains = operational.get("chain_candidates", [])
    if chains:
        lines.append("The corpus contains source-local mechanism chains that a provenance graph does not expose.")
    else:
        lines.append("The current corpus does not yet contain a complete extracted mechanism chain; this is an audit failure, not permission to invent one.")
    lines.append("")
    lines.append("## Two Graphs")
    lines.append("")
    lines.append("1. **Provenance graph:** papers, authors, dates, claim families and disagreement links.")
    lines.append("2. **Operational graph:** equation witnesses, local derivation roles and branch-specific tests.")
    lines.append("")
    lines.append("## Audit Scale")
    lines.append("")
    lines.append(f"- selected sources: `{len(sources.get('sources', []))}`")
    lines.append(f"- operational witness nodes: `{len(operational.get('nodes', []))}`")
    lines.append(f"- derivation-candidate edges: `{len(operational.get('edges', []))}`")
    lines.append(f"- complete chain candidates: `{len(chains)}`")
    lines.append("")
    lines.append("## Mechanism Role Counts")
    lines.append("")
    lines.extend(_role_count_lines(operational))
    lines.append("")
    lines.append("## Inspectable Chain Candidates")
    lines.append("")
    lines.extend(_chain_lines(chains))
    lines.append("## Interpretation")
    lines.append("")
    lines.append("The useful object is not a vote between named papers. It is a branch structure: collider production assumptions feed either an evaporation branch or a stable-object branch; the stable branch must then pass through stopping, capture, accretion and astrophysical survival constraints. A provenance graph can record disagreement about these papers, but it cannot tell whether the branch closes.")
    lines.append("")
    lines.append("## Source Inventory")
    lines.append("")
    lines.extend(_source_inventory(sources))
    lines.append("")
    lines.append("## Boundary")
    lines.append("")
    lines.append("The script does not assert final LHC safety. It shows whether a source set contains the mechanism-level evidence needed to inspect that safety argument.")
    return "\n".join(lines) + "\n"
