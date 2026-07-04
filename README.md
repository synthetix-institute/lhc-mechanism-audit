# LHC Mechanism Audit

This repository builds a static, inspectable report on one question:

> Do the processed arXiv papers support a dangerous LHC black-hole scenario?

The report compares two layers of evidence. The first is a provenance graph:
papers connected to extracted claim families. The second is an equation
mechanism graph: formula windows connected to physical roles such as production,
evaporation, capture, growth and astronomical bounds. The conclusion is obtained
from the second layer. A dangerous branch requires production in a parton
collision, survival against evaporation, stopping or capture in matter, net
positive growth and consistency with astronomical survival constraints.

The repository does not require the private Hyperion core to build the public
PDF. It uses static artifacts committed under `runs/lhc_black_hole_audit_500k_strict`.

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

The public graph receipts can be expanded into source-local constructor objects:
source id, section, equation order, local context, variable roles, matched graph
node, route signature, constructor roles, slot matches and source-local chains.

From the committed/static run plus the local selected source folder:

```bash
python3 -B scripts/build_constructor_layer_export.py \
  --run-dir runs/lhc_black_hole_audit_500k_strict \
  --source-dir data/hf_lhc_selection_500k/sources \
  --out-dir outputs/lhc_constructor_layer_export
```

This writes:

- `outputs/lhc_constructor_layer_export/constructor_layer_export.json`
- `outputs/lhc_constructor_layer_export/constructor_layer_export.md`

The current local source folder is mostly title/abstract-scale text. The export
therefore reports `limited_abstract_scale_sources`; it is structurally valid and
matches the public graph nodes, but it cannot reconstruct full paper derivations.
For full constructor-layer evidence, run the same command on a source directory
containing full LaTeX/PDF papers, preferably including the LHC safety seed papers.

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

Then build the audit from selected sources:

```bash
python -B scripts/build_lhc_mechanism_audit.py \
  --papers-dir data/hf_lhc_selection/sources \
  --out-dir outputs/lhc_black_hole_audit_500k_strict \
  --knowledgeparser-root /Users/vbaulin/antigr/KnowledgeParser
```

To generate the current public PDF from that output:

```bash
scripts/build_lhc_black_hole_answer.sh \
  outputs/lhc_black_hole_audit_500k_strict \
  paper
```

## CERN Alignment

The final chapter of the report compares the branch logic and equations against:

J.-P. Blaizot, J. Iliopoulos, J. Madsen, G. G. Ross, P. Sonderegger and
H.-J. Specht, "Study of potentially dangerous events during heavy-ion collisions
at the LHC: Report of the LHC Safety Study Group", CERN-2003-001 (2003).

The report uses the same physical branch structure: production is only the first
step; a dangerous case also requires survival, accretion faster than decay and
consistency with astrophysical constraints. The added contribution here is the
corpus-level separation of claim/provenance evidence from equation-mechanism
evidence.

## Legacy Demo Scripts

Older demo builders remain in `scripts/` for reference:

- `scripts/build_static_public_demo.sh`
- `scripts/build_public_demo_report.py`

The main reproducible public report is now built by:

```bash
scripts/build_lhc_black_hole_answer.sh
```
