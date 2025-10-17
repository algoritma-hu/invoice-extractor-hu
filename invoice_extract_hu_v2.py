import os, re, sys, csv, subprocess

IN_DIR = "invoices_hu"
OUT_CSV = "extracted_invoices_v2.csv"

RX = {
    "szamlaszam": re.compile(r"Számlaszám:\s*([A-Z0-9\-_/]+)", re.I),
    "kibocsatas_datum": re.compile(r"(Kibocsátás dátuma|Kelt):\s*([0-9]{4}[-./][0-9]{2}[-./][0-9]{2})", re.I),
    "teljesites_datum": re.compile(r"Teljesítés dátuma:\s*([0-9]{4}[-./][0-9]{2}[-./][0-9]{2})", re.I),
    "hatarido": re.compile(r"(Fizetési határidő|Határidő):\s*([0-9]{4}[-./][0-9]{2}[-./][0-9]{2})", re.I),
    "fizmod": re.compile(r"Fizetési mód:\s*([A-Za-zÁÉÍÓÖŐÚÜŰáéíóöőúüű]+)", re.I),
    "netto_osszeg": re.compile(r"Nettó:\s*([\d\s\.,]+)\s*Ft", re.I),
    "afa_osszeg": re.compile(r"ÁFA\s*\(\d+%\):\s*([\d\s\.,]+)\s*Ft", re.I),
    "brutto_osszeg": re.compile(r"Végösszeg\s*\(bruttó\):\s*([\d\s\.,]+)\s*Ft", re.I),
}

def normint(s):
    if not s: return None
    s = s.replace("\u00a0"," ").replace(" ", "").replace(".", "").replace(",", "")
    return int(s) if s.isdigit() else None

def pdftotext_text(pdf_path: str) -> str:
    # requires: poppler-utils (pdftotext)
    res = subprocess.run(
        ["pdftotext", "-layout", pdf_path, "-"],
        capture_output=True, check=True
    )
    return res.stdout.decode("utf-8", errors="ignore")

def extract_text(pdf_path: str) -> str:
    # Try embedded text first
    try:
        txt = pdftotext_text(pdf_path)
        if txt.strip():
            return txt
    except Exception:
        pass
    # Fallback to OCR (for scans)
    from pdf2image import convert_from_path
    import pytesseract
    pages = convert_from_path(pdf_path, dpi=200)
    return "\n".join(pytesseract.image_to_string(p, lang="hun+eng") for p in pages)

def find_one(rx, text, grp=1, last=False):
    m = (list(rx.finditer(text)) or [None])[-1] if last else rx.search(text)
    return m.group(grp).strip() if m else None

def extract_fields(text: str):
    d = {}
    d["szamlaszam"] = find_one(RX["szamlaszam"], text)
    d["kibocsatas_datum"] = find_one(RX["kibocsatas_datum"], text, grp=2)
    d["teljesites_datum"] = find_one(RX["teljesites_datum"], text)
    d["hatarido"] = find_one(RX["hatarido"], text, grp=2)
    d["fizmod"] = find_one(RX["fizmod"], text)

    d["netto_osszeg"] = normint(find_one(RX["netto_osszeg"], text, last=True))
    d["afa_osszeg"] = normint(find_one(RX["afa_osszeg"], text, last=True))
    d["brutto_osszeg"] = normint(find_one(RX["brutto_osszeg"], text, last=True))

    # Parties: first non-empty line after headers
    d["elado_nev"] = None
    d["vevo_nev"] = None
    m = re.search(r"Eladó\s*\(Kibocsátó\)\s*\n([^\n].*)", text, re.I)
    if m: d["elado_nev"] = m.group(1).strip()
    m = re.search(r"Vevő\s*\n([^\n].*)", text, re.I)
    if m: d["vevo_nev"] = m.group(1).strip()
    return d

def main():
    files = sorted(f for f in os.listdir(IN_DIR) if f.lower().endswith(".pdf"))
    if not files:
        print("No PDFs in", IN_DIR); sys.exit(1)

    rows = []
    for f in files:
        path = os.path.join(IN_DIR, f)
        text = extract_text(path)
        data = extract_fields(text)
        data["file"] = f
        rows.append(data)
        print(f"{f} -> {data}")

    cols = [
        "file","szamlaszam","kibocsatas_datum","teljesites_datum","hatarido",
        "fizmod","elado_nev","vevo_nev","netto_osszeg","afa_osszeg","brutto_osszeg"
    ]
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as fp:
        w = csv.DictWriter(fp, fieldnames=cols)
        w.writeheader(); w.writerows(rows)
    print("Saved ->", OUT_CSV)

if __name__ == "__main__":
    main()
