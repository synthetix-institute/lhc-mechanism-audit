# LHC Mechanism Audit

This repository builds a static, inspectable report on one scientific question:

> Do the processed arXiv papers support a dangerous LHC black-hole scenario?

The answer in the committed report is **no**: the retained equation evidence
does not contain a closed collider-danger branch. It contains a collider
production hook and many adjacent astrophysical black-hole mechanisms, but the
downstream links needed for a dangerous LHC scenario remain unfilled: survival
after production, stopping or capture in matter, positive microscopic mass
growth and evasion of astronomical survival bounds.

This is not a seed-paper demonstration. The static run in this repository is a
public export from a Hyperion pass over arXiv/Hugging Face LaTeX data. The
committed report uses **492 selected papers** from the arXiv corpus parsed by
Hyperion, yielding **1,408 equation witnesses** and a retained
operator/substrate mechanism layer. The six seed papers remain in the
repository only as references for the historical LHC-safety debate and for small
smoke tests.

The report compares two evidence layers:

1. **Provenance graph:** papers connected to extracted claim families. This
   layer shows who says what kind of thing: astrophysical black-hole statements,
   risk statements and safety statements.
2. **Mechanism graph:** fingerprinted equation windows connected to physical
   roles such as production, evaporation, capture, growth and astronomical
   bounds. This layer tests whether the equations close into a continuous
   physical branch.

The conclusion is obtained from the second layer. A dangerous branch requires
production in a parton collision, survival against evaporation, stopping or
capture in matter, net positive growth and consistency with astronomical
survival constraints.

## Main Result

The static run contains:

- 492 selected papers from the arXiv/HF LaTeX corpus parsed by Hyperion;
- 377 extracted source-to-claim records in the provenance layer;
- 1,408 equation witnesses;
- 204 usable mechanism nodes after fingerprint and formula-quality gates;
- 72 LHC-black-hole-relevant mechanism nodes;
- 35 evidence-grade case receipts;
- 0 direct LHC-safety mechanism nodes under the retained gates.

The physical constructor has six required slots. The retained evidence fills the
first slot directly and the downstream slots only by transfer from adjacent
astrophysical mechanisms:

| Constructor slot | Direct collider receipts | Transfer receipts | Status |
| --- | ---: | ---: | --- |
| production threshold | 1 | 0 | direct hook |
| survival against evaporation | 0 | 6 | transfer only |
| stopping or capture in matter | 0 | 1 | transfer only |
| net positive mass growth | 0 | 29 | transfer only |
| growth on a relevant timescale | 0 | 11 | transfer only |
| evasion of astronomical survival bounds | 0 | 28 | transfer only |

The mechanism verdict is therefore specific: the corpus supplies equations for
adjacent black-hole growth, accretion, compact-object and lifetime mechanisms,
but it does not supply the closed collider chain required by the dangerous LHC
scenario.

The repository does not require the private Hyperion core to build the public
PDF. It uses static artifacts committed under `runs/lhc_black_hole_audit_500k_strict`.
The PDF is generated automatically from those artifacts: the build script
derives the constructor summaries, knowledge graphs, mechanism figures, TeX
source and compiled PDF without hand-editing the report.

## Build The Main PDF

Prerequisites:

- Python 3.9 or newer
- `matplotlib`
- a LaTeX installation with `latexmk`

From the repository root:

```bash
python3 -m pip install matplotlib
scripts/build_lhc_black_hole_answer.sh
```

This writes:

- `paper/lhc_black_hole_answer.tex`
- `paper/lhc_black_hole_answer.pdf`
- `paper/lhc_black_hole_answer_manifest.json`
- `paper/figures/lhc_*.pdf`

The build is deterministic with respect to the committed static run directory.
Updating `runs/lhc_black_hole_audit_500k_strict/` and rerunning the script
regenerates the TeX, all figures and the PDF.

To build from a different static run directory:

```bash
scripts/build_lhc_black_hole_answer.sh \
  /path/to/lhc_black_hole_audit_500k_strict \
  paper
```

The run directory must contain at least:

- `manifest.json`
- `provenance_graph.json`
- `equation_mechanism_graph.json`
- `sparse_attention_audit.json`

The build script also derives:

- `physical_constructor.json`
- `physical_constructor.md`
- `public_knowledge_graph.json`
- `public_knowledge_graph.md`
- `discourse_vs_mechanism_attention.json`
- `discourse_vs_mechanism_attention.md`

## Constructor-Layer Export

The public graph receipts can be expanded into constructor objects: source id,
equation order, local context, variable roles, matched graph node, route
signature, constructor roles, slot matches and source-local chains.

The default mode uses the retained equation fingerprints in
`equation_mechanism_graph.json`. It does not need full arXiv source files:

```bash
python3 -B scripts/build_constructor_layer_export.py \
  --run-dir runs/lhc_black_hole_audit_500k_strict \
  --out-dir outputs/lhc_constructor_layer_fingerprint \
  --fingerprint-only
```

This writes:

- `outputs/lhc_constructor_layer_fingerprint/constructor_layer_export.json`
- `outputs/lhc_constructor_layer_fingerprint/constructor_layer_export.md`

In the current static run this produces 1,408 fingerprinted equation windows,
986 slot-matched equations, 412 LHC-black-hole-relevant equations and 241
source-local constructor chains.

This constructor layer is the bridge between raw equation witnesses and the
physical verdict. It tests whether formula windows instantiate the six required
physical slots and whether those slots connect into a source-local branch. It is
not a citation count and not a text similarity score.

If full source text is available, the same export can add section positions and
larger local derivation excerpts:

```bash
python3 -B scripts/build_constructor_layer_export.py \
  --run-dir runs/lhc_black_hole_audit_500k_strict \
  --source-dir data/hf_lhc_selection_500k/sources \
  --out-dir outputs/lhc_constructor_layer_export
```

This writes:

- `outputs/lhc_constructor_layer_export/constructor_layer_export.json`
- `outputs/lhc_constructor_layer_export/constructor_layer_export.md`

The fingerprint-native export is the mechanism layer. Full source text is useful
for human-facing excerpts and variable definitions, but it is not required to
assemble the retained constructor roles.

## What The PDF Contains

The generated report is `paper/lhc_black_hole_answer.pdf`.

It contains:

- a problem-first introduction to the LHC black-hole question;
- a mechanism verdict expressed as a physical branch;
- a detailed constructor with six slots and equation conditions;
- provenance and public knowledge graph figures;
- a retained equation mechanism graph;
- representative equation receipts;
- a transfer analysis from astrophysical black-hole equations to collider variables;
- a final comparison with the CERN Safety Study Group report, `CERN-2003-001`;
- references, including the CERN report and LHC-safety papers.

## Relation To The CERN Safety Report

The final chapter compares the mechanism result with the independent CERN Safety
Study Group report:

J.-P. Blaizot, J. Iliopoulos, J. Madsen, G. G. Ross, P. Sonderegger and
H.-J. Specht, "Study of potentially dangerous events during heavy-ion collisions
at the LHC: Report of the LHC Safety Study Group", CERN-2003-001 (2003).

The agreement is structural. CERN-2003-001 does not treat production alone as
the safety question; it evaluates whether a produced object could survive,
interact with matter, grow and evade astrophysical constraints. The constructor
in this repository tests the same branch form against the larger arXiv-derived
equation layer. It finds the same kind of break: no retained direct collider
equation chain closes the path from production to survival, capture and positive
growth.

The added contribution here is not a replacement for CERN's dedicated physics
assessment. It is a corpus-level check showing how a provenance graph and an
equation-mechanism graph give different answers. Provenance locates claims;
the constructor tests whether the mechanism required by the claim is present.

## Static Artifacts

The committed static run is:

```text
runs/lhc_black_hole_audit_500k_strict/
```

Important files:

- `manifest.json`: run-level counts and source summary.
- `provenance_graph.json`: paper and claim-family graph.
- `equation_witnesses.json`: source-local equation windows.
- `equation_mechanism_graph.json`: retained equation mechanism graph.
- `constructor_layer/constructor_layer_export.json`: fingerprint-native
  constructor objects and source-local chains.
- `operational_graph.json`: earlier operational graph artifact.
- `sparse_attention_audit.json`: route-level sparse attention over retained mechanisms.
- `summary.json`: compact public summary.

These artifacts are derived outputs. They are sufficient to rebuild the public
PDF and figures without rerunning the full arXiv/Hugging Face selection.

## Regenerating Static Artifacts From Papers

For the minimal included fixture:

```bash
python -B scripts/build_lhc_mechanism_audit.py \
  --papers-dir examples \
  --out-dir outputs/minimal
```

For a folder of downloaded LaTeX sources or PDFs:

```bash
python -B scripts/build_lhc_mechanism_audit.py \
  --papers-dir data/papers \
  --out-dir outputs/lhc_black_hole_audit \
  --knowledgeparser-root /Users/vbaulin/antigr/KnowledgeParser
```

For broad arXiv selection from Hugging Face:

```bash
python -B scripts/select_lhc_literature.py \
  --dataset synthetix-institute/latex-data-pub \
  --out-dir data/hf_lhc_selection \
  --max-docs 500000 \
  --min-score 3
```

The selected sources written by the broad selector may be abstract-scale if the
dataset row exposes only title/abstract fields. To export full LaTeX from the
Hugging Face dataset for the selected IDs, run:

```bash
python -B scripts/export_hf_full_sources_from_selection.py \
  --dataset synthetix-institute/latex-data \
  --selection-manifest data/hf_lhc_selection/selection_manifest.json \
  --out-dir data/hf_lhc_full_selection
```

Then build the audit from selected sources or full exported sources:

```bash
python -B scripts/build_lhc_mechanism_audit.py \
  --papers-dir data/hf_lhc_full_selection/sources \
  --out-dir outputs/lhc_black_hole_audit_500k_strict \
  --knowledgeparser-root /Users/vbaulin/antigr/KnowledgeParser
```

To generate the current public PDF from that output:

```bash
scripts/build_lhc_black_hole_answer.sh \
  outputs/lhc_black_hole_audit_500k_strict \
  paper
```

## Legacy Demo Scripts

Older demo builders remain in `scripts/` for reference:

- `scripts/build_static_public_demo.sh`
- `scripts/build_public_demo_report.py`

The main reproducible public report is now built by:

```bash
scripts/build_lhc_black_hole_answer.sh
```
