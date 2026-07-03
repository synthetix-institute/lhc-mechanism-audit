# Equation Mechanism Graph

This report uses Hyperion operator/substrate fingerprints, not claim provenance, as the primary evidence layer.
Text role labels are retained only as weak annotations.

## Scale

- source equation witnesses: `1408`
- fingerprinted mechanism nodes: `1408`
- usable non-artifact mechanism nodes: `204`
- LHC-black-hole case-relevant mechanism nodes: `72`
- evidence-grade case mechanism nodes: `35`
- direct LHC-safety mechanism nodes: `0`
- astrophysical analogue mechanism nodes: `28`
- collider-threshold/selection mechanism nodes: `1`
- artifact or unusable nodes retained for audit: `1200`
- source-local route-transition edges: `120`
- case-relevant source-local route-transition edges: `44`
- rich cross-source route analogues: `130`
- case-internal rich analogues: `24`
- case-transfer rich analogues: `51`
- evidence-grade case-internal rich analogues: `5`
- evidence-grade case-transfer rich analogues: `49`

## Main Finding

This corpus does not contain formula-clean direct LHC-safety mechanisms under the current gates. It contains one collider-threshold/selection hook and a larger set of astrophysical black-hole mechanisms. The evidence therefore supports a mechanism-translation audit: use accretion, evaporation, capture, mass-growth and compact-object survival mechanisms as constraints on the collider branch, rather than treating the problem as a provenance dispute over who said safe or dangerous.

## Six-Route Evidence

Counts below use only non-artifact constructor pairs.

- `constraint_closure`: `165` nodes — balance, normalization, residual, conservation or closure condition.
- `spectral_operator`: `160` nodes — operator, generator, mode, eigenvalue, expectation or spectral readout.
- `transport_flow`: `95` nodes — state change, flux, rate, propagation or dynamical update.
- `boundary_weak_form`: `28` nodes — domain, interface, boundary, weak/test form or realization condition.
- `discrete_protocol`: `24` nodes — algorithmic, measurement, recurrence, intervention or ordered update protocol.
- `commutator_incompatibility`: `12` nodes — non-commutation, incompatibility, bracket or order dependence.

## Dominant Route Signatures

- `constraint_closure + transport_flow + spectral_operator`: `40`
- `constraint_closure + spectral_operator`: `36`
- `constraint_closure + spectral_operator + transport_flow`: `24`
- `constraint_closure`: `20`
- `spectral_operator`: `10`
- `discrete_protocol + boundary_weak_form`: `9`
- `transport_flow + constraint_closure + spectral_operator`: `8`
- `constraint_closure + spectral_operator + boundary_weak_form + transport_flow`: `5`
- `discrete_protocol`: `5`
- `spectral_operator + transport_flow`: `5`
- `transport_flow + spectral_operator`: `4`
- `constraint_closure + boundary_weak_form`: `3`

## Case-Relevant Mechanism Evidence

This gate asks whether a formula-clean mechanism node is locally attached to the LHC black-hole safety case. Source-level words can support relevance, but they do not create route evidence.
Evidence-grade receipts require the formula window itself to contain the black-hole case and a mechanism category; source-level relevance alone is not enough.

- `black_hole`: `72`
- `astrophysical_bound`: `51`
- `accretion_growth`: `49`
- `evaporation_branch`: `24`
- `capture_stopping`: `14`
- `collider_threshold`: `10`
- `safety_risk`: `2`

Evidence-grade branch counts:

- `stable_growth_or_capture_branch`: `29`
- `astrophysical_black_hole_analogue`: `28`
- `evaporation_branch`: `12`
- `production_threshold_branch`: `1`

Interpretation:

If direct LHC-safety receipts are sparse while astrophysical black-hole analogues are present, the result should not be read as a failure of the mechanism graph. It means the inspectable scientific substrate is mostly adjacent physics: accretion, evaporation, capture, mass growth and astrophysical survival bounds. The safety argument must therefore be audited by translating those mechanisms into the collider branch, rather than by counting who asserted safety or danger.
Collider-threshold/selection candidates are separated because they can show where a collider event selection or formation condition enters the case, but they are not by themselves accretion, evaporation or safety mechanisms.

## Constructor Frame Quality

- `partial_constructor_pair`: `744`
- `artifact_or_fragment_pair`: `469`
- `equation_shape_or_unclassified_pair`: `168`
- `complete_constructor_pair`: `27`

## Formula-Core Quality

- `prose_or_latex_artifact`: `947`
- `no_relation_operator`: `689`
- `word_heavy_formula`: `372`
- `formula_core`: `299`
- `sentence_boundary_inside_formula`: `272`
- `long_prose_fragment`: `6`

## Constructor Roles Present

- `operator_apparatus`: `142`
- `selector`: `106`
- `real_substrate_geometry`: `94`
- `closure_constraints`: `68`
- `readout_current`: `45`
- `protocol_order`: `25`

## Frequent Transition Labels

- `preserve_operator_apparatus`: `49`
- `add_selector`: `47`
- `add_closure_constraints`: `44`
- `add_operator_apparatus`: `42`
- `add_real_substrate_geometry`: `32`
- `project_operator_apparatus`: `29`
- `project_selector`: `28`
- `project_real_substrate_geometry`: `23`
- `preserve_selector`: `20`
- `add_readout_current`: `18`
- `preserve_real_substrate_geometry`: `16`
- `modify_real_substrate_geometry`: `14`
- `modify_operator_apparatus`: `13`
- `project_readout_current`: `13`
- `preserve_readout_current`: `12`
- `preserve_closure_constraints`: `11`
- `project_closure_constraints`: `11`
- `project_protocol_order`: `9`
- `preserve_protocol_order`: `8`
- `add_protocol_order`: `5`

## Global Cross-Source Route Analogues

These route analogues are formula-clean but not necessarily LHC-case-specific.

- `0709.3372` -> `0807.3458`: `constraint_closure + spectral_operator + transport_flow`, cosine `1.000`
- `0709.3372` -> `1011.4793`: `constraint_closure + spectral_operator + transport_flow`, cosine `1.000`
- `0709.3372` -> `1111.1677`: `constraint_closure + spectral_operator + transport_flow`, cosine `1.000`
- `0709.3372` -> `1201.5525`: `constraint_closure + spectral_operator + transport_flow`, cosine `1.000`
- `0709.3372` -> `1207.1244`: `constraint_closure + spectral_operator + transport_flow`, cosine `1.000`
- `0709.3372` -> `1211.0547`: `constraint_closure + spectral_operator + transport_flow`, cosine `1.000`
- `0709.3372` -> `1310.5857`: `constraint_closure + spectral_operator + transport_flow`, cosine `1.000`
- `0807.3458` -> `1011.4793`: `constraint_closure + spectral_operator + transport_flow`, cosine `1.000`
- `0807.3458` -> `1111.1677`: `constraint_closure + spectral_operator + transport_flow`, cosine `1.000`
- `0807.3458` -> `1201.5525`: `constraint_closure + spectral_operator + transport_flow`, cosine `1.000`
- `0807.3458` -> `1207.1244`: `constraint_closure + spectral_operator + transport_flow`, cosine `1.000`
- `0807.3458` -> `1211.0547`: `constraint_closure + spectral_operator + transport_flow`, cosine `1.000`
- `0807.3458` -> `1310.5857`: `constraint_closure + spectral_operator + transport_flow`, cosine `1.000`
- `1011.4793` -> `1111.1677`: `constraint_closure + spectral_operator + transport_flow`, cosine `1.000`
- `1011.4793` -> `1201.5525`: `constraint_closure + spectral_operator + transport_flow`, cosine `1.000`
- `1011.4793` -> `1207.1244`: `constraint_closure + spectral_operator + transport_flow`, cosine `1.000`
- `1011.4793` -> `1211.0547`: `constraint_closure + spectral_operator + transport_flow`, cosine `1.000`
- `1011.4793` -> `1310.5857`: `constraint_closure + spectral_operator + transport_flow`, cosine `1.000`
- `1111.1677` -> `1201.5525`: `constraint_closure + spectral_operator + transport_flow`, cosine `1.000`
- `1111.1677` -> `1207.1244`: `constraint_closure + spectral_operator + transport_flow`, cosine `1.000`
- ... `110` additional cross-source analogues omitted.

## Case-Relevant Cross-Source Route Analogues

Internal to the LHC black-hole case:

- `0807.3458` -> `astro-ph0105365`: `transport_flow + constraint_closure + spectral_operator`, cosine `1.000`
- `0807.3458` -> `astro-ph0510698`: `transport_flow + constraint_closure + spectral_operator`, cosine `1.000`
- `astro-ph0105365` -> `astro-ph0510698`: `transport_flow + constraint_closure + spectral_operator`, cosine `1.000`
- `0811.2129` -> `1111.1677`: `constraint_closure + spectral_operator`, cosine `1.000`
- `1109.6593` -> `1502.04146`: `constraint_closure + spectral_operator + boundary_weak_form + transport_flow`, cosine `0.992`

Transfer analogues from the case to other formula-clean sources:

- `0709.3372` -> `1111.1677`: `constraint_closure + spectral_operator + transport_flow`, cosine `1.000`
- `0807.3458` -> `1111.1677`: `constraint_closure + spectral_operator + transport_flow`, cosine `1.000`
- `1011.4793` -> `1111.1677`: `constraint_closure + spectral_operator + transport_flow`, cosine `1.000`
- `1111.1677` -> `1201.5525`: `constraint_closure + spectral_operator + transport_flow`, cosine `1.000`
- `1111.1677` -> `1207.1244`: `constraint_closure + spectral_operator + transport_flow`, cosine `1.000`
- `1111.1677` -> `1211.0547`: `constraint_closure + spectral_operator + transport_flow`, cosine `1.000`
- `1111.1677` -> `1310.5857`: `constraint_closure + spectral_operator + transport_flow`, cosine `1.000`
- `0804.0708` -> `1505.05756`: `transport_flow + spectral_operator`, cosine `1.000`
- `1201.5525` -> `1505.05756`: `transport_flow + spectral_operator`, cosine `1.000`
- `1207.1244` -> `1505.05756`: `transport_flow + spectral_operator`, cosine `1.000`
- `0807.3458` -> `0811.1473`: `transport_flow + constraint_closure + spectral_operator`, cosine `1.000`
- `0807.3458` -> `1508.04780`: `transport_flow + constraint_closure + spectral_operator`, cosine `1.000`

## Case-Relevant Mechanism Examples

### Direct LHC-Safety Receipts

No formula-clean direct LHC-safety mechanism passed the current gate.
This is the substantive result: the selected corpus supports an indirect mechanism audit through adjacent black-hole physics.

### Collider-Threshold/Selection Candidates

### `0904.0230` / `E00053`

- route signature: `constraint_closure + boundary_weak_form`
- route evidence: boundary_weak_form=0.26, constraint_closure=0.45
- constructor roles: `real_substrate_geometry, selector`
- pair status: `partial_constructor_pair`
- case score: `7`
- formula-window case categories: `black_hole, collider_threshold`
- source case categories: `none`
- branch labels: `production_threshold_branch`
- formula detail score: `4`

Formula:

```text
|y_{\gamma \gamma}| \leq 1
```

### Astrophysical Black-Hole Analogues

### `0807.3458` / `E00034`

- route signature: `transport_flow + constraint_closure + spectral_operator`
- route evidence: transport_flow=0.75, spectral_operator=0.25, constraint_closure=0.45
- constructor roles: `operator_apparatus, readout_current, real_substrate_geometry`
- pair status: `complete_constructor_pair`
- case score: `13`
- formula-window case categories: `accretion_growth, astrophysical_bound, black_hole, evaporation_branch`
- source case categories: `none`
- branch labels: `astrophysical_black_hole_analogue, evaporation_branch, stable_growth_or_capture_branch`
- formula detail score: `11`

Formula:

```text
3 \times 10^{-13}~\mathrm{M}_{\odot}~\mathrm{yr}^{-1} \lesssim \langle \dot{M}_{\mathrm{long}} \rangle \lesssim 1 \times 10^{-10}~\mathrm{M}_{\odot}~\mathrm{yr}^{-1}
```

### `0807.3458` / `E00035`

- route signature: `transport_flow + constraint_closure + spectral_operator`
- route evidence: transport_flow=0.75, spectral_operator=0.25, constraint_closure=0.45
- constructor roles: `operator_apparatus, readout_current, real_substrate_geometry`
- pair status: `complete_constructor_pair`
- case score: `13`
- formula-window case categories: `accretion_growth, astrophysical_bound, black_hole, evaporation_branch`
- source case categories: `none`
- branch labels: `astrophysical_black_hole_analogue, evaporation_branch, stable_growth_or_capture_branch`
- formula detail score: `11`

Formula:

```text
4 \times 10^{-14}~\mathrm{M}_{\odot}~\mathrm{yr}^{-1} \lesssim \langle \dot{M}_{\mathrm{long}} \rangle \lesssim 2 \times 10^{-11}~\mathrm{M}_{\odot}~\mathrm{yr}^{-1}
```

### `astro-ph0212297` / `E01142`

- route signature: `constraint_closure + transport_flow + spectral_operator`
- route evidence: transport_flow=0.26, constraint_closure=0.45, spectral_operator=0.25
- constructor roles: `operator_apparatus, selector`
- pair status: `partial_constructor_pair`
- case score: `13`
- formula-window case categories: `accretion_growth, astrophysical_bound, black_hole, evaporation_branch`
- source case categories: `none`
- branch labels: `astrophysical_black_hole_analogue, evaporation_branch, stable_growth_or_capture_branch`
- formula detail score: `8`

Formula:

```text
B_c\simeq 10^{16}\mbox{G}\left({7M_\odot}/{M_H}\right) \left({6M_H}/{R}\right)^2\left({M_T}/{0.03M_H}\right)^{1/2}
```

### `1307.7685` / `E00825`

- route signature: `constraint_closure + transport_flow + spectral_operator`
- route evidence: transport_flow=0.26, constraint_closure=0.45, spectral_operator=0.25
- constructor roles: `operator_apparatus, real_substrate_geometry, selector`
- pair status: `partial_constructor_pair`
- case score: `11`
- formula-window case categories: `accretion_growth, astrophysical_bound, black_hole`
- source case categories: `none`
- branch labels: `astrophysical_black_hole_analogue, stable_growth_or_capture_branch`
- formula detail score: `7`

Formula:

```text
\delta M_{BH}< 5 \times 10^{-4}M_{BH}
```

### `1207.1244` / `E00797`

- route signature: `constraint_closure + transport_flow + spectral_operator + discrete_protocol`
- route evidence: transport_flow=0.26, constraint_closure=0.45, discrete_protocol=0.17, spectral_operator=0.25
- constructor roles: `closure_constraints, operator_apparatus, protocol_order, real_substrate_geometry`
- pair status: `partial_constructor_pair`
- case score: `7`
- formula-window case categories: `astrophysical_bound, black_hole`
- source case categories: `none`
- branch labels: `astrophysical_black_hole_analogue`
- formula detail score: `7`

Formula:

```text
M_1 = 0.9_{-0.3}^{+4.6} M_\odot
```

### `1604.02455` / `E01020`

- route signature: `constraint_closure + transport_flow + spectral_operator`
- route evidence: transport_flow=0.43, constraint_closure=0.45, spectral_operator=0.25
- constructor roles: `operator_apparatus, real_substrate_geometry, selector`
- pair status: `partial_constructor_pair`
- case score: `14`
- formula-window case categories: `accretion_growth, astrophysical_bound, black_hole, evaporation_branch`
- source case categories: `astrophysical_bound`
- branch labels: `astrophysical_black_hole_analogue, evaporation_branch, stable_growth_or_capture_branch`
- formula detail score: `6`

Formula:

```text
4000M \sim 60(M_{\rm NS/1.625M_\odot)
```

### `1604.02455` / `E01021`

- route signature: `constraint_closure + transport_flow + spectral_operator`
- route evidence: transport_flow=0.43, constraint_closure=0.45, spectral_operator=0.25
- constructor roles: `operator_apparatus, real_substrate_geometry, selector`
- pair status: `partial_constructor_pair`
- case score: `14`
- formula-window case categories: `accretion_growth, astrophysical_bound, black_hole, evaporation_branch`
- source case categories: `astrophysical_bound`
- branch labels: `astrophysical_black_hole_analogue, evaporation_branch, stable_growth_or_capture_branch`
- formula detail score: `6`

Formula:

```text
\Delta t \sim 0.1 (M_{\rm NS/1.625M_\odot)
```

### `astro-ph0212297` / `E01141`

- route signature: `constraint_closure + spectral_operator + transport_flow`
- route evidence: transport_flow=0.17, constraint_closure=0.45, spectral_operator=0.25
- constructor roles: `operator_apparatus`
- pair status: `partial_constructor_pair`
- case score: `13`
- formula-window case categories: `accretion_growth, astrophysical_bound, black_hole, evaporation_branch`
- source case categories: `none`
- branch labels: `astrophysical_black_hole_analogue, evaporation_branch, stable_growth_or_capture_branch`
- formula detail score: `6`

Formula:

```text
{\cal E_B}/{{\cal E}_k}<0.1
```

- ... `20` additional examples omitted.

### Other Evidence-Grade Case Nodes

### `astro-ph0109539` / `E01098`

- route signature: `constraint_closure + spectral_operator + transport_flow`
- route evidence: transport_flow=0.17, spectral_operator=0.25, constraint_closure=0.45
- constructor roles: `operator_apparatus, readout_current, real_substrate_geometry`
- pair status: `partial_constructor_pair`
- case score: `8`
- formula-window case categories: `accretion_growth, black_hole`
- source case categories: `accretion_growth`
- branch labels: `stable_growth_or_capture_branch`
- formula detail score: `8`

Formula:

```text
\langle M\rangle \sim 9 {M}_\odot
```

### `1503.07522` / `E00932`

- route signature: `spectral_operator + transport_flow`
- route evidence: transport_flow=0.17, spectral_operator=0.25
- constructor roles: `operator_apparatus, real_substrate_geometry`
- pair status: `partial_constructor_pair`
- case score: `7`
- formula-window case categories: `accretion_growth, black_hole`
- source case categories: `none`
- branch labels: `stable_growth_or_capture_branch`
- formula detail score: `6`

Formula:

```text
\mu_4\equiv(\mathrm{dm/M_\odot)/(\mathrm{dr/1000\,\mathrm{km)|_{s=4
```

### `astro-ph0206011` / `E01119`

- route signature: `constraint_closure + spectral_operator + transport_flow`
- route evidence: transport_flow=0.17, constraint_closure=0.45, spectral_operator=0.25
- constructor roles: `operator_apparatus`
- pair status: `partial_constructor_pair`
- case score: `7`
- formula-window case categories: `accretion_growth, black_hole`
- source case categories: `none`
- branch labels: `stable_growth_or_capture_branch`
- formula detail score: `6`

Formula:

```text
L_{\nu \overline{\nu}} \propto t^{-5/2}
```

### `astro-ph0105365` / `E01083`

- route signature: `transport_flow + constraint_closure + spectral_operator`
- route evidence: transport_flow=0.75, constraint_closure=0.45, spectral_operator=0.25
- constructor roles: `operator_apparatus, selector`
- pair status: `partial_constructor_pair`
- case score: `10`
- formula-window case categories: `accretion_growth, black_hole, capture_stopping`
- source case categories: `accretion_growth`
- branch labels: `stable_growth_or_capture_branch`
- formula detail score: `5`

Formula:

```text
\dot M \sim (R_{in}/R_a)\dot M_{Bondi}
```

### `astro-ph0105046` / `E01079`

- route signature: `constraint_closure + spectral_operator`
- route evidence: constraint_closure=0.45, spectral_operator=0.25
- constructor roles: `operator_apparatus, readout_current, real_substrate_geometry, selector`
- pair status: `partial_constructor_pair`
- case score: `8`
- formula-window case categories: `accretion_growth, black_hole`
- source case categories: `accretion_growth`
- branch labels: `stable_growth_or_capture_branch`
- formula detail score: `5`

Formula:

```text
\epsilon_{BH} \simeq 10^{-3}
```

### `astro-ph0212297` / `E01146`

- route signature: `constraint_closure + spectral_operator`
- route evidence: constraint_closure=0.45, spectral_operator=0.25
- constructor roles: `operator_apparatus`
- pair status: `partial_constructor_pair`
- case score: `7`
- formula-window case categories: `accretion_growth, black_hole`
- source case categories: `none`
- branch labels: `stable_growth_or_capture_branch`
- formula detail score: `4`

Formula:

```text
E_j/E_{rot}\simeq 10^{-3}
```

## Global Mechanism Examples

These are formula-clean global examples from the operational graph, not LHC-specific receipts.

### `0807.3458` / `E00034`

- route signature: `transport_flow + constraint_closure + spectral_operator`
- route evidence: transport_flow=0.75, spectral_operator=0.25, constraint_closure=0.45
- constructor roles: `operator_apparatus, readout_current, real_substrate_geometry`
- pair status: `complete_constructor_pair`

Formula:

```text
3 \times 10^{-13}~\mathrm{M}_{\odot}~\mathrm{yr}^{-1} \lesssim \langle \dot{M}_{\mathrm{long}} \rangle \lesssim 1 \times 10^{-10}~\mathrm{M}_{\odot}~\mathrm{yr}^{-1}
```

### `0807.3458` / `E00035`

- route signature: `transport_flow + constraint_closure + spectral_operator`
- route evidence: transport_flow=0.75, spectral_operator=0.25, constraint_closure=0.45
- constructor roles: `operator_apparatus, readout_current, real_substrate_geometry`
- pair status: `complete_constructor_pair`

Formula:

```text
4 \times 10^{-14}~\mathrm{M}_{\odot}~\mathrm{yr}^{-1} \lesssim \langle \dot{M}_{\mathrm{long}} \rangle \lesssim 2 \times 10^{-11}~\mathrm{M}_{\odot}~\mathrm{yr}^{-1}
```

### `1201.5525` / `E00398`

- route signature: `boundary_weak_form + constraint_closure + spectral_operator`
- route evidence: spectral_operator=0.25, constraint_closure=0.35, boundary_weak_form=0.35
- constructor roles: `closure_constraints, protocol_order, readout_current, real_substrate_geometry, selector`
- pair status: `partial_constructor_pair`

Formula:

```text
\tilde{m}^2_{ij} &= m_{3/2}^2 \tilde{K}_{ij} - F_{\bar{n}}\, F_m\, \partial_{\bar{n}}\, \partial_m\, \tilde{K} \;, & A_{ijk} &= A_0\, Y_{ijk} + F_m\, \partial_m\, Y_{ijk} \;,
```

### `1201.5525` / `E00300`

- route signature: `spectral_operator + constraint_closure + transport_flow`
- route evidence: transport_flow=0.33, spectral_operator=0.55, constraint_closure=0.45
- constructor roles: `operator_apparatus, readout_current, real_substrate_geometry, selector`
- pair status: `partial_constructor_pair`

Formula:

```text
-\mathcal{L}_{L}&= h_{1} \overline{L}_1 \left(\nu_R \Phi\right)'_1 +h_{2} \overline{L}_2 \left(\nu_R \Phi\right)_1 +h_{3} \overline{L}_3 \left(\nu_R \Phi\right)''_1 +\lambda L_{1}^{T}C\Delta L_{2}+ \lambda L_{2}^{T}C\Delta L_{1}\nonumber\\ &+ \lambda^{\prime} L_{3}^{T}C\Delta L_{3} + M_R \left(\overline{S_L} \nu_R\right)_1 + h \left(S^T_L C S_L\right)'_1\sigma+\hbox{h.c.}\,,
```

### `1201.5525` / `E00315`

- route signature: `spectral_operator + constraint_closure + transport_flow`
- route evidence: transport_flow=0.17, spectral_operator=0.55, constraint_closure=0.45
- constructor roles: `operator_apparatus, readout_current, real_substrate_geometry, selector`
- pair status: `partial_constructor_pair`

Formula:

```text
\mathcal{M}^{II}_{\nu}=2u_{\Delta}\left( \begin{array}{ccc} 0 &\lambda & 0\\[+2mm] \lambda & 0 & 0\\[+2mm] 0 & 0 & \lambda^{\prime} \end{array} \right)\,,
```

### `1201.5525` / `E00370`

- route signature: `constraint_closure + commutator_incompatibility + transport_flow + spectral_operator`
- route evidence: transport_flow=0.33, commutator_incompatibility=0.33, constraint_closure=0.45, spectral_operator=0.25
- constructor roles: `closure_constraints, operator_apparatus, readout_current, real_substrate_geometry, selector`
- pair status: `complete_constructor_pair`

Formula:

```text
\widetilde\epsilon_Q \, \widetilde\epsilon_u \sim \epsilon_u^2 \quad,\quad \widetilde\epsilon_Q \, \widetilde\epsilon_d \sim \epsilon_d^2 \quad,\quad \widetilde\epsilon_L \, \widetilde\epsilon_e \sim \epsilon_d^2 \;.
```

### `1201.5525` / `E00371`

- route signature: `constraint_closure + commutator_incompatibility + transport_flow + spectral_operator`
- route evidence: transport_flow=0.33, commutator_incompatibility=0.33, constraint_closure=0.45, spectral_operator=0.25
- constructor roles: `closure_constraints, operator_apparatus, readout_current, real_substrate_geometry, selector`
- pair status: `complete_constructor_pair`

Formula:

```text
\widetilde m^2_f \sim m^2_0 \begin{pmatrix} 1 & \widetilde\epsilon_f^{\,2} \, \epsilon_d^2 & \widetilde\epsilon_f^{\,2} \, \epsilon_d^2 \\ \cdot & 1 + \widetilde\epsilon_f^{\,2} & \widetilde\epsilon_f^{\,2} \\ \cdot & \cdot & 1 \end{pmatrix} \quad,\quad f = u,\, d,\, Q,\, e,\, L
```

### `1201.5525` / `E00460`

- route signature: `spectral_operator + constraint_closure + transport_flow + commutator_incompatibility`
- route evidence: transport_flow=0.33, spectral_operator=0.55, commutator_incompatibility=0.17, constraint_closure=0.45
- constructor roles: `operator_apparatus, readout_current, real_substrate_geometry, selector`
- pair status: `complete_constructor_pair`

Formula:

```text
{W}_\nu = \frac{y_{s}}{\sqrt{\Lambda^2 V}} \psi \bar{\Delta}_2 S_\nu + \frac{1}{\sqrt{\Lambda^2 V}} \left(y^\nu_\phi\phi_{1,1,1} +y^{\nu}_\xi \xi\right) S_{\nu} S_{\nu} \;.
```

### `1201.5525` / `E00372`

- route signature: `constraint_closure + spectral_operator + boundary_weak_form`
- route evidence: boundary_weak_form=0.17, constraint_closure=0.35, spectral_operator=0.25
- constructor roles: `closure_constraints, operator_apparatus, readout_current, real_substrate_geometry, selector`
- pair status: `partial_constructor_pair`

Formula:

```text
\widetilde\epsilon_Q = \widetilde\epsilon_d = \widetilde\epsilon_L = \widetilde\epsilon_e = \epsilon_d \approx 0.15 \quad,\quad \widetilde\epsilon_u = \epsilon_u^2/\epsilon_d \approx 0.02 \;.
```

### `1205.2671` / `E00724`

- route signature: `commutator_incompatibility + constraint_closure + discrete_protocol + spectral_operator`
- route evidence: constraint_closure=0.45, commutator_incompatibility=0.55, discrete_protocol=0.45, spectral_operator=0.25
- constructor roles: `operator_apparatus, protocol_order, real_substrate_geometry, selector`
- pair status: `partial_constructor_pair`

Formula:

```text
A_{PV} = \left[- G_F Q^2 \over 4 \pi \alpha \sqrt{2}\right] \left[ Q_{W}^{p} + F^{p}(Q^{2},\theta,E) \right] \rightarrow \left[- G_F Q^2 \over 4 \pi \alpha \sqrt{2}\right] \left[ Q_{W}^{p} + Q^{2} B(Q^{2})+C(E)\right]\,,
```

### `1201.5525` / `E00461`

- route signature: `spectral_operator + constraint_closure + commutator_incompatibility + transport_flow`
- route evidence: transport_flow=0.26, spectral_operator=0.55, commutator_incompatibility=0.33, constraint_closure=0.45
- constructor roles: `operator_apparatus, readout_current, real_substrate_geometry, selector`
- pair status: `partial_constructor_pair`

Formula:

```text
M_{\nu} = - \frac{1}{\Lambda^2 V} (y_s \left<\bar\Delta_2\right>) (M_{SS}^{-1}) (y_s \left<\bar\Delta_2\right>)^T = - m_0 U^*_\mathrm{tbm} \begin{pmatrix} \frac{1}{3a+b} & 0 & 0 \\ . & \frac{1}{b} & 0 \\ . & . & \frac{1}{3a-b} \end{pmatrix} U^\dagger_\mathrm{tbm}\;.
```

### `1201.5525` / `E00191`

- route signature: `constraint_closure + transport_flow + spectral_operator`
- route evidence: transport_flow=0.45, constraint_closure=0.45, spectral_operator=0.25
- constructor roles: `operator_apparatus, real_substrate_geometry, selector`
- pair status: `partial_constructor_pair`

Formula:

```text
\frac{dR}{dE_E}=\frac{\rho_{DM}}{m_{DM} m_N}\int_{|\vec{v}|>v_{min}}d^3v \frac{d\sigma}{dE_R} v f(\vec{v})
```

- ... `192` additional examples omitted.

## Boundary

This graph does not prove physical equivalence. It separates equation-level mechanism evidence from provenance and word-level selection, making route analogies inspectable.
