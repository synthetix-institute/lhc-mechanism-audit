# Public LaTeX Demo

The public report is generated from static audit artifacts. It does not import
Hyperion and does not expose private fingerprints, model checkpoints or core
pipeline files.

## Build From Full Cluster Outputs

```bash
cd /home/softmat/Desktop/Hyperion/lhc-mechanism-audit
git pull --ff-only

python -B scripts/build_static_public_demo.sh \
  outputs/lhc_black_hole_audit_500k_strict \
  paper
```

This writes:

- `paper/lhc_mechanism_audit_demo.tex`
- `paper/generated/run_numbers.tex`
- `paper/generated/public_demo_manifest.json`
- `paper/figures/evidence_funnel.pdf`
- `paper/figures/provenance_vs_mechanism.pdf`
- `paper/figures/mechanism_translation.pdf`
- `paper/figures/sparse_attention_routes.pdf`

Compile with:

```bash
cd paper
latexmk -pdf lhc_mechanism_audit_demo.tex
```

## Build From Sanitized Summary Only

For a public smoke test without cluster outputs:

```bash
python -B scripts/build_static_public_demo.sh \
  runs/lhc_black_hole_audit_500k_strict \
  paper
```

The sparse-attention figure is only fully populated when
`sparse_attention_audit.json` has been generated from the full static graph.
