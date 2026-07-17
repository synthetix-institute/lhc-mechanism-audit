#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

python3 -B scripts/build_judges_guide.py

if command -v latexmk >/dev/null 2>&1; then
  latexmk -pdf -interaction=nonstopmode -halt-on-error \
    -output-directory=paper paper/lhc_judges_guide.tex
elif command -v pdflatex >/dev/null 2>&1; then
  pdflatex -interaction=nonstopmode -halt-on-error \
    -output-directory=paper paper/lhc_judges_guide.tex
  pdflatex -interaction=nonstopmode -halt-on-error \
    -output-directory=paper paper/lhc_judges_guide.tex
else
  printf '%s\n' "LaTeX is required to build paper/lhc_judges_guide.pdf." >&2
  exit 1
fi

printf '%s\n' "Built paper/lhc_judges_guide.pdf"
