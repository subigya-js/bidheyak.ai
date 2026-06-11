"""OCR PDFs on a Modal GPU instead of the local Mac.

Run from ingestion/extract/ (after `modal setup`):
    modal run modal_ocr.py

It reads PDFs from ../data/pdfs/, sends each one's bytes to a GPU function
that OCRs it, and writes the result to ../data/text/{bill_id}.txt.
Idempotent: a .txt that already exists locally is skipped.

Cost note: you only pay for GPU seconds while OCR runs. No storage, no idle
cost. The whole 32-file batch is a few minutes of GPU time — cents.
"""

from __future__ import annotations

from pathlib import Path

import modal

# 1) The cloud ENVIRONMENT: a container image with our OCR libraries.
#    Modal builds this once and caches it.
image = (
    modal.Image.debian_slim()
    .apt_install("libgl1", "libglib2.0-0")          # system deps easyocr/opencv need
    .pip_install("easyocr", "pymupdf")
)

app = modal.App("bidheyak-ocr", image=image)

# Local paths (resolved on YOUR machine, not in the cloud).
PDF_DIR = Path(__file__).resolve().parent.parent / "data" / "pdfs"
TEXT_DIR = Path(__file__).resolve().parent.parent / "data" / "text"

OCR_DPI = 300
OCR_LANGS = ["ne"]


# 2) The GPU FUNCTION: runs in the cloud. gpu="A10G" is a modest, cheap GPU.
#    The EasyOCR model is loaded once per warm container and reused.
@app.function(gpu="A10G", timeout=3600)
def ocr_pdf(pdf_bytes: bytes) -> str:
    import fitz
    import easyocr

    reader = easyocr.Reader(OCR_LANGS, gpu=True)
    parts: list[str] = []
    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        for page in doc:
            pix = page.get_pixmap(dpi=OCR_DPI)
            result = reader.readtext(pix.tobytes("png"), detail=0, paragraph=True)
            parts.append("\n".join(result))
    return "\n".join(parts)


# 3) The LOCAL ENTRYPOINT: runs on your Mac, orchestrates the batch.
@app.local_entrypoint()
def main() -> None:
    TEXT_DIR.mkdir(parents=True, exist_ok=True)
    pdfs = sorted(PDF_DIR.glob("*.pdf"))

    # Decide which still need OCR (skip ones already done locally).
    pending = [p for p in pdfs if not (TEXT_DIR / f"{p.stem}.txt").exists()]
    print(f"{len(pdfs)} PDFs total, {len(pending)} need OCR.")
    if not pending:
        print("Nothing to do.")
        return

    # Send all pending PDFs to the GPU in parallel; results stream back.
    names = [p.stem for p in pending]
    payloads = [p.read_bytes() for p in pending]
    for name, text in zip(names, ocr_pdf.map(payloads)):
        (TEXT_DIR / f"{name}.txt").write_text(text, encoding="utf-8")
        print(f"  [ok] {name}  ({len(text)} chars)")

    print(f"\nDone. Text files in {TEXT_DIR}")