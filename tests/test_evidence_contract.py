from __future__ import annotations

from lhc_audit.evidence_contract import SLOT_CONTRACTS, classify_receipt


def slot(slot_id: str):
    return next(item for item in SLOT_CONTRACTS if item["slot_id"] == slot_id)


def node(formula: str, context: str):
    return {"formula": formula, "context": context, "route_signature": []}


def test_rapidity_cut_is_not_a_production_receipt():
    grade, details = classify_receipt(
        node(r"|y_{\gamma\gamma}|\le 1", "LHC microscopic black-hole production search"),
        slot("production_selector"),
    )
    assert grade is None
    assert details["formula_quantity_hits"] == []


def test_context_does_not_turn_generic_equation_into_evaporation():
    grade, _ = classify_receipt(
        node(r"E^2=p^2+m^2", "Hawking evaporation lifetime for a black hole at the LHC"),
        slot("survival_lifetime"),
    )
    assert grade is None


def test_hawking_temperature_alone_does_not_establish_survival():
    grade, _ = classify_receipt(
        node(r"T_H=(d+1)/(4\pi R_H)", "mini black hole at a collider"),
        slot("survival_lifetime"),
    )
    assert grade is None


def test_bondi_growth_is_not_stopping():
    value = node(
        r"\frac{dM}{dt}=\pi\rho v r_c^2(M)",
        "black-hole accretion in a white dwarf medium",
    )
    stopping_grade, _ = classify_receipt(value, slot("stopping_capture"))
    growth_grade, _ = classify_receipt(value, slot("net_positive_growth"))
    assert stopping_grade is None
    assert growth_grade == "candidate_transfer_receipt"


def test_true_production_threshold_is_direct_collider_receipt():
    grade, details = classify_receipt(
        node(
            r"\tau=x_1x_2>\tau_{min}=M_{min}^2/(y^2s)",
            "LHC parton production of a microscopic black hole",
        ),
        slot("production_selector"),
    )
    assert grade == "direct_collider_receipt"
    assert "production_threshold" in details["formula_quantity_hits"]


def test_momentum_loss_is_stopping_receipt():
    grade, _ = classify_receipt(
        node(
            r"\left({dp\over d\ell}\right)_{sc}=-C\rho E^2R^2/s",
            "stopping of an LHC-produced microscopic black hole in matter",
        ),
        slot("stopping_capture"),
    )
    assert grade == "direct_collider_receipt"


def test_dedicated_source_title_supplies_regime_without_changing_formula_role():
    value = node(
        r"{dM\over dt}=-{C\over R_H^2}",
        "The mass loss is obtained by integration over emitted modes.",
    )
    value["source_title"] = "Exclusion of black hole disaster scenarios at the LHC"
    grade, details = classify_receipt(value, slot("survival_lifetime"))
    assert grade == "direct_collider_receipt"
    assert "evaporation_rate" in details["formula_quantity_hits"]
