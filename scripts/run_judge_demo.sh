#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

python3 -B scripts/judge_demo.py --counterfactual no-hawking

printf '\n%s\n' "Inspect one source receipt with:"
printf '%s\n' "  python3 -B scripts/judge_demo.py --receipt E00202"
printf '%s\n' "Read the judge guide at paper/lhc_judges_guide.pdf"
