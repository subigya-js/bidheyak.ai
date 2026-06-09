"""Classify each downloaded PDF as unicode | preeti | scanned.

The decision per file, using three cheap checks:
  1. Extract the text layer with PyMuPDF.
  2. Almost no text at all            -> SCANNED  (image pages, needs OCR)
  3. Has text but little Devanagari   -> PREETI   (legacy font = Latin gibberish)
  4. Has text, plenty of Devanagari   -> UNICODE  (use directly)

This script ONLY reports. It writes nothing and changes no files — its job is
to reveal the real mix across the corpus before we build extraction paths.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import fitz  # PyMuPDF

PDF_DIR = Path(__file__).resolve().parent.parent / "data" / "pdfs"

# Tunable thresholds (we validate these against real output and adjust).
MIN_CHARS_FOR_TEXT = 100        # below this total -> treat as scanned
MIN_DEVANAGARI_RATIO = 0.20     # of letters, fraction that must be Devanagari


def _devanagari_ratio(text: str) -> float:
    """Fraction of alphabetic chars that are Devanagari (U+0900–U+097F)."""
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return 0.0
    devanagari = [c for c in letters if "\u0900" <= c <= "\u097f"]
    return len(devanagari) / len(letters)


@dataclass(frozen=True)
class Detection:
    bill_id: str
    kind: str            # "unicode" | "preeti" | "scanned"
    char_count: int
    devanagari_ratio: float


def detect_pdf(path: Path) -> Detection:
    bill_id = path.stem
    with fitz.open(path) as doc:
        text = "".join(page.get_text() for page in doc)

    stripped = text.strip()
    if len(stripped) < MIN_CHARS_FOR_TEXT:
        return Detection(bill_id, "scanned", len(stripped), 0.0)

    ratio = _devanagari_ratio(stripped)
    kind = "unicode" if ratio >= MIN_DEVANAGARI_RATIO else "preeti"
    return Detection(bill_id, kind, len(stripped), ratio)


def main() -> None:
    pdfs = sorted(PDF_DIR.glob("*.pdf"))
    if not pdfs:
        print(f"No PDFs found in {PDF_DIR}")
        return

    print(f"Classifying {len(pdfs)} PDFs...\n")
    counts = {"unicode": 0, "preeti": 0, "scanned": 0}

    for path in pdfs:
        d = detect_pdf(path)
        counts[d.kind] += 1
        print(f"  {d.kind:8}  {d.bill_id:10}  "
              f"chars={d.char_count:<7} devanagari={d.devanagari_ratio:.2f}")

    print("\nMix across the corpus:")
    for kind, n in counts.items():
        print(f"  {kind}: {n}")


if __name__ == "__main__":
    main()