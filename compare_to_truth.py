import csv

truth_path = "invoices_hu/ground_truth.csv"
pred_path = "extracted_invoices.csv"
keys = ["szamlaszam","kibocsatas_datum","teljesites_datum","hatarido"]

truth = {r["file"]: r for r in csv.DictReader(open(truth_path, encoding="utf-8"))}
preds = list(csv.DictReader(open(pred_path, encoding="utf-8")))

total = 0; correct = 0
for r in preds:
    f = r["file"]
    if f not in truth: continue
    total += len(keys)
    for k in keys:
        if r.get(k,"").strip() == truth[f].get(k,"").strip():
            correct += 1
print(f"Field accuracy (basic keys): {correct}/{total} = {correct/total:.1%}" if total else "No comparable rows.")
