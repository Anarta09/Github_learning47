# token_scheduler.py
import threading
import time
import logging
from typing import Optional

from dependencies.auth_dep import get_admin_token  # adjust import if path different

# Global state
_admin_token: Optional[str] = None
_lock = threading.Lock()
_stop_event = threading.Event()

# 7 hours 45 minutes in seconds
_REFRESH_INTERVAL = int(4*60)

# internal thread reference
_thread: Optional[threading.Thread] = None


def _fetch_and_store_token():
    """Fetch token using get_admin_token() and store it thread-safely."""
    global _admin_token
    try:
        new_token = get_admin_token()
        with _lock:
            _admin_token = new_token
        logging.info("Admin token refreshed.")
    except Exception as e:
        logging.exception("Failed to refresh admin token: %s", e)


def _scheduler_loop():
    """Background loop that refreshes token immediately and then every interval."""
    # First immediate fetch so app doesn't wait for the first interval
    _fetch_and_store_token()

    # Then loop until stop requested
    while not _stop_event.wait(_REFRESH_INTERVAL):
        _fetch_and_store_token()


def start_token_scheduler():
    """Start background thread for token refresh (idempotent)."""
    global _thread
    if _thread and _thread.is_alive():
        logging.debug("Token scheduler already running.")
        return

    _stop_event.clear()
    _thread = threading.Thread(target=_scheduler_loop, name="AdminTokenRefresher", daemon=True)
    _thread.start()
    logging.info("Started admin token scheduler (interval: %s seconds).", _REFRESH_INTERVAL)


def stop_token_scheduler():
    """Signal background thread to stop and wait for it to finish."""
    _stop_event.set()
    if _thread:
        _thread.join(timeout=10)
    logging.info("Stopped admin token scheduler.")


def get_current_admin_token(wait_for_first: bool = True) -> Optional[str]:
    """
    Return current admin token.
    If token is not yet available and wait_for_first=True, wait a short time (up to ~5s).
    """
    global _admin_token
    if _admin_token is None and wait_for_first:
        # give background thread a little time to fetch token
        # we'll loop small sleeps up to a total timeout
        timeout = 5.0
        interval = 0.1
        waited = 0.0
        while _admin_token is None and waited < timeout:
            time.sleep(interval)
            waited += interval
    with _lock:
        return _admin_token
