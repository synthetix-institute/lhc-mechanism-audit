# LHC Mechanism Audit

This repository is a worked example for the epistemic-stack contest.  It tests
a specific claim:

> A provenance graph can organize the LHC black-hole debate, but it cannot by
> itself decide the safety argument.  The decisive layer is the mechanism:
> production assumptions, evaporation or stability branches, capture/stopping,
> accretion, astrophysical bounds and falsifying observations.

The repository builds two inspectable graphs from real papers:

1. `provenance_graph.json`: who wrote which paper, what claim family it belongs
   to, and which sources support or challenge the safety conclusion.
2. `operational_graph.json`: equation and derivation witnesses, classified by
   mechanism role, with chain candidates that only exist when source-local
   equations or explicit derivation language support them.

The point is not to produce another prose summary.  The point is to show what a
claim graph misses.

## Core Sources

The seed set is stored in `data/seed_papers.json`.

- Giddings and Mangano, *Astrophysical implications of hypothetical stable
  TeV-scale black holes*, arXiv:0806.3381.
- Ellis et al., *Review of the Safety of LHC Collisions*, arXiv:0806.3414.
- Plaga, *On the potential catastrophic risk from metastable quantum-black
  holes produced at particle colliders*, arXiv:0808.1415.
- Koch, Bleicher and Stoecker, *Exclusion of black hole disaster scenarios at
  the LHC*, arXiv:0807.3349.
- Giddings and Mangano, *Comments on claimed risk from metastable black holes*,
  arXiv:0808.4087.
- Casadio, Fabi and Harms, *Possibility of catastrophic black hole growth in the
  warped brane-world scenario at the LHC*, arXiv:0901.2948.

## Quick Start

Run on the included minimal fixture:

```bash
python -B scripts/build_lhc_mechanism_audit.py \
  --papers-dir examples \
  --out-dir outputs/minimal
```

Run on downloaded arXiv sources or PDFs:

```bash
python -B scripts/build_lhc_mechanism_audit.py \
  --papers-dir data/papers \
  --out-dir outputs/lhc_black_hole_audit \
  --knowledgeparser-root /Users/vbaulin/antigr/KnowledgeParser
```

Select related literature from a Hugging Face LaTeX dataset:

```bash
python -B scripts/select_lhc_literature.py \
  --dataset synthetix-institute/latex-data-pub \
  --out-dir data/hf_lhc_selection \
  --max-docs 0
```

Then build from the selected source files:

```bash
python -B scripts/build_lhc_mechanism_audit.py \
  --papers-dir data/hf_lhc_selection/sources \
  --out-dir outputs/hf_lhc_audit \
  --knowledgeparser-root /Users/vbaulin/antigr/KnowledgeParser
```

## Outputs

The builder writes:

- `sources.json`: selected papers and source files.
- `provenance_graph.json`: attribution and claim/disagreement graph.
- `equation_witnesses.json`: extracted equation/local-text witnesses with
  optional Hyperion operator/substrate fingerprints.
- `operational_graph.json`: mechanism-role graph and derivation-chain
  candidates.
- `shallow_failure.md`: what a provenance-only system can and cannot conclude.
- `audit_report.md`: compact mechanism-first report.

## Claim Boundary

This repository does not claim that an automated script resolves the LHC safety
question.  It demonstrates a stricter evaluation layer: claims are demoted when
they lack a source-local equation witness, an explicit mechanism role, or a
testable physical branch.  The output should be inspected as an audit object,
not as a final physics review.
