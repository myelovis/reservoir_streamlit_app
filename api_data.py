"""Bounded HTTP requests for Streamlit data sources."""
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class ApiDataError(RuntimeError):
    """An upstream request failed or did not return usable observations."""


def get_response(source, url, params=None):
    retries = Retry(total=2, backoff_factor=1, status_forcelist=(500, 502, 503, 504),
                    respect_retry_after_header=False)
    with requests.Session() as session:
        session.mount("https://", HTTPAdapter(max_retries=retries))
        try:
            response = session.get(url, params=params, timeout=(8, 45))
            response.raise_for_status()
        except requests.HTTPError as error:
            status = error.response.status_code
            if status == 429:
                raise ApiDataError(f"{source} reached its request limit. Wait and retry.") from None
            raise ApiDataError(f"{source} returned HTTP {status}. Check access or try again later.") from None
        except requests.RequestException:
            raise ApiDataError(f"Could not connect to {source}. Check the connection and retry.") from None
    return response


def get_json(source, url, params=None):
    response = get_response(source, url, params)
    try:
        return response.json()
    except ValueError:
        raise ApiDataError(f"{source} did not return valid JSON. Try again later.") from None
