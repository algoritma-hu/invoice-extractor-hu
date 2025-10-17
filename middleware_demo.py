import argparse, time, yaml
from pathlib import Path
from classify import classify
from extractors.hu_invoice import extract_invoice
from extractors.receipt_basic import extract_receipt
from routing import route, append_logs, ensure_dirs
from notify import send_email

def load_cfg(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def process_once(cfg):
    inbox = Path(cfg["paths"]["inbox"])
    out_root = Path(cfg["paths"]["out_root"])
    ensure_dirs(out_root, cfg["routing"])

    files = [p for p in inbox.iterdir() if p.is_file()]
    rows = []
    for p in files:
        doc_type = classify(str(p))
        if doc_type == "invoice":
            meta = extract_invoice(str(p))
        elif doc_type == "receipt":
            meta = extract_receipt(str(p))
        else:
            meta = {"doc_type":"other", "file":p.name, "confidence":0.2}
        dest = route(str(p), doc_type, meta, cfg)
        rec = {"src": str(p), "dest": dest, "doc_type": doc_type, **meta}
        rows.append(rec)

    if rows:
        append_logs(rows, cfg)
        try:
            send_email(rows, cfg)
        except Exception as e:
            # Do not fail the run on email issues
            print(f"[notify] skipped or failed: {e}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.yaml")
    args = ap.parse_args()
    cfg = load_cfg(args.config)

    if cfg["run"]["continuous"]:
        while True:
            process_once(cfg)
            time.sleep(3)
    else:
        process_once(cfg)

if __name__ == "__main__":
    main()
