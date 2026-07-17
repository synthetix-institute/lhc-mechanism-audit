#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CORE_PDF="${ROOT_DIR}/paper/lhc_judges_guide.pdf"
ARTICLE_PDF="${ROOT_DIR}/paper/lhc_black_hole_answer.pdf"
OUTPUT_PDF="${ROOT_DIR}/paper/lhc_epistack_submission_packet.pdf"

cd "${ROOT_DIR}"

bash scripts/build_judges_guide.sh

if [[ "${REBUILD_ARTICLE:-0}" == "1" || ! -f "${ARTICLE_PDF}" ]]; then
  bash scripts/build_lhc_black_hole_answer.sh
fi

if [[ ! -f "${ARTICLE_PDF}" ]]; then
  printf '%s\n' "Missing ${ARTICLE_PDF}" >&2
  exit 2
fi

if "${PYTHON_BIN:-python3}" -B -c "import pypdf" >/dev/null 2>&1; then
  "${PYTHON_BIN:-python3}" -B scripts/merge_submission_packet.py \
    "${CORE_PDF}" "${ARTICLE_PDF}" "${OUTPUT_PDF}"
elif command -v pdfunite >/dev/null 2>&1; then
  TEMP_PDF="${OUTPUT_PDF}.tmp"
  rm -f "${TEMP_PDF}"
  pdfunite "${CORE_PDF}" "${ARTICLE_PDF}" "${TEMP_PDF}"
  mv "${TEMP_PDF}" "${OUTPUT_PDF}"
elif command -v qpdf >/dev/null 2>&1; then
  TEMP_PDF="${OUTPUT_PDF}.tmp"
  rm -f "${TEMP_PDF}"
  qpdf --empty --pages "${CORE_PDF}" "${ARTICLE_PDF}" -- "${TEMP_PDF}"
  mv "${TEMP_PDF}" "${OUTPUT_PDF}"
else
  printf '%s\n' "Install pypdf, Poppler (pdfunite) or qpdf to assemble the submission packet." >&2
  exit 3
fi

if command -v pdfinfo >/dev/null 2>&1; then
  CORE_PAGES="$(pdfinfo "${CORE_PDF}" | awk '/^Pages:/ {print $2}')"
  ARTICLE_PAGES="$(pdfinfo "${ARTICLE_PDF}" | awk '/^Pages:/ {print $2}')"
  TOTAL_PAGES="$(pdfinfo "${OUTPUT_PDF}" | awk '/^Pages:/ {print $2}')"
  printf '%s\n' "Built ${OUTPUT_PDF} (${CORE_PAGES}-page core + ${ARTICLE_PAGES}-page article = ${TOTAL_PAGES} pages)."
else
  printf '%s\n' "Built ${OUTPUT_PDF}."
fi
