from pathlib import Path

INVOICE_KEYS = ("számla", "szamla", "számlaszám", "vevő", "eladó", "áfa")
RECEIPT_KEYS = ("nyugta", "block", "pénztárgép", "vásárlás", "bruttó", "összeg")

def _hint_from_name(p: Path) -> str:
    name = p.name.lower()
    if "proforma" in name: return "other"      # avoid false-positive
    if "invoice" in name or "szamla" in name or "számla" in name: return "invoice"
    if "receipt" in name or "nyugta" in name: return "receipt"
    return ""

def classify(path: str) -> str:
    p = Path(path)
    # filename hints first
    hint = _hint_from_name(p)
    if hint: return "invoice" if hint=="invoice" else ("receipt" if hint=="receipt" else "other")
    # very cheap content sniff (works for PDFs with extractable text; images will fall back)
    try:
        import pdfminer.high_level as pm
        text = pm.extract_text(str(p))[:5000].lower()
    except Exception:
        text = ""
    score_inv = sum(k in text for k in INVOICE_KEYS)
    score_rec = sum(k in text for k in RECEIPT_KEYS)
    if score_inv >= max(2, score_rec+1): return "invoice"
    if score_rec >= max(2, score_inv+1): return "receipt"
    return "other"
