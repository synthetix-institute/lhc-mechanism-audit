# Provenance and Equation Mechanisms

Provenance resolves responsibility and documentary dependence. The mechanism graph resolves which equations instantiate each physical condition and whether those equations compose in source order.

## Provenance graph

- `paper` nodes: `496`
- `author` nodes: `15`
- `external_reference` nodes: `327`
- `claim` nodes: `708`
- `source_makes_claim` edges: `708`
- `author_wrote_paper` edges: `16`
- `paper_cites_paper` edges: `369`

## Equation graph

- strict equation receipts: `36`
- attended graph edges: `91`

## Physical constructor

- branch: `incomplete_direct_mechanism_branch`
- direct conditions: `5/6`
- missing source-local transitions: `4`

| Condition | Status | Direct equations | Transfer candidates |
|---|---:|---:|---:|
| production threshold | `direct_mechanism_receipt` | 3 | 0 |
| survival against evaporation | `direct_mechanism_receipt` | 3 | 0 |
| stopping or capture in matter | `direct_mechanism_receipt` | 5 | 2 |
| net positive mass growth | `direct_mechanism_receipt` | 11 | 10 |
| growth on a relevant timescale | `direct_mechanism_receipt` | 1 | 3 |
| evasion of astronomical survival bounds | `candidate_transfer_only` | 0 | 1 |

## Findings

- The provenance layer contains 496 papers, 708 claims and 369 citation links.
- Strict formula contracts recover 36 equation nodes; 91 graph edges connect at least one such receipt.
- The physical constructor fills 5 of 6 conditions with direct collider equations and leaves 4 adjacent mechanism transitions without a source-local derivation path.
