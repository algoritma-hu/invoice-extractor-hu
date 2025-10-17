from pathlib import Path
from datetime import datetime

# TODO: replace with your real logic from invoice_extract_hu_v2.py
def extract_invoice(path: str) -> dict:
    p = Path(path)
    # Minimal stub result; integrate your regex/OCR ASAP
    return {
        "doc_type": "invoice",
        "file": p.name,
        "seller": None,
        "invoice_no": None,
        "issue_date": None,   # "YYYY-MM-DD"
        "net": None,
        "vat": None,
        "gross": None,
        "currency": "HUF",
        "confidence": 0.4,
        "extracted_at": datetime.utcnow().isoformat(timespec="seconds")
    }
