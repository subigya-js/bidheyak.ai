import sys

import requests
import urllib3
from bs4 import BeautifulSoup

# hr.parliament.gov.np ships an incomplete cert chain (no intermediate CA),
# so verification can't build a path to a trusted root. This is a throwaway
# probe — no sensitive data leaves the machine — so we skip verification.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

LISTING_URL = "https://hr.parliament.gov.np/en/bills?type=reg"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

TIMEOUT_SECONDS = 30


def main() -> None:
    try:
        response = requests.get(
            LISTING_URL,
            headers=HEADERS,
            timeout=TIMEOUT_SECONDS,
            verify=False,  # server's cert chain is incomplete; safe to skip for a probe
        )
    except requests.RequestException as error:
        print(f"Request failed entirely: {error!r}")
        sys.exit(1)

    print(f"HTTP status      : {response.status_code}")
    print(f"Response length  : {len(response.text)} chars")

    if response.status_code != 200:
        print(f"\nServer rejected plain request ({response.status_code}). Body:\n")
        print(response.text[:500])
        return

    soup = BeautifulSoup(response.text, "html.parser")
    bill_links = [
        a["href"] for a in soup.find_all("a", href=True)
        if "/bills/" in a["href"] and "type=" not in a["href"]
    ]
    print(f"Bill-detail links: {len(bill_links)}")
    print(f"Tables / rows    : {len(soup.find_all('table'))} / {len(soup.find_all('tr'))}")
    for link in bill_links[:5]:
        print(f"    {link}")

    print()
    if bill_links:
        print("Verdict: SERVER-RENDERED. Use requests + BeautifulSoup.")
    else:
        print("Verdict: likely JS-RENDERED. Use Playwright.")


if __name__ == "__main__":
    main()