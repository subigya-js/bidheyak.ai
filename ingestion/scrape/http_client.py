"""HTTP Layer: secure SSL fix, polite delays, retries, shared session.

The site ships an incomplete certificate chain, so stock verification fails.
We fix it the SECURE way truststore (verify against the OS trust store),
NOT by disabling verification. This code runs on a schedule, so it must never run with certificate checking off.
"""

from __future__ import annotations
import time
import requests

try:
    import truststore
    truststore.inject_into_ssl()
    _TRUSTSTORE_ACTIVE = True
except ImportError:
    _TRUSTSTORE_ACTIVE = False

import config

class FetchError(RuntimeError):
    """Raised when a URL cannot be retrieved after all retries."""


def build_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({
        "User-Agent": config.USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    })
    return session


def fetch(session: requests.Session, url: str) -> str:
    last_error: Exception | None = None
    for attempt in range(1, config.MAX_RETRIES + 1):
        try:
            response = session.get(url, timeout=config.REQUEST_TIMEOUT_SECONDS)
            if response.status_code >= 500:
                raise FetchError(
                    f"Server error {response.status_code} for {url}")
            response.raise_for_status()
            return response.text
        except (requests.RequestException, FetchError) as error:
            last_error = error
            if attempt < config.MAX_RETRIES:
                time.sleep(config.RETRY_BACKOFF_SECONDS * attempt)
        finally:
            time.sleep(config.REQUEST_DELAY_SECONDS)
    raise FetchError(
        f"Failed to fetch {url} after {config.MAX_RETRIES} tries: {last_error!r}")
