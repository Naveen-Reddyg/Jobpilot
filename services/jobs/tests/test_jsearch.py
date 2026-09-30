import json
import unittest
from io import BytesIO
from urllib.error import HTTPError
from unittest.mock import patch

from app.discovery.connectors import jsearch


class FakeResponse:
    def __init__(self, payload: object) -> None:
        self.payload = json.dumps(payload).encode()

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def read(self) -> bytes:
        return self.payload


class JSearchTests(unittest.TestCase):
    def test_search_jobs_normalizes_jsearch_results(self) -> None:
        payload = {
            "data": [
                {
                    "job_id": "job-1",
                    "job_title": "Backend Engineer",
                    "employer_name": "Example Co",
                    "job_city": "Austin",
                    "job_state": "Texas",
                    "job_country": "US",
                    "job_description": "Python and PostgreSQL",
                    "job_apply_link": "https://example.com/apply",
                    "job_posted_at_datetime_utc": "2026-09-30T08:00:00Z",
                }
            ]
        }
        with patch.object(jsearch, "urlopen", return_value=FakeResponse(payload)) as mocked_urlopen:
            jobs = jsearch.search_jobs(api_key="test-key", query="Backend Engineer jobs")

        request = mocked_urlopen.call_args.args[0]
        headers = {name.lower(): value for name, value in request.header_items()}
        self.assertIn("/search-v2?", request.full_url)
        self.assertIn("country=us", request.full_url)
        self.assertIn("work_from_home=true", request.full_url)
        self.assertIn("num_pages=1", request.full_url)
        self.assertIn("date_posted=all", request.full_url)
        self.assertIn("query=Backend+Engineer+jobs", request.full_url)
        self.assertEqual(headers["x-rapidapi-key"], "test-key")
        self.assertEqual(
            jobs,
            [
                {
                    "source_job_id": "job-1",
                    "title": "Backend Engineer",
                    "company": "Example Co",
                    "location": "Austin, Texas, US",
                    "description_excerpt": "Python and PostgreSQL",
                    "application_url": "https://example.com/apply",
                    "published_at": "2026-09-30T08:00:00Z",
                }
            ],
        )

    def test_search_jobs_accepts_nested_search_v2_results(self) -> None:
        payload = {
            "status": "OK",
            "data": {
                "jobs": [
                    {
                        "job_id": "job-v2",
                        "job_title": "Platform Engineer",
                        "employer_name": "Example Co",
                        "job_apply_link": "https://example.com/apply",
                        "job_description": "Build platform services",
                    }
                ]
            },
        }
        with patch.object(jsearch, "urlopen", return_value=FakeResponse(payload)):
            jobs = jsearch.search_jobs(api_key="test-key", query="Platform Engineer jobs")

        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0]["source_job_id"], "job-v2")
        self.assertEqual(jobs[0]["title"], "Platform Engineer")

    def test_search_jobs_requires_an_api_key(self) -> None:
        with self.assertRaisesRegex(jsearch.JSearchError, "not configured"):
            jsearch.search_jobs(api_key="", query="Backend Engineer jobs")

    def test_search_jobs_rejects_unexpected_response(self) -> None:
        with patch.object(jsearch, "urlopen", return_value=FakeResponse({"results": []})):
            with self.assertRaisesRegex(jsearch.JSearchError, "unexpected response"):
                jsearch.search_jobs(api_key="test-key", query="Backend Engineer jobs")

    def test_unauthorized_response_identifies_invalid_key(self) -> None:
        unauthorized = HTTPError("https://example.com", 401, "Unauthorized", None, None)
        with patch.object(jsearch, "urlopen", side_effect=unauthorized):
            with self.assertRaisesRegex(jsearch.JSearchError, "HTTP 401.*API key"):
                jsearch.search_jobs(api_key="test-key", query="Backend Engineer jobs")

    def test_forbidden_response_identifies_subscription_issue(self) -> None:
        forbidden = HTTPError("https://example.com", 403, "Forbidden", None, None)
        with patch.object(jsearch, "urlopen", side_effect=forbidden):
            with self.assertRaisesRegex(jsearch.JSearchError, "HTTP 403.*subscribed to JSearch"):
                jsearch.search_jobs(api_key="test-key", query="Backend Engineer jobs")

    def test_provider_body_identifies_missing_subscription(self) -> None:
        body = BytesIO(b'{"message":"You are not subscribed to this API"}')
        forbidden = HTTPError("https://example.com", 403, "Forbidden", None, body)
        with patch.object(jsearch, "urlopen", side_effect=forbidden):
            with self.assertRaisesRegex(jsearch.JSearchError, "not subscribed to JSearch"):
                jsearch.search_jobs(api_key="test-key", query="Backend Engineer jobs")

    def test_provider_body_identifies_quota_limit(self) -> None:
        body = BytesIO(b'{"message":"Monthly quota exceeded"}')
        forbidden = HTTPError("https://example.com", 403, "Forbidden", None, body)
        with patch.object(jsearch, "urlopen", side_effect=forbidden):
            with self.assertRaisesRegex(jsearch.JSearchError, "quota or rate limit"):
                jsearch.search_jobs(api_key="test-key", query="Backend Engineer jobs")

    def test_not_found_endpoint_response_identifies_route(self) -> None:
        body = BytesIO(b'{"message":"Endpoint not found"}')
        not_found = HTTPError("https://example.com", 404, "Not Found", None, body)
        with patch.object(jsearch, "urlopen", side_effect=not_found):
            with self.assertRaisesRegex(jsearch.JSearchError, "GET /search-v2"):
                jsearch.search_jobs(api_key="test-key", query="Backend Engineer jobs")

    def test_not_found_response_includes_safe_provider_detail(self) -> None:
        body = BytesIO(b'{"message":"Invalid query parameter"}')
        not_found = HTTPError("https://example.com", 404, "Not Found", None, body)
        with patch.object(jsearch, "urlopen", side_effect=not_found):
            with self.assertRaisesRegex(jsearch.JSearchError, "Invalid query parameter"):
                jsearch.search_jobs(api_key="test-key", query="Backend Engineer jobs")

    def test_provider_detail_redacts_credential_like_values(self) -> None:
        detail = jsearch._safe_provider_detail(b'{"message":"x-rapidapi-key: private-value"}')
        self.assertNotIn("private-value", detail)
        self.assertIn("[redacted]", detail)