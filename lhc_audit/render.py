from __future__ import annotations

from typing import Any, Dict, List


def render_shallow_failure(provenance: Dict[str, Any], operational: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append("# Why Provenance Alone Fails On The LHC Black-Hole Case")
    lines.append("")
    lines.append("A provenance/discourse graph can say which papers support or challenge the safety conclusion.")
    lines.append("It cannot by itself decide whether the safety conclusion follows from the physical mechanism.")
    lines.append("")
    lines.append("## What the provenance graph sees")
    lines.append("")
    for node in provenance.get("nodes", []):
        lines.append(f"- `{node['id']}`: {node.get('title', node['id'])} — stance `{node.get('stance')}`")
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
    for role, count in sorted(operational.get("role_counts", {}).items()):
        lines.append(f"- `{role}`: {count} witness(es)")
    lines.append("")
    lines.append("## Chain candidates")
    lines.append("")
    if not operational.get("chain_candidates"):
        lines.append("No complete chain candidate was found. The correct output is therefore not a confident conclusion, but a request for more source-local equations or manual review.")
    for chain in operational.get("chain_candidates", []):
        lines.append(f"- `{chain['source_id']}` / `{chain['chain_type']}` / `{chain['status']}`")
        for step in chain.get("logic", []):
            lines.append(f"  - {step}")
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
    lines.append("## Sources")
    lines.append("")
    for item in sources.get("sources", []):
        lines.append(f"- `{item.get('source_id')}`: `{item.get('path')}`")
    lines.append("")
    lines.append("## Mechanism Role Counts")
    lines.append("")
    for role, count in sorted(operational.get("role_counts", {}).items()):
        lines.append(f"- `{role}`: `{count}`")
    lines.append("")
    lines.append("## Inspectable Chain Candidates")
    lines.append("")
    for chain in chains:
        lines.append(f"### {chain['chain_type']} ({chain['source_id']})")
        lines.append("")
        for step in chain.get("logic", []):
            lines.append(f"- {step}")
        lines.append("")
    lines.append("## Boundary")
    lines.append("")
    lines.append("The script does not assert final LHC safety. It shows whether a source set contains the mechanism-level evidence needed to inspect that safety argument.")
    return "\n".join(lines) + "\n"
