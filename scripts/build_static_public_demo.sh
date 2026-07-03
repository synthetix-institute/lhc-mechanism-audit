#!/usr/bin/env bash
set -euo pipefail

OUT_DIR="${1:-outputs/lhc_black_hole_audit_500k_strict}"
PAPER_DIR="${2:-paper}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
export MPLCONFIGDIR="${MPLCONFIGDIR:-/tmp/lhc-mechanism-mpl}"
mkdir -p "${MPLCONFIGDIR}"

if [[ -f "${OUT_DIR}/equation_mechanism_graph.json" ]]; then
  "${PYTHON_BIN}" -B scripts/build_sparse_attention_audit.py --out-dir "${OUT_DIR}"
else
  echo "WARNING: ${OUT_DIR}/equation_mechanism_graph.json not found; using sanitized summary fallback." >&2
fi

"${PYTHON_BIN}" -B scripts/build_public_demo_report.py \
  --out-dir "${OUT_DIR}" \
  --paper-dir "${PAPER_DIR}"

echo "Wrote ${PAPER_DIR}/lhc_mechanism_audit_demo.tex"
