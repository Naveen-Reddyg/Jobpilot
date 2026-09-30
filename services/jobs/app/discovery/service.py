from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from app.database import connect_database
from app.discovery.connectors.jsearch import JSearchError, search_jobs
from app.discovery.connectors.jsearch import JSEARCH_HOST
from app.settings import settings


class DiscoveryError(Exception):
    def __init__(self, message: str, status_code: int) -> None:
        super().__init__(message)
        self.status_code = status_code


def run_jsearch_discovery(user_id: UUID) -> dict[str, object]:
    if not settings.rapidapi_key:
        raise DiscoveryError("Add RAPIDAPI_KEY to the workspace .env file and restart the API.", 503)

    with connect_database() as connection:
        profile = connection.execute(
            "SELECT target_job_titles, target_skills FROM user_profiles WHERE user_id = %s",
            (user_id,),
        ).fetchone()
        if profile is None:
            raise DiscoveryError("Save a profile before searching for jobs.", 400)

        titles = [title.strip() for title in profile["target_job_titles"] or [] if title.strip()]
        if not titles:
            raise DiscoveryError("Add at least one target job title before searching.", 400)

        source = connection.execute(
            "SELECT id FROM source_feeds WHERE source_type = 'rapidapi' AND source_name = 'JSearch' LIMIT 1"
        ).fetchone()
        if source is None:
            source = connection.execute(
                """
                INSERT INTO source_feeds (source_name, source_type, config_ref)
                VALUES ('JSearch', 'rapidapi', %s)
                RETURNING id
                """,
                (JSEARCH_HOST,),
            ).fetchone()
        else:
            connection.execute("UPDATE source_feeds SET enabled = TRUE WHERE id = %s", (source["id"],))

        run = connection.execute(
            """
            INSERT INTO discovery_runs (scheduled_for, started_at, status, source_count)
            VALUES (%s, %s, 'RUNNING', 1)
            RETURNING id
            """,
            (datetime.now(timezone.utc), datetime.now(timezone.utc)),
        ).fetchone()

    try:
        found: dict[str, dict[str, str | None]] = {}
        queried_titles = titles[:3]
        for title in queried_titles:
            for job in search_jobs(
                api_key=settings.rapidapi_key,
                query=f"{title} jobs",
                country=settings.rapidapi_country,
            ):
                found.setdefault(str(job["source_job_id"]), job)
    except JSearchError as error:
        with connect_database() as connection:
            connection.execute(
                "UPDATE discovery_runs SET status = 'FAILED', finished_at = %s, error_summary = %s WHERE id = %s",
                (datetime.now(timezone.utc), str(error), run["id"]),
            )
        raise DiscoveryError(str(error), 502) from error

    skills = profile["target_skills"] or []
    created = 0
    with connect_database() as connection:
        for job in found.values():
            description = job["description_excerpt"] or ""
            matched = [skill for skill in skills if skill.casefold() in description.casefold()]
            score = round(100 * len(matched) / len(skills)) if skills else 0
            rationale = (
                f"Job description mentions: {', '.join(matched)}."
                if matched
                else "Review the job description against your target skills."
            )
            published_at = _parse_datetime(job["published_at"])
            saved_job = connection.execute(
                """
                INSERT INTO jobs (
                    source_feed_id, source_job_id, application_url, title, company,
                    location, description_excerpt, published_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (source_feed_id, source_job_id) DO UPDATE SET
                    application_url = EXCLUDED.application_url,
                    title = EXCLUDED.title,
                    company = EXCLUDED.company,
                    location = EXCLUDED.location,
                    description_excerpt = EXCLUDED.description_excerpt,
                    published_at = EXCLUDED.published_at
                RETURNING id
                """,
                (
                    source["id"],
                    job["source_job_id"],
                    job["application_url"],
                    job["title"],
                    job["company"],
                    job["location"] or "",
                    description,
                    published_at,
                ),
            ).fetchone()
            recommendation = connection.execute(
                """
                INSERT INTO recommendations (
                    user_id, job_id, match_percentage, matched_skills, missing_skills, rationale
                ) VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (user_id, job_id) DO NOTHING
                RETURNING id
                """,
                (
                    user_id,
                    saved_job["id"],
                    score,
                    matched,
                    [skill for skill in skills if skill not in matched],
                    rationale,
                ),
            ).fetchone()
            created += int(recommendation is not None)

        connection.execute(
            """
            UPDATE discovery_runs
            SET status = 'SUCCEEDED', finished_at = %s, jobs_checked = %s,
                recommendations_created = %s
            WHERE id = %s
            """,
            (datetime.now(timezone.utc), len(found), created, run["id"]),
        )

    return {
        "run_id": str(run["id"]),
        "status": "SUCCEEDED",
        "provider": "JSearch via RapidAPI",
        "queried_titles": queried_titles,
        "jobs_checked": len(found),
        "recommendations_created": created,
    }


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed