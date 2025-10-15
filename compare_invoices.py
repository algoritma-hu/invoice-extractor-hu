import csv, os, unicodedata

def strip_accents(s): 
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c)!='Mn')

def stem(path):
    b = os.path.basename(path)
    n, _ = os.path.splitext(b)
    return strip_accents(n.lower())

with open("invoices_hu/ground_truth.csv", encoding="utf-8") as f:
    gt_rows = list(csv.DictReader(f))

gt_by_exact = {r["file"]: r for r in gt_rows}
gt_by_stem  = {stem(r["file"]): r for r in gt_rows}

with open("invoices_hu/extracted_invoices_v2.csv", encoding="utf-8") as f:
    pred_rows = list(csv.DictReader(f))

fields = ["szamlaszam", "teljesites_datum", "brutto_osszeg", "valuta"]

def norm_num(s):
    s = (s or "").replace("\xa0"," ").strip()
    s = s.replace(".", " ").replace(",", " ")
    return "".join(ch for ch in s if ch.isdigit())

def norm_date(s):
    s = (s or "").strip().replace("/", "-").replace(".", "-")
    parts = s.split("-")
    if len(parts) == 3 and all(p.isdigit() for p in parts):
        y,m,d = parts
        if len(y)==4: return f"{y}-{int(m):02d}-{int(d):02d}"
    return s

def norm_val(field,val):
    if field=="brutto_osszeg": return norm_num(val)
    if field.endswith("_datum"): return norm_date(val)
    if field=="valuta": return (val or "").upper()
    return (val or "").strip()

total={k:0 for k in fields}
correct={k:0 for k in fields}
missing=0

for p in pred_rows:
    pf=p["file"]
    g=gt_by_exact.get(pf)
    if not g:
        alt=stem(pf)
        g=gt_by_stem.get(alt)
    if not g:
        # silently skip predictions without GT (like sample1.txt)
        continue

    print(f"\nFile: {pf}")
    for k in fields:
        pval=norm_val(k,p.get(k,""))
        gval=norm_val(k,g.get(k,""))
        total[k]+=1
        ok=(pval==gval)
        if ok: correct[k]+=1
        mark="✅" if ok else "❌"
        print(f" {mark} {k:20} GT: {gval} | PRED: {pval}")

print("\n== Accuracy ==")
for k in fields:
    if total[k]:
        acc=100*correct[k]/total[k]
        print(f"{k:20}: {correct[k]}/{total[k]} ({acc:.1f}%)")
print(f"Unmatched files (no GT): {missing}")
