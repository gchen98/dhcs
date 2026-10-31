import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def get_retry_session(total_retries:int)->requests.Session:
    # 1. Define your retry strategy
    retry_strategy = Retry(
        total=total_retries,                                      # Total number of retries to allow
        backoff_factor=1,
        status_forcelist=[408, 429, 500, 502, 503, 504], # HTTP status codes to retry on
        allowed_methods=["HEAD", "GET", "OPTIONS"],   # Only retry idempotent HTTP methods
        raise_on_status=False # Return response instead of raising exception if final retry fails
    )

    # 2. Create an HTTP adapter with the strategy
    adapter = HTTPAdapter(max_retries=retry_strategy)
    # 3. Create a session and mount the adapter for both HTTP and HTTPS
    session = requests.Session()
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

