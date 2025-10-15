# Invoice Extractor (HU) — PDF → TXT → Structured CSV → Accuracy Report

Production-lean Phase-1 pipeline that converts Hungarian invoices (PDF) to text, extracts key fields with robust regex heuristics, and compares results against a ground-truth CSV.

## Why this matters
- **Realistic**: Works on mixed-layout PDFs (text or OCR) common in Hungarian SMEs.
- **Deterministic & cheap**: No external APIs; all local tools (Poppler, Tesseract optional).
- **Measurable**: Instant per-field accuracy vs. ground truth.

---

## Quick Start

### System dependencies (Ubuntu / Pop!\_OS)
```bash
sudo apt update
sudo apt install -y poppler-utils           # pdftotext
# Optional OCR for scanned PDFs:
sudo apt install -y ocrmypdf tesseract-ocr tesseract-ocr-hun
