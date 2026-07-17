#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_DIR="${1:-${ROOT_DIR}/runs/lhc_black_hole_audit_revised}"
PAPER_DIR="${2:-${ROOT_DIR}/paper}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

export MPLCONFIGDIR="${MPLCONFIGDIR:-/tmp/lhc-mechanism-mpl}"
mkdir -p "${MPLCONFIGDIR}" "${PAPER_DIR}"

required=(
  "manifest.json"
  "provenance_graph.json"
  "equation_mechanism_graph.json"
)

for file in "${required[@]}"; do
  if [[ ! -f "${RUN_DIR}/${file}" ]]; then
    echo "Missing ${RUN_DIR}/${file}" >&2
    echo "Provide a static audit run directory, or copy cluster outputs into ${RUN_DIR}." >&2
    exit 2
  fi
done

cd "${ROOT_DIR}"
"${PYTHON_BIN}" -B scripts/build_physical_constructor.py --out-dir "${RUN_DIR}"
"${PYTHON_BIN}" -B scripts/build_sparse_attention_audit.py --out-dir "${RUN_DIR}"
"${PYTHON_BIN}" -B scripts/build_discourse_mechanism_attention.py --run-dir "${RUN_DIR}"
"${PYTHON_BIN}" -B scripts/build_public_knowledge_graph.py --out-dir "${RUN_DIR}"
"${PYTHON_BIN}" -B scripts/build_constructor_layer_export.py \
  --run-dir "${RUN_DIR}" \
  --out-dir "${RUN_DIR}" \
  --fingerprint-only
"${PYTHON_BIN}" -B scripts/build_lhc_black_hole_answer.py \
  --run-dir "${RUN_DIR}" \
  --paper-dir "${PAPER_DIR}"

if ! command -v latexmk >/dev/null 2>&1; then
  echo "latexmk is required to compile the PDF. The TeX file was written to ${PAPER_DIR}/lhc_black_hole_answer.tex" >&2
  exit 3
fi

cd "${PAPER_DIR}"
latexmk -pdf -interaction=nonstopmode -halt-on-error lhc_black_hole_answer.tex

echo "Wrote ${PAPER_DIR}/lhc_black_hole_answer.pdf"
