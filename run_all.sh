#!/usr/bin/env bash
set -euo pipefail
DIR="${1:-invoices_hu}"

echo "== Convert PDFs to TXT in $DIR =="
for f in "$DIR"/*.pdf; do
  [ -e "$f" ] || continue
  out="${f%.pdf}.txt"
  if [ ! -s "$out" ]; then pdftotext -layout "$f" "$out" || true; fi
done

echo "== Extract =="
IN_DIR="$DIR" python3 extract_invoices.py

echo "== Compare =="
IN_DIR="$DIR" python3 compare_invoices.py

