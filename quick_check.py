import json, re, subprocess, sys, pathlib

PATTERN_FILE = "patterns_hu.json"

def run_pdftotext(pdf_path: str) -> str:
    try:
        out = subprocess.check_output(
            ["pdftotext", "-layout", pdf_path, "-"],
            stderr=subprocess.STDOUT
        )
        return out.decode("utf-8", errors="ignore")
    except subprocess.CalledProcessError as e:
        print(e.output.decode("utf-8", errors="ignore"), file=sys.stderr)
        raise

def load_patterns(path=PATTERN_FILE):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

POS_SIGNALS = [
    r"(?i)\bSzámla\b",
    r"(?i)\bAdószám\b",
    r"(?i)\bTeljesítés\b",
    r"(?i)\bFizetési\s+határidő\b",
    r"(?i)\bBruttó\b|\bNettó\b|\bÁFA\b",
]
NEG_SIGNALS = [
    r"(?i)\bHasználati\s+útmutató\b",
    r"(?i)\bJegyzőkönyv\b",
    r"(?i)\bÖnéletrajz\b",
    r"(?i)\bSzerződés\b(?!.*Számla)",
]

def score_invoice(text: str, fields: dict) -> float:
    score = 0.0
    # Heuristic signals
    seen = sum(bool(re.search(p, text)) for p in POS_SIGNALS)
    if seen:
        score += min(0.2 * seen, 0.6)
    if any(re.search(n, text) for n in NEG_SIGNALS):
        score -= 0.2

    # Field presence bonuses
    if fields.get("szamlaszam"):
        score += 0.2
    date_hits = sum(1 for k in ("kibocsatas_datum","teljesites_datum","fizetesi_hatarido") if fields.get(k))
    if date_hits >= 2:
        score += 0.2
    money_hit = (any(fields.get(k) for k in ("osszeg_brutto","osszeg_netto"))
                 and re.search(r"(?i)\b(HUF|Ft|EUR|€|USD|\$)\b", text))
    if money_hit:
        score += 0.2

    return max(0.0, min(1.0, score))
def extract_fields(text: str, patterns: dict) -> dict:
    out = {}
    for key, plist in patterns.items():
        val = None
        for p in plist:
            m = re.search(p, text)
            if m:
                val = m.group(1) if m.groups() else m.group(0)
                break
        out[key] = val
    return out
def main():
    if len(sys.argv) != 2:
        print("Usage: python3 quick_check.py /path/to/file.pdf", file=sys.stderr)
        sys.exit(2)
    pdf = sys.argv[1]
    if not pathlib.Path(pdf).exists():
        print(f"File not found: {pdf}", file=sys.stderr)
        sys.exit(2)

    text = run_pdftotext(pdf)
    patterns = load_patterns()
    fields = extract_fields(text, patterns)
    conf = score_invoice(text, fields)
    kind = "invoice" if conf >= 0.6 else "other"
    print(json.dumps(
        {"file": pdf, "kind": kind, "confidence": round(conf, 3), "fields": fields},
        ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
