"""Walk the registered-bills listing and extract one record per bill.
Cell positions (from real HTML):
    Cell 1: Registration No.
    Cell 2: Date
    Cell 3: Title (link)
    Cell 4: Ministry

Since the registration number is repeated on multiple bills in the same table. So, we use bill_id (Extraced from bill URL) as the primary key.

The detail URL is taken from the View button, which is present on EVERY row (unlike the title, which some rows lack). 
To be resilient to shifting cell counts, we locate the detail link by it's /bills/<id> URL pattern rather than a fixed cell index.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from bs4 import BeautifulSoup

import config
from http_client import fetch, FetchError

# A bill detail link looks like .../bills/<id> (NOT a listing link with ?type=).
_DETAIL_RE = re.compile(r"/bills/[A-Za-z0-9]+")


@dataclass(frozen=True)
class BillListItem:
    bill_id: str
    reg_number: str
    registration_date: str
    title: str
    ministry: str
    detail_url: str


def _clean(text: str) -> str:
    return " ".join(text.split()).strip()


def _bill_id_from_url(url: str) -> str | None:
    """The site's own unique id, e.g. .../bills/vSXD5e70 -> 'vSXD5e70'."""
    match = _DETAIL_RE.search(url)
    return match.group(0).rsplit("/", 1)[-1] if match else None


def _detail_url_in_row(row) -> str | None:
    """Find the bill detail link anywhere in the row (View button or title)."""
    for a in row.find_all("a", href=True):
        href = a["href"]
        if "/bills/" in href and "type=" not in href and _DETAIL_RE.search(href):
            return href
    return None


def parse_listing_page(html: str) -> list[BillListItem]:
    soup = BeautifulSoup(html, "html.parser")
    items: list[BillListItem] = []

    for row in soup.find_all("tr"):  # Find all rows in the table
        cells = row.find_all("td")  # Find all cells in the row
        if len(cells) < 5:
            continue  # header/layout row

        detail_url = _detail_url_in_row(row)
        if detail_url is None:
            continue  # no detail link = not a real bill row
        
        bill_id = _bill_id_from_url(detail_url)
        if bill_id is None:
            continue

        reg_number = _clean(cells[1].get_text())
        if not reg_number:
            print(f" [skip] row missing reg_number: {detail_url}")
            continue

        title_link = cells[3].find("a")
        title = _clean(title_link.get_text()) if title_link else _clean(
            cells[3].get_text())
        if not title:
            title = f"Untitled bill {reg_number}"

        items.append(BillListItem(
            bill_id=bill_id,
            reg_number=reg_number,
            registration_date=_clean(cells[2].get_text()),
            title=title,
            ministry=_clean(cells[4].get_text()),
            detail_url=detail_url
        ))

    return items


def _listing_url(page: int) -> str:
    base = (
        f"{config.SITE_BASE_URL}{config.BILLS_PATH}"
        f"?type={config.REGISTERED_BILLS_TYPE}"
        f"&ref={config.REGISTERED_BILLS_REF}"
    )
    if page == 1:
        return base
    return f"{base}&page={page}"


def walk_registered_bills(session) -> list[BillListItem]:
    all_items: dict[str, BillListItem] = {}
    page = 1

    while page <= config.MAX_PAGES:
        try:
            html = fetch(session, _listing_url(page))
        except FetchError as error:
            if page == 1:
                # First page failed = we have nothing. This is a real failure.
                raise
            # A later page failing, after we already collected bills, is the
            # site's messy "past the end" signal. Stop, but make it visible.
            print(
                f"  [stop] page {page} failed, treating as end of data: {error}")
            break

        items = parse_listing_page(html)
        if not items:
            break  # empty page = clean, trustworthy end

        for item in items:
            all_items.setdefault(item.bill_id, item)
        page += 1

    return list(all_items.values())
