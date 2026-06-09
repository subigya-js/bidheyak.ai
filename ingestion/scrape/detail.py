"""Find the Registered Bill PDF link on a bill's detail page.

The detail page has an info table whose rows pair a label cell ("Registered
Bill" / "Authenticated Bill") with a cell containing a download link. We scope
to the row labelled "Registered Bill" so we never grab the authenticated PDF
by mistake. A bill may have no registered PDF ("No File") -> returns None.
"""

from __future__ import annotations

from bs4 import BeautifulSoup

REGISTERED_LABEL = "registered bill"


def find_registered_pdf_url(html: str) -> str | None:
    soup = BeautifulSoup(html, "html.parser")

    for row in soup.find_all("tr"):
        cells = row.find_all("td")
        if len(cells) < 2:
            continue

        label = " ".join(cells[0].get_text().split()).strip().lower()
        if label != REGISTERED_LABEL:
            continue

        # This is the "Registered Bill" row. Find a .pdf link within it.
        for a in row.find_all("a", href=True):
            href = a["href"]
            if href.lower().endswith(".pdf"):
                return href
        return None  # row found but no file ("No File")

    return None  # no "Registered Bill" row at all
