# Sparse Attention Audit

This audit reads the static equation mechanism graph and measures which mechanism routes co-activate in the LHC black-hole case layer.

## Scale

- usable mechanism nodes: `204`
- evidence-grade case nodes: `35`

## Findings

- Sparse attention supports the main audit finding: direct collider-safety mechanisms are absent under the strict gate, while adjacent astrophysical black-hole mechanisms are present.
- Collider-threshold evidence appears as a separate branch from accretion, evaporation and capture mechanisms.
- Evidence-grade case nodes concentrate on spectral_operator (34), constraint_closure (33), transport_flow (25), consistent with mechanism translation rather than claim provenance.
- Astrophysical analogues are routed mainly through spectral_operator (28), constraint_closure (27), transport_flow (21), boundary_weak_form (3).

## Evidence-Grade Route Counts

- `spectral_operator`: `34`
- `constraint_closure`: `33`
- `transport_flow`: `25`
- `boundary_weak_form`: `4`
- `discrete_protocol`: `1`

## Branch To Route Attention

- `astrophysical_black_hole_analogue`: spectral_operator=0.35, constraint_closure=0.34, transport_flow=0.26, boundary_weak_form=0.04, discrete_protocol=0.01
- `evaporation_branch`: constraint_closure=0.32, spectral_operator=0.32, transport_flow=0.30, boundary_weak_form=0.05
- `stable_growth_or_capture_branch`: spectral_operator=0.36, constraint_closure=0.34, transport_flow=0.29, boundary_weak_form=0.01
- `production_threshold_branch`: constraint_closure=0.50, boundary_weak_form=0.50

## Route Co-Attention

- `constraint_closure` + `spectral_operator`: `32`
- `spectral_operator` + `transport_flow`: `25`
- `constraint_closure` + `transport_flow`: `23`
- `boundary_weak_form` + `constraint_closure`: `4`
- `boundary_weak_form` + `spectral_operator`: `3`
- `boundary_weak_form` + `transport_flow`: `2`
- `discrete_protocol` + `transport_flow`: `1`
- `constraint_closure` + `discrete_protocol`: `1`
- `discrete_protocol` + `spectral_operator`: `1`

## Boundary

This is a sparse co-activation audit over static public graph artifacts. It supports report interpretation; it does not create new Hyperion fingerprints or claim physical equivalence.
