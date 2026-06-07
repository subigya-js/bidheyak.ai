import sys
import requests
import urllib3
from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE = "https://hr.parliament.gov.np/en/bills?type=reg"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def unique_ids(html: str) -> set[str]:
    soup = BeautifulSoup(html, "html.parser")
    ids = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "/bills/" in href and "type=" not in href:
            ids.add(href.rstrip("/").split("/")[-1])
    return ids


def main() -> None:
    # Look for pagination links on page 1 to see how many pages exist.
    r1 = requests.get(BASE, headers=HEADERS, timeout=30, verify=False)
    soup = BeautifulSoup(r1.text, "html.parser")
    page_links = sorted({
        a["href"] for a in soup.find_all("a", href=True) if "page=" in a["href"]
    })
    print("Pagination links found on page 1:")
    for link in page_links:
        print("   ", link)

    # Compare page 1 vs page 2 vs a deliberately-too-high page.
    ids_p1 = unique_ids(r1.text)
    ids_p2 = unique_ids(requests.get(
        f"{BASE}&page=2", headers=HEADERS, timeout=30, verify=False).text)
    ids_p999 = unique_ids(requests.get(
        f"{BASE}&page=999", headers=HEADERS, timeout=30, verify=False).text)

    print(f"\nUnique bill IDs — page 1: {len(ids_p1)}")
    print(f"Unique bill IDs — page 2: {len(ids_p2)}")
    print(f"Unique bill IDs — page 999: {len(ids_p999)}")
    print(f"Page 1 and page 2 identical? {ids_p1 == ids_p2}")
    print(f"Page 999 same as page 1 (loops back)? {ids_p999 == ids_p1}")
    print(f"Page 999 empty? {len(ids_p999) == 0}")


if __name__ == "__main__":
    main()
