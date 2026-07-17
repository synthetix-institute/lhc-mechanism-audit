# Revised Static Evidence Bundle

This directory contains the retained inputs needed to regenerate the public
LHC black-hole report:

- `manifest.json`: corpus scale and source-selection record;
- `provenance_graph.json`: papers, citations and extracted claims;
- `equation_mechanism_graph.json`: fingerprinted equations and measured graph
  transitions;
- `lhc_gold_benchmark.json`: recovery results for twelve named equations from
  six primary papers.

Derived constructors, attention results, figures, LaTeX and PDF are rebuilt by:

```bash
bash scripts/build_lhc_black_hole_answer.sh
```
