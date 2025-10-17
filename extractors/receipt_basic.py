from pathlib import Path
from datetime import datetime

def extract_receipt(path: str) -> dict:
    p = Path(path)
    # Stub; you can expand with OCR/regex later
    return {
        "doc_type": "receipt",
        "file": p.name,
        "merchant": None,
        "date": None,     # "YYYY-MM-DD"
        "total": None,
        "currency": "HUF",
        "confidence": 0.3,
        "extracted_at": datetime.utcnow().isoformat(timespec="seconds")
    }
