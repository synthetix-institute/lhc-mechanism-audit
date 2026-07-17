# Judge's Route

Start with the [complete submission packet](paper/lhc_epistack_submission_packet.pdf).
Pages 1--10 answer the LHC black-hole question in ordinary language and show
one complete chain from a primary-source equation to the case conclusion.
Pages 11--24 contain the full scientific article, larger graphs and independent
CERN comparison.

The submission's main result is simple: scientific papers contain two graphs.
One records authors, claims and citations. The other records how physical
quantities are transformed by equations. The LHC case shows why both are
needed. A challenge to Hawking evaporation changes one part of the safety
argument; the equation graph then activates the stable-object branch and tests
stopping, accretion, growth time and compact-star survival.

## Five-Minute Inspection

1. Read the six-condition diagram on page 2 of the guide.
2. Inspect the worked receipt beginning on page 3.
3. Compare the documentary and equation graphs.
4. Open [the receipt bundle](paper/lhc_judges_guide_receipts.json) and search for
   `E00455` or `E00202`.
5. Propagate the Hawking counterfactual:

```bash
bash scripts/run_judge_demo.sh
```

The dependency-free command verifies the selected equation IDs, checks the
prespecified primary-source benchmark and prints the calculations that become
active when evaporation is removed. Rebuild the complete PDF with
`bash scripts/build_submission_packet.sh`.

## Most Informative Artifacts

- [Submission packet](paper/lhc_epistack_submission_packet.pdf): ten-page core
  followed by the fourteen-page article.
- [Judge's guide](paper/lhc_judges_guide.pdf): the core as a standalone file.
- [Full public article](paper/lhc_black_hole_answer.pdf): detailed physics,
  figures and the held-out CERN comparison.
- [Receipt bundle](paper/lhc_judges_guide_receipts.json): source positions,
  formulas and branch assignments used in the guide.
- [Joined graph](runs/lhc_black_hole_audit_revised/public_knowledge_graph.json):
  authorship, citations, claims, equations and physical conditions.
- [Equation graph](runs/lhc_black_hole_audit_revised/equation_mechanism_graph.json):
  source-local transitions and cross-paper analogues.
- [Twelve-equation benchmark](data/lhc_gold_benchmark.json): prespecified
  primary-source checks.

## Comparative Test

Run a preferred deep-research system with
[the fixed comparison prompt](data/judge_comparison_prompt.txt). The decisive
counterfactual is: *assume Hawking evaporation is absent*. A claim summary can
report that one safety argument has weakened. This submission computes what
comes next and identifies the equations required to keep the stable branch
alive.

## Full Rebuild

The static build above uses committed graph artifacts. The end-to-end scientific
pipeline is:

```bash
bash scripts/run_full_audit.sh
```

Its stages extract claims and equations, build both graphs, apply formula-level
conditions, rank informative equation transitions, assemble the physical branch
and regenerate the public article.

The underlying operational archive contains 2.5 million arXiv papers. The
committed LHC case uses a fixed 500,000-document screening slice so its selection
and attrition can be reproduced independently of the larger archive.
