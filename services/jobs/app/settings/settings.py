from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv("DATABASE_URL", "postgresql://jobsync:jobsync_dev@postgres:5432/jobsync")
    storage_connection_string: str = os.getenv(
        "STORAGE_CONNECTION_STRING",
        "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;"
        "AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;"
        "BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;",
    )
    storage_container: str = os.getenv("STORAGE_CONTAINER", "resumes")
    max_resume_bytes: int = int(os.getenv("MAX_RESUME_BYTES", str(10 * 1024 * 1024)))
    local_user_id: str = os.getenv("LOCAL_USER_ID", "00000000-0000-4000-8000-000000000001")
    local_user_email: str = os.getenv("LOCAL_USER_EMAIL", "local-user@jobsync.invalid")
    discovery_cron: str = os.getenv("DISCOVERY_CRON", "0 6,18 * * *")
    discovery_timezone: str = os.getenv("DISCOVERY_TIMEZONE", "UTC")
    rapidapi_key: str | None = os.getenv("RAPIDAPI_KEY") or None
    rapidapi_country: str = os.getenv("RAPIDAPI_COUNTRY", "us")
    llm_provider: str | None = os.getenv("LLM_PROVIDER") or None
    llm_model: str | None = os.getenv("LLM_MODEL") or None


settings = Settings()
