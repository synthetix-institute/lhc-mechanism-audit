# Discourse-vs-Mechanism Sparse Attention

## Result

A discourse graph ranks who said what. A mechanism graph tests whether equations can be assembled into the required physical branch. In this run the two layers diverge: claims exist, but the equation constructor stops after the production hook.

## Discourse Graph

- paper nodes: `492`
- claim nodes: `377`
- source-to-claim edges: `377`

Claim attention:
- `astrophysical_claim`: `0.942`
- `risk_claim`: `0.053`
- `safety_claim`: `0.005`

## Mechanism Graph

- fingerprinted equation windows: `1408`
- usable equation nodes: `204`
- case-relevant nodes: `72`
- evidence-grade receipts: `35`

Route attention:
- `spectral_operator`: `0.351`
- `constraint_closure`: `0.340`
- `transport_flow`: `0.258`
- `boundary_weak_form`: `0.041`
- `discrete_protocol`: `0.010`

## Constructor

- branch verdict: `broken_danger_branch`
- required downstream slots: `5`
- direct downstream slots: `0`
- transfer-only downstream slots: `5`
- missing downstream slots: `0`

| Slot | Status | Direct receipts | Transfer receipts |
|---|---:|---:|---:|
| production threshold | `direct_hook` | 1 | 0 |
| survival against evaporation | `transfer_only` | 0 | 6 |
| stopping or capture in matter | `transfer_only` | 0 | 1 |
| net positive mass growth | `transfer_only` | 0 | 29 |
| growth on a relevant timescale | `transfer_only` | 0 | 11 |
| evasion of astronomical survival bounds | `transfer_only` | 0 | 28 |

## Findings

- The discourse graph resolves the literature as papers linked to claim families. It shows where statements occur, but it has no variable for survival, capture, growth, or astronomical-bound closure.
- The mechanism graph resolves the same source set as formula receipts placed into physical slots. That layer finds one direct collider production hook and no direct downstream collider closure.
- Sparse route attention concentrates on spectral/operator, closure, and transport roles. Those are exactly the operations needed to test threshold, lifetime, capture, and growth.
- The decisive result is structural: downstream evidence is transfer evidence from astrophysics, not a closed collider catastrophe branch.
