import re, csv, glob, os, io, unicodedata

# ---------- helpers ----------
def norm_num(s: str) -> str:
    s = (s or "").replace("\xa0"," ").strip()
    s = s.replace(".", " ").replace(",", " ")
    return "".join(ch for ch in s if ch.isdigit())

def norm_date(s: str) -> str:
    s = (s or "").strip().replace("/", "-").replace(".", "-")
    parts = s.split("-")
    if len(parts) == 3 and all(p.isdigit() for p in parts):
        y, m, d = parts
        if len(y)==4: return f"{y}-{int(m):02d}-{int(d):02d}"
    return s

def strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")

# ---------- regexes ----------
RX_INVOICE_NO = re.compile(r"(?:Sz[áa]mla(?:\s*sz[aá]ma)?|Sz[áa]mlasz[aá]m|Bizonylat(?:\s*sz[aá]ma)?)\s*[:#]?\s*([A-Z0-9/-]{3,})", re.I)
RX_DATE_TELJ  = re.compile(r"Teljes[íi]t[ée]s(?:\s*d[aá]tuma)?\s*[:#]?\s*([0-9]{4}[-./][0-9]{2}[-./][0-9]{2})", re.I)

# Amount candidates: look for labeled totals; allow number on same or next line.
LABEL_PATTERNS = [
    (re.compile(r"Fizetend[őo]\b.*", re.I),                         4),
    (re.compile(r"Brutt[oó].{0,20}(?:v[ée]g[öo]sszeg|összeg)\b", re.I), 4),
    (re.compile(r"(?:V[ée]g[öo]sszeg|Összesen)\b.*", re.I),         3),
    (re.compile(r"Brutt[oó]\b.*", re.I),                            3),
]
# generic number token with optional Ft
RX_NUM = re.compile(r"([\d][\d\s.,]{1,15})\s*(?:Ft|HUF)?\b", re.I)

NEGATIVE_CONTEXT = re.compile(r"\b(Nett[oó]|ÁFA|AFA|Ad[oó])\b", re.I)

def find_brutto_amount(txt: str) -> str:
    lines = txt.splitlines()
    n = len(lines)
    candidates = []

    for i, line in enumerate(lines):
        for rx_label, base_score in LABEL_PATTERNS:
            if rx_label.search(line):
                # same line amounts
                for m in RX_NUM.finditer(line):
                    amt = norm_num(m.group(1))
                    if not amt: continue
                    score = base_score
                    if NEGATIVE_CONTEXT.search(line): score -= 3
                    candidates.append((score, int(amt), i, "same-line"))
                # next line amounts (common in PDFs)
                if i+1 < n:
                    next_line = lines[i+1]
                    for m in RX_NUM.finditer(next_line):
                        amt = norm_num(m.group(1))
                        if not amt: continue
                        score = base_score - 1  # slightly lower than same-line
                        if NEGATIVE_CONTEXT.search(next_line): score -= 3
                        candidates.append((score, int(amt), i+1, "next-line"))

    # If none found near labels, fallback to global max number ≥ 5_000, downweight NETTÓ/ÁFA contexts
    if not candidates:
        best = None
        for i, line in enumerate(lines):
            for m in RX_NUM.finditer(line):
                amt = norm_num(m.group(1))
                if not amt: continue
                val = int(amt)
                if val < 5000:  # ignore tiny line items
                    continue
                score = 1
                if NEGATIVE_CONTEXT.search(line):
                    score -= 3
                tup = (score, val, i, "fallback")
                if best is None or tup > best:
                    best = tup
        if best:
            candidates.append(best)

    if not candidates:
        return ""

    # choose by score, then by amount
    candidates.sort(reverse=True)  # sorts by score -> amount -> line idx -> origin
    return str(candidates[0][1])

def extract_from_text(txt: str) -> dict:
    out = {}
    if m := RX_INVOICE_NO.search(txt):
        out["szamlaszam"] = m.group(1).strip()
    if m := RX_DATE_TELJ.search(txt):
        out["teljesites_datum"] = norm_date(m.group(1))
    brutto = find_brutto_amount(txt)
    if brutto:
        out["brutto_osszeg"] = brutto
    # default currency if seen
    out["valuta"] = "HUF" if "HUF" in txt or "Ft" in txt or "ft" in txt else "HUF"
    return out

rows = []
for path in sorted(glob.glob("invoices_hu/*.txt")):
    fname = os.path.basename(path)
    with io.open(path, "r", encoding="utf-8", errors="ignore") as f:
        txt = f.read()
    data = extract_from_text(txt)
    data.setdefault("szamlaszam", "")
    data.setdefault("teljesites_datum", "")
    data.setdefault("brutto_osszeg", "")
    data.setdefault("valuta", "HUF")
    rows.append({"file": fname, **data})

with open("invoices_hu/extracted_invoices_v2.csv", "w", newline="", encoding="utf-8") as w:
    wr = csv.DictWriter(w, fieldnames=["file","szamlaszam","teljesites_datum","brutto_osszeg","valuta"])
    wr.writeheader()
    wr.writerows(rows)

print(f"Wrote invoices_hu/extracted_invoices_v2.csv with {len(rows)} rows.")
