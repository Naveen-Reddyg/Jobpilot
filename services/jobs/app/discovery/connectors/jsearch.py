from __future__ import annotations

import json
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


JSEARCH_HOST = "jsearch.p.rapidapi.com"
JSEARCH_URL = f"https://{JSEARCH_HOST}/search-v2"


class JSearchError(Exception):
    pass


def search_jobs(*, api_key: str, query: str, country: str = "us") -> list[dict[str, str | None]]:
    if not api_key:
        raise JSearchError("RapidAPI is not configured.")

    query_string = urlencode(
        {
            "country": country,
            "work_from_home": "true",
            "num_pages": 1,
            "date_posted": "all",
            "query": query,
        }
    )
    request = Request(
        f"{JSEARCH_URL}?{query_string}",
        headers={"X-RapidAPI-Key": api_key, "X-RapidAPI-Host": JSEARCH_HOST},
        method="GET",
    )
    try:
        with urlopen(request, timeout=20) as response:
            payload = json.loads(response.read())
    except HTTPError as error:
        try:
            provider_detail = _safe_provider_detail(error.read(2048))
        except (AttributeError, OSError):
            provider_detail = ""
        provider_error = provider_detail.casefold()
        if error.code == 401:
            raise JSearchError("RapidAPI returned HTTP 401. Verify that the API key is correct.") from None
        if error.code == 403:
            if "not subscribed" in provider_error or "subscription required" in provider_error:
                raise JSearchError(
                    "RapidAPI reports this app is not subscribed to JSearch. Subscribe using the same RapidAPI account as this API key."
                ) from None
            if any(term in provider_error for term in ("quota", "rate limit", "limit exceeded")):
                raise JSearchError("JSearch plan quota or rate limit was reached. Check plan usage and reset time.") from None
            raise JSearchError(
                "RapidAPI returned HTTP 403. Verify that you subscribed to JSearch and your plan allows this endpoint."
            ) from None
        if error.code == 404:
            if any(term in provider_error for term in ("endpoint not found", "route not found", "api not found")):
                raise JSearchError(
                    "RapidAPI could not find the JSearch endpoint. Verify GET /search-v2 on jsearch.p.rapidapi.com."
                ) from None
            if provider_detail:
                raise JSearchError(f"JSearch returned HTTP 404: {provider_detail}") from None
            raise JSearchError(
                "JSearch returned HTTP 404. Verify the JSearch Job Search endpoint and RapidAPI subscription."
            ) from None
        raise JSearchError(f"JSearch returned HTTP {error.code}.") from None
    except (URLError, TimeoutError):
        raise JSearchError("JSearch could not be reached.") from None
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise JSearchError("JSearch returned invalid JSON.") from None

    records = _job_records(payload)
    if records is None:
        top_level_fields = ", ".join(payload.keys()) if isinstance(payload, dict) else type(payload).__name__
        data = payload.get("data") if isinstance(payload, dict) else None
        data_fields = ", ".join(data.keys()) if isinstance(data, dict) else type(data).__name__
        raise JSearchError(
            f"JSearch returned an unexpected response format (fields: {top_level_fields}; data: {data_fields})."
        )

    jobs: list[dict[str, str | None]] = []
    for record in records:
        if not isinstance(record, dict):
            continue
        job_id = _text(record.get("job_id"))
        title = _text(record.get("job_title"))
        company = _text(record.get("employer_name"))
        apply_url = _text(record.get("job_apply_link")) or _text(record.get("job_google_link"))
        if not job_id or not title or not company or not apply_url:
            continue
        location = ", ".join(
            part
            for part in (
                _text(record.get("job_city")),
                _text(record.get("job_state")),
                _text(record.get("job_country")),
            )
            if part
        )
        if not location and record.get("job_is_remote") is True:
            location = "Remote"
        jobs.append(
            {
                "source_job_id": job_id,
                "title": title,
                "company": company,
                "location": location,
                "description_excerpt": (_text(record.get("job_description")) or "")[:4000],
                "application_url": apply_url,
                "published_at": _text(record.get("job_posted_at_datetime_utc")),
            }
        )
    return jobs


def _text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized or None


def _job_records(payload: object) -> list[object] | None:
    if not isinstance(payload, dict):
        return None

    def find_records(value: object) -> list[object] | None:
        if isinstance(value, list):
            return value
        if not isinstance(value, dict):
            return None
        if _text(value.get("job_id")):
            return [value]
        for field in ("jobs", "job_results", "results", "items", "records", "data"):
            records = find_records(value.get(field))
            if records is not None:
                return records
        return None

    return find_records(payload.get("data"))


def _safe_provider_detail(body: bytes) -> str:
    try:
        payload = json.loads(body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return ""
    if not isinstance(payload, dict):
        return ""
    for field in ("message", "error", "detail"):
        value = payload.get(field)
        if isinstance(value, dict):
            value = value.get("message")
        if isinstance(value, str) and value.strip():
            detail = re.sub(
                r"(?i)(x-rapidapi-key|api[_ -]?key|authorization)\s*[:=]\s*\S+",
                r"\1=[redacted]",
                value.strip(),
            )
            return detail[:200]
    return ""
