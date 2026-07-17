from __future__ import annotations

import json
from pathlib import Path

from lhc_audit.physical_constructor import build_physical_constructor


FORMULAS = [
    r"\tau=x_1x_2>\tau_{min}=M_{min}^2/(y^2s)",
    r"\frac{dM}{dt}\approx-P_{evap}<0",
    r"{dp\over d\ell}=-A\rho R^2",
    r"\frac{dM}{dt}=\rho\sigma v>0",
    r"t_{grow}=\int dM/\dot M<t_{exposure}",
    r"N_{CR}P_{capture}P_{grow}\ll1",
]


def write_graph(run_dir: Path, *, omit_edge: int | None = None) -> None:
    nodes = []
    edges = []
    for index, formula in enumerate(FORMULAS):
        nodes.append({
            "id": f"E{index}",
            "source_id": "0806.3381",
            "source_equation_ordinal": index,
            "formula": formula,
            "context": "LHC microscopic black hole collider matter cosmic ray white dwarf neutron star",
            "route_signature": ["transport_flow", "constraint_closure"],
            "route_profile": {"transport_flow": 0.8, "constraint_closure": 0.8},
            "constructor_roles": ["operator_apparatus", "closure_constraints"],
            "formula_detail_score": 8,
            "pair_status": "complete_constructor_pair",
            "case_evidence": {"local_categories": ["black_hole", "collider_threshold"]},
        })
        if index and omit_edge != index - 1:
            edges.append({
                "source": f"E{index - 1}",
                "target": f"E{index}",
                "source_id": "0806.3381",
                "edge_type": "source_local_route_transition",
            })
    graph = {
        "nodes": nodes,
        "usable_node_ids": [node["id"] for node in nodes],
        "edges": edges,
        "source_witness_count": len(nodes),
        "usable_mechanism_node_count": len(nodes),
        "case_relevant_mechanism_node_count": len(nodes),
    }
    (run_dir / "equation_mechanism_graph.json").write_text(json.dumps(graph), encoding="utf-8")


def test_constructor_closes_only_with_composable_source_local_paths(tmp_path: Path):
    write_graph(tmp_path)
    result = build_physical_constructor(tmp_path)
    assert result["branch_closed"] is True
    assert len(result["supported_transitions"]) == 5


def test_missing_source_local_path_keeps_branch_open(tmp_path: Path):
    write_graph(tmp_path, omit_edge=2)
    result = build_physical_constructor(tmp_path)
    assert result["branch_closed"] is False
    assert any(
        transition["source_slot"] == "stopping_capture"
        and transition["target_slot"] == "net_positive_growth"
        for transition in result["broken_transitions"]
    )


def test_constructor_retains_every_matching_equation(tmp_path: Path):
    nodes = [
        {
            "id": f"G{index}",
            "source_id": "growth-paper",
            "source_equation_ordinal": index,
            "formula": rf"\frac{{dM}}{{dt}}=\rho\sigma v+{index}>0",
            "context": "LHC microscopic black hole accretion in matter",
            "route_signature": ["transport_flow", "constraint_closure"],
            "constructor_roles": ["operator_apparatus", "closure_constraints"],
            "formula_detail_score": 8,
            "pair_status": "complete_constructor_pair",
            "case_evidence": {},
        }
        for index in range(15)
    ]
    graph = {
        "nodes": nodes,
        "usable_node_ids": [node["id"] for node in nodes],
        "edges": [],
        "source_witness_count": len(nodes),
        "usable_mechanism_node_count": len(nodes),
        "case_relevant_mechanism_node_count": len(nodes),
    }
    (tmp_path / "equation_mechanism_graph.json").write_text(
        json.dumps(graph),
        encoding="utf-8",
    )

    result = build_physical_constructor(tmp_path)
    growth = next(
        slot for slot in result["slots"]
        if slot["slot_id"] == "net_positive_growth"
    )
    assert growth["direct_receipt_count"] == 15
    assert len(growth["direct_receipts"]) == 15
