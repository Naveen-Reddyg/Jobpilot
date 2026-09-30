from contextlib import asynccontextmanager
from hashlib import sha256
from typing import Literal
from uuid import UUID, uuid4

from azure.storage.blob import BlobServiceClient, ContentSettings
from fastapi import FastAPI, File, HTTPException, Query, UploadFile, status
from pydantic import BaseModel, Field

from app.database import apply_migrations, connect_database
from app.discovery.service import DiscoveryError, run_jsearch_discovery
from app.settings import settings


@asynccontextmanager
async def lifespan(_: FastAPI):
    apply_migrations()
    yield


app = FastAPI(title="AgenticJobSync API", lifespan=lifespan)
local_user_id = UUID(settings.local_user_id)


class ProfileUpdate(BaseModel):
    target_job_titles: list[str] = Field(default_factory=list, max_length=30)
    target_skills: list[str] = Field(default_factory=list, max_length=100)
    timezone: str = Field(default="UTC", min_length=1, max_length=100)


class DecisionUpdate(BaseModel):
    decision: Literal["APPROVE", "SKIP"]


def ensure_local_user(connection) -> None:
    connection.execute(
        """
        INSERT INTO users (id, email, password_hash)
        VALUES (%s, %s, '!disabled!')
        ON CONFLICT (id) DO NOTHING
        """,
        (local_user_id, settings.local_user_email),
    )


def paged_offset(cursor: str | None) -> int:
    if cursor is None:
        return 0
    try:
        offset = int(cursor)
    except ValueError as error:
        raise HTTPException(status_code=422, detail="Invalid cursor") from error
    if offset < 0:
        raise HTTPException(status_code=422, detail="Invalid cursor")
    return offset


def profile_payload(row) -> dict[str, object]:
    return {
        "target_job_titles": row["target_job_titles"] or [],
        "target_skills": row["target_skills"] or [],
        "timezone": row["timezone"] or "UTC",
        "resume": (
            {"id": str(row["resume_id"]), "filename": row["resume_filename"], "uploaded_at": row["resume_created_at"].isoformat()}
            if row["resume_id"]
            else None
        ),
    }


@app.get("/api/health")
def health_check() -> dict[str, object]:
    services = {"api": "healthy", "database": "healthy", "storage": "healthy"}
    try:
        with connect_database() as connection:
            connection.execute("SELECT 1")
    except Exception:
        services["database"] = "unhealthy"
    try:
        BlobServiceClient.from_connection_string(settings.storage_connection_string).get_service_properties()
    except Exception:
        services["storage"] = "unhealthy"
    healthy = all(value == "healthy" for value in services.values())
    if not healthy:
        raise HTTPException(status_code=503, detail={"status": "unhealthy", "services": services})
    return {"status": "ok", "services": services}


@app.get("/api/v1/discovery/provider")
def get_discovery_provider() -> dict[str, str | bool]:
    return {"provider": "JSearch via RapidAPI", "configured": bool(settings.rapidapi_key)}


@app.post("/api/v1/discovery/run")
def start_discovery() -> dict[str, object]:
    try:
        return run_jsearch_discovery(local_user_id)
    except DiscoveryError as error:
        raise HTTPException(status_code=error.status_code, detail=str(error)) from error


@app.get("/api/v1/profile")
def get_profile() -> dict[str, object]:
    with connect_database() as connection:
        row = connection.execute(
            """
            SELECT COALESCE(profile.target_job_titles, ARRAY[]::TEXT[]) AS target_job_titles,
                   COALESCE(profile.target_skills, ARRAY[]::TEXT[]) AS target_skills,
                   COALESCE(profile.timezone, 'UTC') AS timezone,
                   resume.id AS resume_id,
                   resume.original_filename AS resume_filename,
                   resume.created_at AS resume_created_at
            FROM users AS app_user
            LEFT JOIN user_profiles AS profile ON profile.user_id = app_user.id
            LEFT JOIN LATERAL (
                SELECT id, original_filename, created_at
                FROM resume_assets
                WHERE user_id = app_user.id
                ORDER BY created_at DESC
                LIMIT 1
            ) AS resume ON TRUE
            WHERE app_user.id = %s
            """,
            (local_user_id,),
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile_payload(row)


@app.put("/api/v1/profile")
def update_profile(profile: ProfileUpdate) -> dict[str, object]:
    with connect_database() as connection:
        ensure_local_user(connection)
        row = connection.execute(
            """
            INSERT INTO user_profiles (user_id, target_job_titles, target_skills, timezone)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (user_id) DO UPDATE SET
                target_job_titles = EXCLUDED.target_job_titles,
                target_skills = EXCLUDED.target_skills,
                timezone = EXCLUDED.timezone,
                updated_at = NOW()
            RETURNING target_job_titles, target_skills, timezone
            """,
            (local_user_id, profile.target_job_titles, profile.target_skills, profile.timezone),
        ).fetchone()
    return {"profile": row}


@app.post("/api/v1/resume", status_code=status.HTTP_201_CREATED)
def upload_resume(file: UploadFile = File(...)) -> dict[str, object]:
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=415, detail="Only PDF resumes are accepted")
    content = file.file.read(settings.max_resume_bytes + 1)
    if len(content) > settings.max_resume_bytes:
        raise HTTPException(status_code=413, detail="Resume exceeds the upload size limit")
    if not content.startswith(b"%PDF-"):
        raise HTTPException(status_code=422, detail="Uploaded file is not a valid PDF")

    blob_key = f"{local_user_id}/{uuid4()}.pdf"
    blob_service = BlobServiceClient.from_connection_string(settings.storage_connection_string)
    container = blob_service.get_container_client(settings.storage_container)
    try:
        container.create_container()
    except Exception as error:
        if getattr(error, "status_code", None) != 409:
            raise HTTPException(status_code=503, detail="Resume storage is unavailable") from error
    container.upload_blob(
        blob_key,
        content,
        content_settings=ContentSettings(content_type="application/pdf"),
    )
    try:
        with connect_database() as connection:
            ensure_local_user(connection)
            row = connection.execute(
                """
                INSERT INTO resume_assets (user_id, object_key, original_filename, media_type, byte_size, sha256_digest)
                VALUES (%s, %s, %s, 'application/pdf', %s, %s)
                RETURNING id, original_filename, byte_size, created_at
                """,
                (
                    local_user_id,
                    blob_key,
                    file.filename or "resume.pdf",
                    len(content),
                    sha256(content).hexdigest(),
                ),
            ).fetchone()
    except Exception:
        container.delete_blob(blob_key)
        raise
    return {
        "id": str(row["id"]),
        "filename": row["original_filename"],
        "byte_size": row["byte_size"],
        "uploaded_at": row["created_at"].isoformat(),
    }


@app.get("/api/v1/recommendations")
def get_recommendations(
    status_filter: Literal["PENDING_REVIEW", "APPROVED", "SKIPPED"] | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=100),
    cursor: str | None = None,
) -> dict[str, object]:
    offset = paged_offset(cursor)
    parameters: list[object] = [local_user_id]
    status_clause = ""
    if status_filter is not None:
        status_clause = "AND recommendation.status = %s"
        parameters.append(status_filter)
    parameters.extend((limit + 1, offset))
    with connect_database() as connection:
        rows = connection.execute(
            f"""
            SELECT recommendation.id, recommendation.match_percentage,
                   recommendation.matched_skills, recommendation.missing_skills,
                   recommendation.rationale, recommendation.status,
                   job.title, job.company, job.location, job.application_url
            FROM recommendations AS recommendation
            JOIN jobs AS job ON job.id = recommendation.job_id
            WHERE recommendation.user_id = %s {status_clause}
            ORDER BY recommendation.match_percentage DESC, recommendation.created_at DESC
            LIMIT %s OFFSET %s
            """,
            parameters,
        ).fetchall()
    has_more = len(rows) > limit
    items = [
        {
            "id": str(row["id"]),
            "job": {
                "title": row["title"],
                "company": row["company"],
                "location": row["location"],
                "application_url": row["application_url"],
            },
            "match_percentage": row["match_percentage"],
            "matched_skills": row["matched_skills"],
            "missing_skills": row["missing_skills"],
            "rationale": row["rationale"],
            "status": row["status"],
        }
        for row in rows[:limit]
    ]
    return {"items": items, "next_cursor": str(offset + limit) if has_more else None}


@app.patch("/api/v1/recommendations/{recommendation_id}/decision")
def update_recommendation_decision(recommendation_id: UUID, decision: DecisionUpdate) -> dict[str, object]:
    target_status = "APPROVED" if decision.decision == "APPROVE" else "SKIPPED"
    with connect_database() as connection:
        row = connection.execute(
            """
            UPDATE recommendations
            SET status = %s, decided_at = NOW()
            WHERE id = %s AND user_id = %s
            RETURNING id, status, decided_at
            """,
            (target_status, recommendation_id, local_user_id),
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Recommendation not found")
        job = connection.execute(
            "SELECT application_url FROM jobs WHERE id = (SELECT job_id FROM recommendations WHERE id = %s)",
            (recommendation_id,),
        ).fetchone()
    return {
        "id": str(row["id"]),
        "status": row["status"],
        "decided_at": row["decided_at"].isoformat(),
        "application_url": job["application_url"] if job else None,
    }


@app.post("/api/v1/recommendations/{recommendation_id}/application-link-opened", status_code=status.HTTP_202_ACCEPTED)
def record_application_link_open(recommendation_id: UUID) -> dict[str, bool]:
    with connect_database() as connection:
        exists = connection.execute(
            "SELECT 1 FROM recommendations WHERE id = %s AND user_id = %s",
            (recommendation_id, local_user_id),
        ).fetchone()
        if exists is None:
            raise HTTPException(status_code=404, detail="Recommendation not found")
        connection.execute(
            "INSERT INTO application_link_events (user_id, recommendation_id) VALUES (%s, %s)",
            (local_user_id, recommendation_id),
        )
    return {"recorded": True}


@app.get("/api/v1/history/runs")
def get_history_runs(limit: int = Query(default=50, ge=1, le=100), cursor: str | None = None) -> dict[str, object]:
    offset = paged_offset(cursor)
    with connect_database() as connection:
        rows = connection.execute(
            """
            SELECT id, scheduled_for, status, source_count, jobs_checked,
                   recommendations_created, error_summary
            FROM discovery_runs
            ORDER BY scheduled_for DESC
            LIMIT %s OFFSET %s
            """,
            (limit + 1, offset),
        ).fetchall()
    has_more = len(rows) > limit
    items = [
        {
            "id": str(row["id"]),
            "scheduled_for": row["scheduled_for"].isoformat(),
            "status": row["status"],
            "source_count": row["source_count"],
            "jobs_checked": row["jobs_checked"],
            "recommendations_created": row["recommendations_created"],
            "error_summary": row["error_summary"],
        }
        for row in rows[:limit]
    ]
    return {"items": items, "next_cursor": str(offset + limit) if has_more else None}
