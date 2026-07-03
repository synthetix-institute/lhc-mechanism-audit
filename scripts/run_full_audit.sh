#!/usr/bin/env bash
set -euo pipefail

PAPERS_DIR="${PAPERS_DIR:-examples}"
OUT_DIR="${OUT_DIR:-outputs/lhc_mechanism_audit}"
KNOWLEDGEPARSER_ROOT="${KNOWLEDGEPARSER_ROOT:-/Users/vbaulin/antigr/KnowledgeParser}"

python -B scripts/build_lhc_mechanism_audit.py \
  --papers-dir "$PAPERS_DIR" \
  --out-dir "$OUT_DIR" \
  --knowledgeparser-root "$KNOWLEDGEPARSER_ROOT"

echo
echo "Report: $OUT_DIR/audit_report.md"
echo "Shallow failure test: $OUT_DIR/shallow_failure.md"
