#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PAPERS_DIR="${PAPERS_DIR:-${ROOT_DIR}/data/hf_lhc_selection_500k/sources}"
PRIMARY_SOURCES_DIR="${PRIMARY_SOURCES_DIR:-${ROOT_DIR}/data/arxiv_lhc_full_sources/sources}"
OUT_DIR="${OUT_DIR:-${ROOT_DIR}/outputs/lhc_black_hole_audit_revised}"
PAPER_DIR="${PAPER_DIR:-${ROOT_DIR}/paper}"
KNOWLEDGEPARSER_ROOT="${KNOWLEDGEPARSER_ROOT:-${ROOT_DIR}/..}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
BUILD_PDF="${BUILD_PDF:-1}"

cd "${ROOT_DIR}"
mkdir -p "${OUT_DIR}" "${PAPER_DIR}"

echo "[1/9] Checking the six primary papers and twelve named equation receipts"
"${PYTHON_BIN}" -B scripts/audit_lhc_gold_benchmark.py \
  --sources-dir "${PRIMARY_SOURCES_DIR}" \
  --benchmark data/lhc_gold_benchmark.json \
  --out-json "${OUT_DIR}/lhc_gold_benchmark.json"

echo "[2/9] Building provenance and equation-witness archives"
"${PYTHON_BIN}" -B scripts/build_lhc_mechanism_audit.py \
  --papers-dir "${PAPERS_DIR}" \
  --additional-papers-dir "${PRIMARY_SOURCES_DIR}" \
  --out-dir "${OUT_DIR}" \
  --knowledgeparser-root "${KNOWLEDGEPARSER_ROOT}"

echo "[3/9] Building the equation mechanism graph"
"${PYTHON_BIN}" -B scripts/build_equation_mechanism_graph.py --out-dir "${OUT_DIR}"

echo "[4/9] Testing the six-condition physical constructor"
"${PYTHON_BIN}" -B scripts/build_physical_constructor.py --out-dir "${OUT_DIR}"

echo "[5/9] Computing sparse attention over measured graph edges"
"${PYTHON_BIN}" -B scripts/build_sparse_attention_audit.py --out-dir "${OUT_DIR}"

echo "[6/9] Comparing provenance attention with mechanism attention"
"${PYTHON_BIN}" -B scripts/build_discourse_mechanism_attention.py --run-dir "${OUT_DIR}"

echo "[7/9] Joining provenance, equations and constructor contracts"
"${PYTHON_BIN}" -B scripts/build_public_knowledge_graph.py --out-dir "${OUT_DIR}"

echo "[8/9] Exporting source-ordered constructor equations"
"${PYTHON_BIN}" -B scripts/build_constructor_layer_export.py \
  --run-dir "${OUT_DIR}" \
  --out-dir "${OUT_DIR}" \
  --fingerprint-only

if [[ "${BUILD_PDF}" == "1" ]]; then
  echo "[9/9] Rendering the public paper"
  bash scripts/build_lhc_black_hole_answer.sh "${OUT_DIR}" "${PAPER_DIR}"
else
  echo "[9/9] PDF build skipped (BUILD_PDF=${BUILD_PDF})"
fi

echo "Run: ${OUT_DIR}"
echo "Paper: ${PAPER_DIR}/lhc_black_hole_answer.pdf"
