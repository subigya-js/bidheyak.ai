"""Run the registered-bills listing walker and print what it finds.

From the ingestion/ directory, with the venv active:
    python scrape/run_listings.py

This step only ENUMERATES bills — no PDF download, no database yet.
Goal: confirm we get 32 bills with correct titles before moving on.
"""

from __future__ import annotations

from http_client import _TRUSTSTORE_ACTIVE, build_session
from listings import walk_registered_bills


def main() -> None:
    if not _TRUSTSTORE_ACTIVE:
        print("WARNING: truststore not installed. Run `pip install truststore`.\n")

    session = build_session()
    bills = walk_registered_bills(session)

    print(f"\nDiscovered {len(bills)} registered bills:\n")
    for bill in bills:
        print(f"  [{bill.reg_number}] {bill.title} · {bill.bill_id}")
        print(f"        {bill.ministry} · {bill.registration_date}")

    print(f"\nTotal: {len(bills)} bills")


if __name__ == "__main__":
    main()
