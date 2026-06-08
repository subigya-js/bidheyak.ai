"""Central configuration for the ingestion pipeline.
Everything tunable lives here so nothing is hardcoded across the codebase.
"""

from __future__ import annotations

SITE_BASE_URL = "https://hr.parliament.gov.np"
BILLS_PATH = "/en/bills"

REGISTERED_BILLS_TYPE = "reg"
REGISTERED_BILLS_REF = "BILL"

REQUEST_DELAY_SECONDS = 1.0
REQUEST_TIMEOUT_SECONDS = 30
MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = 2.0

MAX_PAGES = 100

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)