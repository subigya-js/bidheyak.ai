"""Extract clean Nepali Unicode text from a PDF using OCR.

Decision (from real-file comparison): these government PDFs mix legacy and
Unicode fonts in ways that corrupt text-layer extraction and that no font
mapping reliably fixes. OCR reads the RENDERED page, so it is font-agnostic
and produces correct Devanagari regardless of the underlying font chaos.

One universal path: render each page to an image, OCR it, join the text.
The OCR reader is built once and reused (model load is expensive).
"""

from __future__ import annotations

import re

import fitz  # PyMuPDF

# Render resolution. 300 DPI is a good accuracy/speed balance for OCR.
OCR_DPI = 300
# Language(s) for EasyOCR. 'ne' = Nepali (Devanagari).
OCR_LANGS = ["ne"]

_OCR_READER = None


def _get_reader():
    """Build the EasyOCR reader once and reuse it (model load is slow)."""
    global _OCR_READER
    if _OCR_READER is None:
        import easyocr
        _OCR_READER = easyocr.Reader(OCR_LANGS)
    return _OCR_READER


def _clean_text(text: str) -> str:
    """Light normalisation: trim lines, collapse runs of blank lines."""
    lines = [line.strip() for line in text.splitlines()]
    out: list[str] = []
    blank = 0
    for line in lines:
        if line:
            out.append(line)
            blank = 0
        else:
            blank += 1
            if blank <= 1:
                out.append("")
    return "\n".join(out).strip()


def extract_text(pdf_path) -> str:
    """Return clean Devanagari text for a PDF via OCR (font-agnostic)."""
    reader = _get_reader()
    parts: list[str] = []
    with fitz.open(pdf_path) as doc:
        for page in doc:
            pix = page.get_pixmap(dpi=OCR_DPI)
            # detail=0 returns just the text; paragraph=True groups lines.
            result = reader.readtext(pix.tobytes("png"), detail=0, paragraph=True)
            parts.append("\n".join(result))
    return _clean_text("\n".join(parts))