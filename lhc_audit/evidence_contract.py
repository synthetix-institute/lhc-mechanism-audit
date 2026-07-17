from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Sequence, Set, Tuple


SLOT_ORDER = [
    "production_selector",
    "survival_lifetime",
    "stopping_capture",
    "net_positive_growth",
    "growth_timescale",
    "astronomical_bound_evasion",
]


SLOT_CONTRACTS: List[Dict[str, Any]] = [
    {
        "slot_id": "production_selector",
        "label": "production threshold",
        "required_condition": "parton collision can enter a low-scale-gravity production channel",
        "equation_template": r"\sqrt{\hat s}=\sqrt{x_1x_2s}>M_{\min},\quad \sigma_{\rm form}\sim \pi r_s^2(M,M_D,n)",
        "route_need": ["constraint_closure", "boundary_weak_form"],
        "formula_quantities": ["production_threshold", "production_cross_section"],
        "inputs": ["parton_energy", "gravity_scale"],
        "outputs": ["produced_microscopic_black_hole"],
    },
    {
        "slot_id": "survival_lifetime",
        "label": "survival against evaporation",
        "required_condition": "object lifetime exceeds the capture or stopping time",
        "equation_template": r"\tau_{\rm evap}(M,M_D,n)>\tau_{\rm capture}",
        "route_need": ["transport_flow", "constraint_closure"],
        "formula_quantities": ["evaporation_rate", "black_hole_lifetime"],
        "inputs": ["produced_microscopic_black_hole"],
        "outputs": ["long_lived_microscopic_black_hole"],
    },
    {
        "slot_id": "stopping_capture",
        "label": "stopping or capture in matter",
        "required_condition": "object loses enough kinetic energy to remain inside matter",
        "equation_template": r"L_{\rm stop}(M,v,\rho,\sigma)<L_{\rm body}\quad {\rm or}\quad \tau_{\rm capture}<\tau_{\rm escape}",
        "route_need": ["transport_flow", "constraint_closure"],
        "formula_quantities": ["stopping_power", "stopping_length", "capture_condition"],
        "inputs": ["long_lived_microscopic_black_hole", "medium_state"],
        "outputs": ["captured_microscopic_black_hole"],
    },
    {
        "slot_id": "net_positive_growth",
        "label": "net positive mass growth",
        "required_condition": "matter intake exceeds mass loss",
        "equation_template": r"\dot M_{\rm net}=\rho\,\sigma(M)\,v-P_{\rm evap}(M)/c^2>0",
        "route_need": ["transport_flow", "constraint_closure", "spectral_operator"],
        "formula_quantities": ["mass_rate", "mass_gain_per_length", "net_mass_rate"],
        "inputs": ["captured_microscopic_black_hole", "medium_state"],
        "outputs": ["growing_microscopic_black_hole"],
    },
    {
        "slot_id": "growth_timescale",
        "label": "growth on a relevant timescale",
        "required_condition": "integrated growth time is shorter than the physical exposure time",
        "equation_template": r"t_{\rm grow}=\int_{M_0}^{M_*}\frac{dM}{\dot M_{\rm net}(M)}<t_{\rm exposure}",
        "route_need": ["transport_flow", "constraint_closure"],
        "formula_quantities": ["growth_timescale"],
        "inputs": ["growing_microscopic_black_hole", "mass_rate"],
        "outputs": ["macroscopic_growth_within_exposure"],
    },
    {
        "slot_id": "astronomical_bound_evasion",
        "label": "evasion of astronomical survival bounds",
        "required_condition": "same mechanism must remain compatible with observed compact-object survival",
        "equation_template": r"N_{\rm CR}P_{\rm capture}P_{\rm grow}\ll 1\quad {\rm for\ observed\ white\ dwarfs/neutron\ stars}",
        "route_need": ["constraint_closure", "spectral_operator"],
        "formula_quantities": ["astronomical_survival_bound"],
        "inputs": ["macroscopic_growth_within_exposure", "cosmic_ray_exposure"],
        "outputs": ["model_consistent_with_astronomical_survival"],
    },
]


RELATION_RE = re.compile(
    r"=|<|>|&=&|\\leq?|\\geq?|\\ll|\\gg|\\sim|\\simeq|\\approx|"
    r"\\lesssim|\\gtrsim|\\propto"
)
SYMBOL_RE = re.compile(r"\\[A-Za-z]+|[A-Za-z][A-Za-z0-9]*|[_^{}]")
UNIT_PATTERNS = {
    "energy": re.compile(r"\\?(?:TeV|GeV|MeV|keV|eV)\b", re.I),
    "time": re.compile(r"\\?(?:s|sec|second|yr|year|Myr|Gyr)\b", re.I),
    "length": re.compile(r"\\?(?:fm|cm|mm|km|angstrom|AA)\b", re.I),
    "mass": re.compile(r"M_?\{?\\?(?:odot|sun)\}?|\\?(?:kg|g)\b", re.I),
    "density": re.compile(r"(?:g|kg)\s*/\s*(?:cm|m)\^?\{?-?3\}?", re.I),
}


REGIME_PATTERNS = {
    "black_hole": re.compile(r"black[ -]?hole|micro(?:scopic)?[ -]?black[ -]?hole|mini[ -]?black[ -]?hole|\bMBH\b|horizon|Schwarzschild", re.I),
    "collider": re.compile(r"\bLHC\b|Large Hadron Collider|collider|parton|hadron collision|proton[- ]proton", re.I),
    "astrophysical": re.compile(r"cosmic ray|white dwarf|neutron star|compact object|astronomical|stellar|Sun\b|Earth\b", re.I),
    "material": re.compile(r"matter|medium|density|stopping|capture|accretion|Bondi", re.I),
}


FORMULA_QUANTITY_PATTERNS: Dict[str, Sequence[re.Pattern[str]]] = {
    "production_threshold": (
        re.compile(r"(?:\\sqrt\s*\{?\\hat\s*\{?s\}?|\\hat\s*\{?s\}?).{0,100}(?:>|\\ge|\\gtrsim).{0,100}M_?\{?(?:\\?min|D|f|\\ast)\}?", re.S),
        re.compile(r"\\sqrt\s*\{?s\}?.{0,120}(?:\\xi|\\Theta).{0,120}(?:M_?\{?(?:f|D|\\?min)\}?)", re.S),
        re.compile(r"M_?\{?(?:\\?min|BH)\}?.{0,100}(?:>|\\ge|\\gtrsim|\\sim).{0,100}M_?\{?(?:D|f|\\ast)\}?", re.S),
        re.compile(r"\\tau\s*=\s*x_?\{?1\}?\s*x_?\{?2\}?.{0,80}>.{0,80}\\tau_?\{?min\}?.{0,100}M_?\{?min\}?\s*\^?\{?2", re.S),
    ),
    "production_cross_section": (
        re.compile(r"\\sigma_?\{?(?:\\rm\s*)?(?:form|BH|black)\}?(?:\([^)]*\))?.{0,120}(?:\\approx|\\sim|=).{0,80}\\pi.{0,80}(?:r_?\{?[sH]\}?|R_?\{?H\}?|R)\s*\^?\{?2", re.S),
        re.compile(r"\\hat\s*\\?sigma(?:\([^)]*\))?.{0,100}(?:\\approx|\\sim|=).{0,80}\\pi.{0,80}(?:r_?\{?[sH]\}?|R_?\{?H\}?|R)\s*\^?\{?2", re.S),
        re.compile(r"\\sigma(?:\([^)]*\)).{0,100}(?:\\approx|\\sim|=).{0,80}\\pi.{0,80}R_?\{?H\}?\s*\^?\{?2.{0,120}(?:\\xi|\\Theta)", re.S),
        re.compile(r"\\sigma_?\{?BH\}?.{0,80}M\s*>\s*M_?\{?min\}?.{0,100}=.{0,160}\\int.{0,240}\\hat\s*\\?sigma", re.S),
    ),
    "evaporation_rate": (
        re.compile(r"(?:\\dot\s*\{?M\}?|dM\s*(?:/|\\over)\s*dt|\\frac\s*\{(?:\\mathrm\{d\}|\\ud|d)\s*M\}\s*\{(?:\\mathrm\{d\}|\\ud|d)\s*(?:t|\\tau)\}).{0,80}(?:(?:=|\\approx|\\simeq|\\sim)\s*-|<\s*0|-\s*P_?\{?(?:\\rm\s*)?evap)", re.S),
        re.compile(r"(?<![A-Za-z])(?:P|\\Gamma)_?\{?(?:\\rm\s*)?(?:evap|D|H)\}?.{0,80}(?:=|\\sim|\\simeq|\\propto)", re.S),
    ),
    "black_hole_lifetime": (
        re.compile(r"(?:\\tau|t)_?\{?(?:\\rm\s*)?(?:BH|evap|life|decay)\}?.{0,100}(?:=|<|>|\\sim|\\simeq|\\propto)", re.S),
    ),
    "black_hole_temperature": (
        re.compile(r"(?<![A-Za-z])T_?\{?(?:\\rm\s*)?(?:BH|H)\}?.{0,100}(?:=|\\sim|\\simeq|\\propto)", re.S),
    ),
    "stopping_power": (
        re.compile(r"d[Ep]\s*(?:/|\\over)\s*d?[x\\ell l].{0,100}(?:=|\\sim|\\simeq|\\propto|>|<)", re.S),
    ),
    "stopping_length": (
        re.compile(r"(?:L|d)_?\{?(?:\\rm\s*)?(?:stop|stopping)\}?.{0,100}(?:=|<|>|\\sim|\\simeq)", re.S),
    ),
    "capture_condition": (
        re.compile(r"(?:P|\\sigma|\\tau|v|E)_?\{?(?:\\rm\s*)?(?:cap|capture|esc|escape)\}?.{0,100}(?:=|<|>|\\sim|\\simeq)", re.S),
    ),
    "mass_rate": (
        re.compile(r"(?:\\dot\s*\{?M\}?|dM\s*(?:/|\\over)\s*dt|\\frac\s*\{(?:\\mathrm\{d\}|\\ud|d)\s*M\}\s*\{(?:\\mathrm\{d\}|\\ud|d)\s*(?:t|\\tau)\}).{0,120}(?:=|<|>|\\sim|\\simeq|\\propto)", re.S),
    ),
    "mass_gain_per_length": (
        re.compile(r"\\frac\s*\{dM(?:_?\{?\d+\}?)?(?:\([^)]*\))?\}\s*\{dx\}.{0,120}(?:=|\\ge|>|\\sim|\\simeq|\\propto)", re.S),
        re.compile(r"dM\s*(?:/|\\over)\s*d?(?:x|\\ell|l).{0,120}(?:=|\\ge|>|\\sim|\\simeq|\\propto)", re.S),
    ),
    "net_mass_rate": (
        re.compile(r"(?:\\dot\s*\{?M\}?_?\{?(?:\\rm\s*)?net\}?|dM\s*(?:/|\\over)\s*dt).{0,160}(?:\\rho|rho|P_?\{?(?:\\rm\s*)?evap|\\Gamma_?\{?[AD]\}?).{0,100}(?:>|<|=)", re.S),
    ),
    "growth_timescale": (
        re.compile(r"t_?\{?(?:\\rm\s*)?(?:grow|acc|growth)\}?.{0,120}(?:=|<|>|\\sim|\\simeq)", re.S),
        re.compile(r"(?<![A-Za-z])t_?\{?(?:w|WD|NS)\}?(?:\([^)]*\))?.{0,40}(?:=|&=&|\\approx|\\sim).{0,240}(?:\\yr|\\mathrm\{yr\}|Gyr|Myr|s(?:ec)?)", re.S),
        re.compile(r"(?<![A-Za-z])t\s*\([^)]*R_?[BCD][^)]*\).{0,40}(?:=|&=&|\\approx|\\sim).{0,260}(?:\\yr|\\mathrm\{yr\}|Gyr|Myr)", re.S),
        re.compile(r"\\int.{0,120}dM.{0,80}(?:\\dot\s*\{?M\}?|dM\s*(?:/|\\over)\s*dt)", re.S),
    ),
    "astronomical_survival_bound": (
        re.compile(r"N_?\{?(?:\\rm\s*)?(?:CR|BH)\}?.{0,160}P_?\{?(?:\\rm\s*)?(?:cap|capture)\}?.{0,160}P_?\{?(?:\\rm\s*)?grow\}?.{0,80}(?:<|\\ll)", re.S),
        re.compile(r"t_?\{?(?:\\rm\s*)?(?:grow|acc)\}?.{0,100}(?:>|<|\\ll|\\gg).{0,100}t_?\{?(?:\\rm\s*)?(?:WD|NS|star|obs|life)\}?", re.S),
        re.compile(r"(?:N|\\Phi|R)_?\{?(?:\\rm\s*)?(?:CR|BH|prod)\}?.{0,120}(?:=|<|>|\\sim|\\simeq).{0,120}(?:WD|NS|white|neutron)", re.S),
        re.compile(r"t_?\{?(?:w|WD|NS)\}?.{0,100}(?:=|<|>|\\ll|\\gg|\\approx|\\sim).{0,220}(?:\\yr|Gyr|Myr)", re.S),
    ),
}


def compact_math(text: Any) -> str:
    return " ".join(str(text or "").split())


def infer_regimes(formula: Any, context: Any) -> Set[str]:
    blob = f"{formula or ''} {context or ''}"
    return {name for name, pattern in REGIME_PATTERNS.items() if pattern.search(blob)}


def infer_units(formula: Any) -> List[str]:
    value = str(formula or "")
    return sorted(name for name, pattern in UNIT_PATTERNS.items() if pattern.search(value))


def infer_symbols(formula: Any) -> List[str]:
    value = str(formula or "")
    symbols: List[str] = []
    seen: Set[str] = set()
    for token in SYMBOL_RE.findall(value):
        normalized = token.strip("{}")
        if normalized and normalized not in seen:
            seen.add(normalized)
            symbols.append(normalized)
    return symbols[:80]


def infer_formula_quantities(formula: Any) -> Tuple[List[str], Dict[str, List[str]]]:
    value = compact_math(formula)
    quantities: List[str] = []
    hits: Dict[str, List[str]] = {}
    if not RELATION_RE.search(value):
        return quantities, hits
    for quantity, patterns in FORMULA_QUANTITY_PATTERNS.items():
        matched = [pattern.pattern for pattern in patterns if pattern.search(value)]
        if matched:
            quantities.append(quantity)
            hits[quantity] = matched
    return quantities, hits


def equation_contract(node: Dict[str, Any]) -> Dict[str, Any]:
    formula = compact_math(node.get("formula"))
    context = compact_math(node.get("context"))
    source_context = compact_math(
        " ".join(
            str(node.get(key) or "")
            for key in ("source_title", "source_stance", "source_role")
        )
    )
    quantities, quantity_hits = infer_formula_quantities(formula)
    relation = RELATION_RE.search(formula)
    formula_shape_valid = bool(
        relation
        and relation.start() <= 160
        and "\\begin{" not in formula
        and "\\end{" not in formula
        and "$" not in formula
    )
    return {
        "formula": formula,
        "has_relation": bool(relation),
        "formula_shape_valid": formula_shape_valid,
        "formula_quantities": quantities,
        "quantity_hits": quantity_hits,
        "symbols": infer_symbols(formula),
        "units": infer_units(formula),
        "regimes": sorted(infer_regimes(formula, f"{context} {source_context}")),
        "source_context": source_context,
        "source_id": node.get("source_id"),
        "equation_ordinal": node.get("source_equation_ordinal"),
    }


def slot_contract(slot_id: str) -> Dict[str, Any]:
    for slot in SLOT_CONTRACTS:
        if slot["slot_id"] == slot_id:
            return slot
    raise KeyError(slot_id)


def match_equation_to_slot(node: Dict[str, Any], slot: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    contract = equation_contract(node)
    required_quantities = set(slot.get("formula_quantities") or [])
    quantity_hits = sorted(required_quantities & set(contract["formula_quantities"]))
    routes = set(node.get("route_signature") or [])
    route_hits = sorted(routes & set(slot.get("route_need") or []))
    matched = bool(quantity_hits) and bool(contract["formula_shape_valid"])
    if slot.get("slot_id") == "net_positive_growth":
        formula_quantities = set(contract["formula_quantities"])
        formula = contract["formula"]
        if "growth_timescale" in formula_quantities and "net_mass_rate" not in formula_quantities:
            matched = False
        if "evaporation_rate" in formula_quantities and "net_mass_rate" not in formula_quantities:
            matched = False
        if re.search(r"(?:=|\\approx|\\sim|\\simeq)\s*-", formula) and "net_mass_rate" not in formula_quantities:
            matched = False
    return matched, {
        "formula_quantity_hits": quantity_hits,
        "formula_pattern_hits": {
            quantity: contract["quantity_hits"].get(quantity, [])
            for quantity in quantity_hits
        },
        "route_hits": route_hits,
        "regimes": contract["regimes"],
        "symbols": contract["symbols"],
        "units": contract["units"],
        "input_quantities": list(slot.get("inputs") or []),
        "output_quantities": list(slot.get("outputs") or []),
        "formula_contract_valid": matched,
        "formula_shape_valid": contract["formula_shape_valid"],
    }


def classify_receipt(node: Dict[str, Any], slot: Dict[str, Any]) -> Tuple[str | None, Dict[str, Any]]:
    matched, details = match_equation_to_slot(node, slot)
    if not matched:
        return None, details

    regimes = set(details["regimes"])
    if "black_hole" not in regimes:
        return None, details

    if "collider" in regimes:
        details["evidence_scope"] = "direct_collider"
        return "direct_collider_receipt", details

    if "astrophysical" in regimes or "material" in regimes:
        details["evidence_scope"] = "cross_regime_candidate"
        details["transfer_validation"] = "requires_explicit_variable_regime_map"
        return "candidate_transfer_receipt", details

    return None, details


def contracts_compose(left: Dict[str, Any], right: Dict[str, Any]) -> bool:
    left_outputs = left.get("output_quantities") or left.get("outputs") or []
    right_inputs = right.get("input_quantities") or right.get("inputs") or []
    return bool(set(left_outputs) & set(right_inputs))


def source_local_reachable(
    source_id: Any,
    left_node_id: Any,
    right_node_id: Any,
    edges: Iterable[Dict[str, Any]],
) -> bool:
    source = str(source_id or "")
    left = str(left_node_id or "")
    right = str(right_node_id or "")
    if not source or not left or not right:
        return False
    adjacency: Dict[str, Set[str]] = {}
    for edge in edges:
        if str(edge.get("source_id") or "") != source:
            continue
        a = str(edge.get("source") or "")
        b = str(edge.get("target") or "")
        if a and b:
            adjacency.setdefault(a, set()).add(b)
    frontier = [left]
    visited = {left}
    while frontier:
        current = frontier.pop(0)
        if current == right:
            return True
        for nxt in adjacency.get(current, set()):
            if nxt not in visited:
                visited.add(nxt)
                frontier.append(nxt)
    return False
