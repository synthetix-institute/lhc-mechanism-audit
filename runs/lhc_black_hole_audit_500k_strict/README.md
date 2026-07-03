# Public Run Snapshot: LHC Black-Hole Audit 500k Strict

This directory stores a public, sanitized summary of the 500k-source-selection
run. It is intended for reports, figures and public discussion. It does not
include Hyperion core code, private fingerprints, model checkpoints, memory
maps, or raw selected-paper shards.

## Run

- Dataset scanned: `synthetix-institute/latex-data-pub`
- Maximum documents scanned: `500000`
- Selected sources: `492`
- Equation witnesses: `1408`
- Formula-clean usable mechanism nodes: `204`
- LHC-black-hole case-relevant mechanism nodes: `72`
- Evidence-grade case mechanism nodes: `35`

## Main Finding

The selected corpus contains no formula-clean direct LHC-safety mechanism under
the current gates. It contains one collider-threshold or event-selection hook
and a larger set of astrophysical black-hole mechanisms. The serious audit is
therefore a mechanism-translation problem: use accretion, evaporation, capture,
mass growth and compact-object survival mechanisms as constraints on the
collider branch, instead of counting who asserted that the LHC was safe or
dangerous.

## Reproduce From Cluster Outputs

After running the full selection and audit on the cluster, regenerate the public
mechanism graph with:

```bash
cd /home/softmat/Desktop/Hyperion/lhc-mechanism-audit
PYTHONIOENCODING=utf-8 python -B scripts/build_equation_mechanism_graph.py \
  --out-dir outputs/lhc_black_hole_audit_500k_strict
```

Then generate sparse-attention receipts and the public report:

```bash
python -B scripts/build_sparse_attention_audit.py \
  --out-dir outputs/lhc_black_hole_audit_500k_strict

python -B scripts/build_public_demo_report.py \
  --out-dir outputs/lhc_black_hole_audit_500k_strict \
  --paper-dir paper
```
