import argparse
import yaml
from pathlib import Path

from classify import classify  # kept for compatibility
from extractors.hu_invoice import extract_invoice
from extractors.receipt_basic import extract_receipt  # retained
from routing import route, append_logs, ensure_dirs
from notify import send_email

# === HU invoice scorer integration ===
import json
import re
from quick_check import run_pdftotext, load_patterns, extract_fields, score_invoice

PATTERNS = load_patterns()  # loads patterns_hu.json
_CURRENCY_RX = re.compile(r"(?i)\b(Ft|HUF|EUR|\u20AC|USD|\$)\b")  # \u20AC = €

def classify_pdf_with_hu_scorer(pdf_path):
    text = run_pdftotext(str(pdf_path))
    fields = extract_fields(text, PATTERNS)
    confidence = score_invoice(text, fields)
    doc_type = "invoice" if confidence >= 0.6 else "other"
    currency = "HUF" if _CURRENCY_RX.search(text) else None
    return doc_type, float(round(confidence, 3)), currency, fields

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()

    # Load YAML configuration
    with open(args.config, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    # Map your config (paths/routing schema)
    inbox = Path(cfg.get("paths", {}).get("inbox", "./samples"))
    out_root = Path(cfg.get("paths", {}).get("out_root", "./out"))

    # Ensure output dirs/logs exist (your helper expects out_root + routing)
    ensure_dirs(out_root, cfg.get("routing", {}))

    # Collect PDFs from inbox
    inputs = sorted(inbox.glob("*.pdf"))
    if not inputs:
        print(f"⚠️  No PDF files found in input folder: {inbox}")
        return

    for p in inputs:
        try:
            doc_type, confidence, currency, fields = classify_pdf_with_hu_scorer(p)

            if doc_type == "invoice":
                meta = extract_invoice(str(p)) or {}
            else:
                meta = {}

            meta.update({
                "doc_type": doc_type,
                "file": p.name,
                "confidence": confidence,
                "currency": currency or "",
                "szamlaszam": fields.get("szamlaszam") or "",
                "kibocsatas_datum": fields.get("kibocsatas_datum") or "",
                "teljesites_datum": fields.get("teljesites_datum") or "",
                "osszeg_netto": fields.get("osszeg_netto") or "",
                "osszeg_brutto": fields.get("osszeg_brutto") or ""
            })

            dest = route(str(p), doc_type, meta, cfg)
            rec = {"src": str(p), "dest": dest, **meta}
            append_logs(rec, cfg)
            print(f"✅ {p.name} → {doc_type.upper()} ({confidence:.2f})")

        except Exception as e:
            print(f"❌ Error processing {p.name}: {e}")

    # Only send email if enabled in config (notify.enabled)
    if cfg.get("notify", {}).get("enabled"):
        send_email(cfg)

if __name__ == "__main__":
    main()
