# Public Article

## Main submission

`lhc_judges_guide.pdf` is the primary competition document. It is a complete
ten-page explanation of the original two-map solution, the construction method,
one source-to-conclusion receipt and the judging-criteria evidence. Build it
from the repository root:

```bash
bash scripts/build_judges_guide.sh
```

The core states the corpus hierarchy explicitly: Hyperion's operational
archive contains 2.5 million arXiv papers, while the reproducible LHC case uses
a fixed 500,000-document screening slice plus complete primary sources.

The build writes `lhc_judges_guide_receipts.json` and verifies the selected
equation IDs and twelve-equation benchmark before compiling the PDF.

The runnable judge demonstration requires only Python:

```bash
bash scripts/run_judge_demo.sh
```

## Worked two-graph artifact

[`lhc_black_hole_answer.pdf`](lhc_black_hole_answer.pdf) is the separate
fourteen-page knowledge artifact. It explains the LHC black-hole question for
non-specialists, begins with the physical answer,
then follows the six events that would all have to occur before a microscopic
object could become dangerous. The equations are introduced one at a time,
their variables are defined at first use, and the final section compares the
automated reconstruction with the independent CERN safety report.

The article is generated from the retained provenance graph, equation graph,
six-condition physical chain, equation-transition calculation and a
prespecified twelve-equation source test.

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

The figures show the six physical conditions, the full and collapsed
provenance graphs, the joined literature-to-physics graph, the retained
equation graph, the astrophysics-to-collider transfer and the equation steps
that carry the safety argument.
