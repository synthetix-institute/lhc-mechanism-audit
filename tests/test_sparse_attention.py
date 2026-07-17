from __future__ import annotations

import pytest

from lhc_audit.sparse_attention import build_graph_sparse_attention


def test_sparse_attention_uses_edges_and_normalizes_scores():
    nodes = [
        {
            "id": "E0",
            "source_id": "p0",
            "formula": r"\tau=x_1x_2>\tau_{min}=M_{min}^2/s",
            "context": "LHC microscopic black hole collider",
            "route_profile": {"constraint_closure": 0.9},
        },
        {
            "id": "E1",
            "source_id": "p0",
            "formula": r"\frac{dM}{dt}\approx-P_{evap}<0",
            "context": "LHC microscopic black hole collider",
            "route_profile": {"transport_flow": 0.9, "constraint_closure": 0.4},
        },
        {
            "id": "E2",
            "source_id": "p1",
            "formula": r"A\psi=\lambda\psi",
            "context": "spectral problem",
            "route_profile": {"spectral_operator": 0.9},
        },
    ]
    graph = {
        "nodes": nodes,
        "usable_node_ids": ["E0", "E1", "E2"],
        "edges": [
            {"source": "E0", "target": "E1", "source_id": "p0", "edge_type": "source_local_route_transition"},
            {"source": "E0", "target": "E2", "source_id": "p0", "edge_type": "source_local_route_transition"},
        ],
        "analog_edges": [],
    }
    result = build_graph_sparse_attention(graph)
    assert result["strict_receipt_node_count"] == 2
    assert result["attended_edge_count"] == 2
    assert sum(edge["attention"] for edge in result["top_edges"]) == pytest.approx(1.0)
    assert result["route_prevalence"]["constraint_closure"] == 2
