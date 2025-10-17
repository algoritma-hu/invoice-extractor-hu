import os, re, sys, csv
from pdf2image import convert_from_path
import pytesseract

IN_DIR = "invoices_hu"
OUT_CSV = "extracted_invoices.csv"
LANG = "hun+eng"  # fallback to "eng" if you didn't install the hu pack

# Robust-ish patterns for Hungarian invoices
PATTERNS = {
    "szamlaszam": re.compile(r"(Számlaszám|Számla(?:szám)?)[:\s]*([A-Z0-9\-_/]+)", re.I),
    "kibocsatas_datum": re.compile(r"(Kibocsátás(?:\s+dátuma)?|Kelt)[:\s]*([0-9]{4}[-./][0-9]{2}[-./][0-9]{2})", re.I),
    "teljesites_datum": re.compile(r"(Teljesítés(?:\s+dátuma)?)[:\s]*([0-9]{4}[-./][0-9]{2}[-./][0-9]{2})", re.I),
    "hatarido": re.compile(r"(Fizetési\s+határidő|Határidő)[:\s]*([0-9]{4}[-./][0-9]{2}[-./][0-9]{2})", re.I),
    "fizmod": re.compile(r"(Fizetési\s+mód|Fizetési\s+mod)[:\s]*([A-Za-zÁÉÍÓÖŐÚÜŰáéíóöőúüű]+)", re.I),
    # Totals: grab the last number near the word
    "netto_osszeg": re.compile(r"(Nettó)[^\d]*(\d[\d\s.,]*)", re.I),
    "afa_osszeg": re.compile(r"(ÁFA)[^\d]*(\d[\d\s.,]*)", re.I),
    "brutto_osszeg": re.compile(r"(Végösszeg|Bruttó)[^\d]*(\d[\d\s.,]*)", re.I),
    # Parties
    "elado_nev": re.compile(r"(Eladó.*?\n)(.+)", re.I),
    "vevo_nev": re.compile(r"(Vevő.*?\n)(.+)", re.I),
}

def normnum(s):
    if not s: return None
    s = s.replace(" ", "").replace("\u00a0","").replace(".", "").replace(",", "")
    return int(s) if s.isdigit() else None

def extract_fields(text):
    out = {}
    for k, rgx in PATTERNS.items():
        m = None
        # Try to find the last relevant match for totals to avoid header collisions
        if k in ("netto_osszeg","afa_osszeg","brutto_osszeg"):
            matches = list(rgx.finditer(text))
            m = matches[-1] if matches else None
        else:
            m = rgx.search(text)
        if not m:
            out[k] = None
        else:
            val = m.group(2) if m.lastindex and m.lastindex >= 2 else m.group(0)
            val = val.strip()
            out[k] = val
    # Clean up numbers
    for key in ("netto_osszeg","afa_osszeg","brutto_osszeg"):
        out[key] = normnum(out[key])
    return out

def ocr_pdf(path):
    pages = convert_from_path(path, dpi=200)
    txt = []
    for p in pages:
        t = pytesseract.image_to_string(p, lang=LANG)
        txt.append(t)
    return "\n".join(txt)

def main():
    files = [f for f in os.listdir(IN_DIR) if f.lower().endswith(".pdf")]
    if not files:
        print("No PDFs found in", IN_DIR); sys.exit(1)

    rows = []
    for f in sorted(files):
        fp = os.path.join(IN_DIR, f)
        text = ocr_pdf(fp)
        data = extract_fields(text)
        data["file"] = f
        rows.append(data)
        print(f"{f} -> {data}")

    fieldnames = ["file","szamlaszam","kibocsatas_datum","teljesites_datum","hatarido","fizmod",
                  "elado_nev","vevo_nev","netto_osszeg","afa_osszeg","brutto_osszeg"]
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader(); w.writerows(rows)
    print("Saved →", OUT_CSV)

if __name__ == "__main__":
    main()
