from fastapi import APIRouter

router = APIRouter()


@router.get("/api/health")
def health_check() -> dict[str, object]:
    return {
        "status": "ok",
        "services": {
            "api": "healthy",
            "database": "pending",
            "storage": "pending",
        },
    }
