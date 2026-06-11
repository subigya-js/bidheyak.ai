"""Extract text from every downloaded PDF and save it to data/text/{bill_id}.txt.

From the ingestion/ directory (venv active):
    python extract/run_extract.py

Idempotent: a .txt that already exists is skipped, so re-runs only OCR new
PDFs. OCR is slow (minutes per file) — the first full run takes a while.
"""

from __future__ import annotations

from pathlib import Path

from extract import extract_text

PDF_DIR = Path(__file__).resolve().parent.parent / "data" / "pdfs"
TEXT_DIR = Path(__file__).resolve().parent.parent / "data" / "text"


def main() -> None:
    pdfs = sorted(PDF_DIR.glob("*.pdf"))
    if not pdfs:
        print(f"No PDFs in {PDF_DIR}")
        return

    TEXT_DIR.mkdir(parents=True, exist_ok=True)
    done = skipped = failed = 0

    for path in pdfs:
        out_path = TEXT_DIR / f"{path.stem}.txt"
        if out_path.exists():
            skipped += 1
            continue
        try:
            text = extract_text(path)
            out_path.write_text(text, encoding="utf-8")
            done += 1
            print(f"  [ok] {path.stem}  ({len(text)} chars)")
        except Exception as error:
            failed += 1
            print(f"  [error] {path.stem}: {error!r}")

    print(f"\nDone. extracted={done}, skipped={skipped}, failed={failed}")
    print(f"Text files in: {TEXT_DIR}")


if __name__ == "__main__":
    main()