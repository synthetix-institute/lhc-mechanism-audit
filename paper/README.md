# Generated Paper

`lhc_black_hole_answer.pdf` is generated from the retained provenance graph,
equation mechanism graph, six-slot physical constructor, sparse-attention
calculation and the independent equation benchmark.

From the repository root, run:

```bash
bash scripts/build_lhc_black_hole_answer.sh
```

The default evidence bundle is `runs/lhc_black_hole_audit_revised`. The build
regenerates the derived JSON files, eight vector figures, the LaTeX source and
the PDF. A different evidence bundle can be supplied as the first argument.

```bash
bash scripts/build_lhc_black_hole_answer.sh /path/to/run paper
```

The report figures show the evidence funnel, full and collapsed provenance
graphs, public knowledge graph, retained equation graph, physical constructor,
astrophysics-to-collider transfer map and sparse-attention result.
