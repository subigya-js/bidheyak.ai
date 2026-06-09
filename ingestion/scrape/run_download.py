"""Slice B: walk the registered bills, then download each one's PDF.

From the ingestion/ directory (with venv active):
    python scrape/run_download.py

Saves PDFs to ingestion/data/pdfs/{bill_id}.pdf and prints a summary.
"""

from __future__ import annotations

from collections import Counter

from download import download_bill_pdf
from http_client import build_session
from listings import walk_registered_bills


def main() -> None:
    session = build_session()
    bills = walk_registered_bills(session)
    print(f"Found {len(bills)} bills. Downloading registered PDFs...\n")

    summary: Counter[str] = Counter()
    for bill in bills:
        result = download_bill_pdf(session, bill)
        summary[result.status] += 1
        if result.status == "downloaded":
            print(f"  [ok] {bill.bill_id}  {bill.title[:50]}")

    print("\nSummary:")
    for status, count in summary.items():
        print(f"  {status}: {count}")


if __name__ == "__main__":
    main()