"""Download each bill's registered PDF to ingestion/data/pdfs/{bill_id}.pdf.

Idempotent: a PDF already on disk is skipped (cheap re-runs). Files are named
by bill_id (the unique key), never reg_number (which repeats). A bill with no
registered PDF is logged and skipped, per the data policy.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import config
from detail import find_registered_pdf_url
from http_client import FetchError, fetch, fetch_bytes

# ingestion/data/pdfs/  (this file lives in scrape/, so go up one level)
PDF_DIR = Path(__file__).resolve().parent.parent / "data" / "pdfs"


@dataclass(frozen=True)
class DownloadResult:
    bill_id: str
    status: str          # "downloaded" | "skipped_exists" | "no_pdf" | "error"
    pdf_path: str | None
    pdf_url: str | None


def download_bill_pdf(session, bill) -> DownloadResult:
    """Fetch one bill's detail page, find its registered PDF, save to disk."""
    target = PDF_DIR / f"{bill.bill_id}.pdf"

    if target.exists():
        return DownloadResult(bill.bill_id, "skipped_exists", str(target), None)

    try:
        detail_html = fetch(session, bill.detail_url)
    except FetchError as error:
        print(f"  [error] {bill.bill_id}: detail page failed: {error}")
        return DownloadResult(bill.bill_id, "error", None, None)

    pdf_url = find_registered_pdf_url(detail_html)
    if pdf_url is None:
        print(f"  [no_pdf] {bill.bill_id}: no registered PDF on page")
        return DownloadResult(bill.bill_id, "no_pdf", None, None)

    try:
        data = fetch_bytes(session, pdf_url)
    except FetchError as error:
        print(f"  [error] {bill.bill_id}: PDF download failed: {error}")
        return DownloadResult(bill.bill_id, "error", None, pdf_url)

    PDF_DIR.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    return DownloadResult(bill.bill_id, "downloaded", str(target), pdf_url)
