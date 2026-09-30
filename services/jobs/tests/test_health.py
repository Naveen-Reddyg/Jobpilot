from app.api.main import app


def test_app_is_created() -> None:
    assert app.title == "AgenticJobSync API"
