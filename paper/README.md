# Paper Build

The current public report is:

```text
paper/lhc_black_hole_answer.pdf
```

Build it from the repository root:

```bash
scripts/build_lhc_black_hole_answer.sh
```

The script regenerates:

- `paper/lhc_black_hole_answer.tex`
- `paper/lhc_black_hole_answer.pdf`
- `paper/lhc_black_hole_answer_manifest.json`
- `paper/figures/lhc_*.pdf`

The default input is:

```text
runs/lhc_black_hole_audit_500k_strict/
```

To rebuild from another static run:

```bash
scripts/build_lhc_black_hole_answer.sh \
  /path/to/lhc_black_hole_audit_500k_strict \
  paper
```

The LaTeX file can also be compiled manually:

```bash
cd paper
latexmk -pdf -interaction=nonstopmode -halt-on-error lhc_black_hole_answer.tex
```
