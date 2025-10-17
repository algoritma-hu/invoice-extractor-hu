import csv, json, os, re
from pathlib import Path
from datetime import datetime

_slug = lambda s: re.sub(r'[^a-zA-Z0-9._-]+', '_', (s or "")).strip('_') or "unknown"

def ensure_dirs(out_root: Path, mapping: dict):
    (out_root / "logs").mkdir(parents=True, exist_ok=True)
    for sub in mapping.values():
        (out_root / sub).mkdir(parents=True, exist_ok=True)

def build_target_name(meta: dict, doc_type: str, src: Path) -> str:
    date = meta.get("issue_date") or meta.get("date") or datetime.utcnow().date().isoformat()
    key = meta.get("invoice_no") or meta.get("merchant") or src.stem
    return f"{date}_{_slug(str(key))}{src.suffix.lower()}"

def route(path: str, doc_type: str, meta: dict, cfg) -> str:
    src = Path(path)
    out_root = Path(cfg["paths"]["out_root"])
    subdir = cfg["routing"].get(f"{doc_type}s", doc_type)
    target_dir = out_root / subdir
    target_dir.mkdir(parents=True, exist_ok=True)
    name = build_target_name(meta, doc_type, src)
    dst = target_dir / name
    i = 1
    while dst.exists():
        stem, suf = os.path.splitext(name)
        dst = target_dir / f"{stem}__{i}{suf}"
        i += 1
    if not cfg["run"]["dry_run"]:
        src.replace(dst)
    return str(dst)

def append_logs(rows: list, cfg):
    out_root = Path(cfg["paths"]["out_root"])
    logs = out_root / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    # CSV
    csv_path = logs / "events.csv"
    write_header = not csv_path.exists()
    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=sorted(rows[0].keys()))
        if write_header: w.writeheader()
        for r in rows: w.writerow(r)
    # JSONL
    jsonl_path = logs / "events.jsonl"
    with open(jsonl_path, "a", encoding="utf-8") as f:
        for r in rows: f.write(json.dumps(r, ensure_ascii=False) + "\n")
